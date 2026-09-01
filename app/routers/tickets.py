from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket, Evento, Usuario
from app.schemas import TicketCreate, TicketVentaCreate, TicketUpdate, TicketOut, ConfirmarEntregaRequest
from app.auth import get_current_user
from app.utils import generar_codigo_unico, generar_qr_code

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("/registrar-venta", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def registrar_venta(
    ticket_in: TicketVentaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    1. Registrar venta / Vender ticket adicional:
    Crea un ticket con nombre_alumno, codigo_alumno, evento_id y estado (separado o vendido).
    Genera automáticamente el codigo_unico y la imagen QR.
    Requiere autenticación.
    """
    if ticket_in.estado not in ["separado", "vendido"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El estado de la venta debe ser 'separado' o 'vendido'"
        )

    evento = db.query(Evento).filter(Evento.id == ticket_in.evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El evento especificado no existe"
        )
    
    if not evento.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El evento especificado no está activo"
        )

    # Generar código único y QR
    codigo_unico = generar_codigo_unico(db, evento)
    base_url = str(request.base_url).rstrip("/")
    qr_image_url = generar_qr_code(codigo_unico=codigo_unico, host_base_url=base_url)

    db_ticket = Ticket(
        codigo_unico=codigo_unico,
        evento_id=ticket_in.evento_id,
        nombre_alumno=ticket_in.nombre_alumno,
        codigo_alumno=ticket_in.codigo_alumno,
        estado=ticket_in.estado,
        fecha_hora_entrega=None,
        entregado=False,
        qr_image_url=qr_image_url
    )

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.get("/buscar", response_model=List[TicketOut])
def buscar_tickets(
    codigo_alumno: Optional[str] = Query(None, description="Filtrar por código de alumno"),
    codigo_unico: Optional[str] = Query(None, description="Filtrar por código único de ticket"),
    q: Optional[str] = Query(None, description="Búsqueda general por código de alumno o código único"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    2. Buscar ticket:
    Busca por codigo_alumno o por codigo_unico del ticket.
    Devuelve todos los tickets asociados con su estado actual, si están entregados y fecha_hora_entrega.
    Requiere autenticación.
    """
    query = db.query(Ticket)
    
    if codigo_alumno:
        query = query.filter(Ticket.codigo_alumno == codigo_alumno)
    elif codigo_unico:
        query = query.filter(Ticket.codigo_unico == codigo_unico)
    elif q:
        query = query.filter(
            or_(
                Ticket.codigo_alumno.ilike(f"%{q}%"),
                Ticket.codigo_unico.ilike(f"%{q}%"),
                Ticket.nombre_alumno.ilike(f"%{q}%")
            )
        )
    
    return query.all()

@router.post("/confirmar-entrega", response_model=TicketOut)
def confirmar_entrega_body(
    datos: ConfirmarEntregaRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    4. Confirmar entrega:
    Recibe el codigo_unico del ticket, marca entregado=True y guarda fecha_hora_entrega.
    Si el ticket ya estaba entregado, devuelve un error 400 claro indicando la fecha de entrega previa.
    Requiere autenticación.
    """
    ticket = db.query(Ticket).filter(Ticket.codigo_unico == datos.codigo_unico).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ningún ticket con el código '{datos.codigo_unico}'"
        )
    
    if ticket.entregado:
        fecha_str = ticket.fecha_hora_entrega.strftime("%Y-%m-%d %H:%M:%S") if ticket.fecha_hora_entrega else "fecha desconocida"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ticket '{datos.codigo_unico}' ya fue entregado previamente el {fecha_str}."
        )

    ticket.entregado = True
    ticket.estado = "vendido"
    ticket.fecha_hora_entrega = datetime.utcnow()

    db.commit()
    db.refresh(ticket)
    return ticket

@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def crear_ticket(
    ticket_in: TicketCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo ticket genérico para un evento determinado.
    """
    evento = db.query(Evento).filter(Evento.id == ticket_in.evento_id).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El evento especificado no existe"
        )
    
    if not evento.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El evento especificado no está activo"
        )

    codigo_unico = generar_codigo_unico(db, evento)
    base_url = str(request.base_url).rstrip("/")
    qr_image_url = generar_qr_code(codigo_unico=codigo_unico, host_base_url=base_url)

    db_ticket = Ticket(
        codigo_unico=codigo_unico,
        evento_id=ticket_in.evento_id,
        nombre_alumno=ticket_in.nombre_alumno,
        codigo_alumno=ticket_in.codigo_alumno,
        estado=ticket_in.estado or "no_vendido",
        fecha_hora_entrega=None,
        entregado=False,
        qr_image_url=qr_image_url
    )

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.get("", response_model=List[TicketOut])
def listar_tickets(
    evento_id: Optional[int] = None,
    estado: Optional[str] = None,
    entregado: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la lista de tickets con filtros opcionales.
    """
    query = db.query(Ticket)
    if evento_id is not None:
        query = query.filter(Ticket.evento_id == evento_id)
    if estado is not None:
        query = query.filter(Ticket.estado == estado)
    if entregado is not None:
        query = query.filter(Ticket.entregado == entregado)
    
    return query.all()

@router.get("/{codigo_unico}", response_model=TicketOut)
def obtener_ticket(
    codigo_unico: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la información detallada de un ticket mediante su código único.
    """
    ticket = db.query(Ticket).filter(Ticket.codigo_unico == codigo_unico).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado"
        )
    return ticket

@router.put("/{codigo_unico}", response_model=TicketOut)
def actualizar_ticket(
    codigo_unico: str,
    ticket_in: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza la información de un ticket.
    """
    db_ticket = db.query(Ticket).filter(Ticket.codigo_unico == codigo_unico).first()
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado"
        )

    update_data = ticket_in.model_dump(exclude_unset=True)
    
    if "entregado" in update_data:
        if update_data["entregado"] and not db_ticket.entregado:
            db_ticket.fecha_hora_entrega = datetime.utcnow()
            if db_ticket.estado == "no_vendido":
                db_ticket.estado = "vendido"
        elif not update_data["entregado"]:
            db_ticket.fecha_hora_entrega = None

    for field, value in update_data.items():
        setattr(db_ticket, field, value)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.post("/{codigo_unico}/entregar", response_model=TicketOut)
def marcar_ticket_entregado(
    codigo_unico: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Marca un ticket como entregado (vía parametro en la URL).
    Si ya fue entregado, lanza error 400.
    """
    db_ticket = db.query(Ticket).filter(Ticket.codigo_unico == codigo_unico).first()
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado"
        )
    
    if db_ticket.entregado:
        fecha_str = db_ticket.fecha_hora_entrega.strftime("%Y-%m-%d %H:%M:%S") if db_ticket.fecha_hora_entrega else "fecha desconocida"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ticket '{codigo_unico}' ya fue entregado previamente el {fecha_str}."
        )

    db_ticket.entregado = True
    db_ticket.estado = "vendido"
    db_ticket.fecha_hora_entrega = datetime.utcnow()

    db.commit()
    db.refresh(db_ticket)
    return db_ticket
