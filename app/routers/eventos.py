import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.database import get_db
from app.models import Evento, Ticket, Usuario
from app.schemas import EventoCreate, EventoUpdate, EventoOut, EventoKPIsOut
from app.auth import get_current_user

router = APIRouter(prefix="/eventos", tags=["Eventos"])

def calcular_kpis_evento(evento: Evento, db: Session) -> EventoKPIsOut:
    tickets = db.query(Ticket).filter(Ticket.evento_id == evento.id).all()
    
    total = len(tickets)
    vendidos = sum(1 for t in tickets if t.estado == "vendido")
    separados = sum(1 for t in tickets if t.estado == "separado")
    no_vendidos = sum(1 for t in tickets if t.estado == "no_vendido")
    entregados = sum(1 for t in tickets if t.entregado)

    return EventoKPIsOut(
        evento_id=evento.id,
        nombre_evento=evento.nombre,
        total_tickets=total,
        vendidos=vendidos,
        separados=separados,
        no_vendidos=no_vendidos,
        entregados=entregados
    )

@router.get("/kpis", response_model=List[EventoKPIsOut])
def obtener_kpis_todos_eventos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    5. KPIs:
    Devuelve los KPIs de todos los eventos (cantidad de tickets vendidos, separados y no vendidos).
    Requiere autenticación.
    """
    eventos = db.query(Evento).all()
    return [calcular_kpis_evento(e, db) for e in eventos]

@router.get("/{evento_id}/kpis", response_model=EventoKPIsOut)
def obtener_kpis_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    5. KPIs por evento:
    Devuelve la cantidad de tickets vendidos, separados (no recogidos) y no vendidos para un evento específico.
    Requiere autenticación.
    """
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    return calcular_kpis_evento(evento, db)

@router.get("/{evento_id}/exportar/excel")
def exportar_tickets_excel(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    6. Exportar Excel:
    Genera un archivo Excel (.xlsx con openpyxl) con el detalle completo de todos los tickets del evento.
    Requiere autenticación.
    """
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )

    tickets = db.query(Ticket).filter(Ticket.evento_id == evento_id).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tickets"

    # Estilos Excel
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Encabezados
    headers = [
        "ID", "Código Único", "Nombre Alumno", "Código Alumno", 
        "Estado", "Entregado", "Fecha y Hora de Entrega"
    ]
    ws.append(headers)

    for col_num, _ in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Filas de datos
    for ticket in tickets:
        fecha_str = ticket.fecha_hora_entrega.strftime("%Y-%m-%d %H:%M:%S") if ticket.fecha_hora_entrega else "-"
        entregado_str = "Sí" if ticket.entregado else "No"
        
        ws.append([
            ticket.id,
            ticket.codigo_unico,
            ticket.nombre_alumno,
            ticket.codigo_alumno,
            ticket.estado,
            entregado_str,
            fecha_str
        ])

    # Aplicar bordes y ajustar ancho de columnas
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(headers)):
        for cell in row:
            cell.border = thin_border
            if cell.column in [1, 5, 6]:
                cell.alignment = Alignment(horizontal="center")

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"tickets_{evento.nombre.replace(' ', '_')}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{evento_id}/exportar/csv")
def exportar_tickets_csv(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    6. Exportar CSV:
    Genera un archivo CSV con el detalle completo de todos los tickets del evento.
    Requiere autenticación.
    """
    evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )

    tickets = db.query(Ticket).filter(Ticket.evento_id == evento_id).all()

    output = io.StringIO()
    # Escribir BOM para UTF-8 para compatibilidad con Microsoft Excel
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)

    # Encabezados
    writer.writerow([
        "ID", "Código Único", "Nombre Alumno", "Código Alumno", 
        "Estado", "Entregado", "Fecha y Hora de Entrega"
    ])

    for ticket in tickets:
        fecha_str = ticket.fecha_hora_entrega.strftime("%Y-%m-%d %H:%M:%S") if ticket.fecha_hora_entrega else ""
        entregado_str = "Sí" if ticket.entregado else "No"
        writer.writerow([
            ticket.id,
            ticket.codigo_unico,
            ticket.nombre_alumno,
            ticket.codigo_alumno,
            ticket.estado,
            entregado_str,
            fecha_str
        ])

    filename = f"tickets_{evento.nombre.replace(' ', '_')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
def crear_evento(
    evento_in: EventoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo evento. Requiere autenticación.
    """
    db_evento = Evento(
        nombre=evento_in.nombre,
        fecha=evento_in.fecha,
        activo=evento_in.activo
    )
    db.add(db_evento)
    db.commit()
    db.refresh(db_evento)
    return db_evento

@router.get("", response_model=List[EventoOut])
def listar_eventos(
    activo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de eventos. Requiere autenticación.
    """
    query = db.query(Evento)
    if activo is not None:
        query = query.filter(Evento.activo == activo)
    return query.all()

@router.get("/{evento_id}", response_model=EventoOut)
def obtener_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene los detalles de un evento por ID. Requiere autenticación.
    """
    db_evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not db_evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    return db_evento

@router.put("/{evento_id}", response_model=EventoOut)
def actualizar_evento(
    evento_id: int,
    evento_in: EventoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un evento existente. Requiere autenticación.
    """
    db_evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not db_evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    
    update_data = evento_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_evento, field, value)

    db.commit()
    db.refresh(db_evento)
    return db_evento

@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_evento(
    evento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un evento del sistema. Requiere autenticación.
    """
    db_evento = db.query(Evento).filter(Evento.id == evento_id).first()
    if not db_evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )
    db.delete(db_evento)
    db.commit()
    return None
