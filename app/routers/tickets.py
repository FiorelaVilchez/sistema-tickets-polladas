from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket, Evento, Usuario
from app.schemas import (
    VentaMultipleCreate,
    TicketOut,
    ConfirmarEntregaPaymentRequest,
    TicketUpdate
)
from app.auth import get_current_user

router = APIRouter(prefix="/tickets", tags=["Tickets y Ventas"])

@router.post("/registrar-venta", response_model=List[TicketOut], status_code=status.HTTP_201_CREATED)
def registrar_venta_multiple(
    venta_in: VentaMultipleCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra la venta o separación de uno o varios boletos físicos numerados (hasta 20)
    asociados a un solo estudiante o código/DNI.
    Permite asignar la persona referencial que recogerá cada pollada individualmente.
    Requiere autenticación.
    """
    if not venta_in.boletos or len(venta_in.boletos) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe incluir al menos un número de boleto físico para registrar la venta."
        )
    
    if len(venta_in.boletos) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede vender más de 20 boletos por persona en una sola transacción."
        )

    evento = db.query(Evento).filter(Evento.id == venta_in.evento_id).first()
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

    # Validar que los números de boletos físicos no estén ocupados en este evento
    numeros_solicitados = [b.numero_boleto for b in venta_in.boletos]
    if len(numeros_solicitados) != len(set(numeros_solicitados)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede ingresar números de boletos físicos duplicados en la misma venta."
        )

    existentes = db.query(Ticket).filter(
        Ticket.evento_id == venta_in.evento_id,
        Ticket.numero_boleto.in_(numeros_solicitados)
    ).all()

    if existentes:
        ocupados_str = ", ".join(str(t.numero_boleto) for t in existentes)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Los siguientes números de boleto físico ya han sido vendidos o asignados anteriormente: #{ocupados_str}"
        )

    # Cálculos financieros por boleto
    total_boletos = len(venta_in.boletos)
    precio_unitario = venta_in.precio_unitario if venta_in.precio_unitario > 0 else 15.0
    
    monto_total_por_boleto = precio_unitario
    monto_pagado_por_boleto = venta_in.monto_pagado_total / total_boletos if total_boletos > 0 else 0.0
    
    # Ajustar por seguridad
    if monto_pagado_por_boleto > monto_total_por_boleto:
        monto_pagado_por_boleto = monto_total_por_boleto

    monto_pendiente_por_boleto = max(0.0, monto_total_por_boleto - monto_pagado_por_boleto)

    tickets_creados = []
    for item in venta_in.boletos:
        recolector = item.nombre_recolector.strip() if (item.nombre_recolector and item.nombre_recolector.strip()) else venta_in.nombre_alumno.strip()
        
        ticket = Ticket(
            numero_boleto=item.numero_boleto,
            evento_id=venta_in.evento_id,
            codigo_alumno=venta_in.codigo_alumno.strip(),
            nombre_alumno=venta_in.nombre_alumno.strip(),
            carrera=venta_in.carrera.strip() if venta_in.carrera else "INGENIERIA DE SISTEMAS",
            ciclo=venta_in.ciclo.strip() if venta_in.ciclo else "1",
            nombre_recolector=recolector,
            estado=venta_in.estado,
            precio_unitario=precio_unitario,
            monto_total=monto_total_por_boleto,
            monto_pagado=monto_pagado_por_boleto,
            monto_pendiente=monto_pendiente_por_boleto,
            metodo_pago=venta_in.metodo_pago or "ninguno",
            entregado=False,
            fecha_hora_entrega=None
        )
        db.add(ticket)
        tickets_creados.append(ticket)

    db.commit()
    for t in tickets_creados:
        db.refresh(t)

    return tickets_creados

@router.get("/buscar", response_model=List[TicketOut])
def buscar_tickets(
    numero_boleto: Optional[int] = Query(None, description="Filtrar por número de boleto físico"),
    codigo_alumno: Optional[str] = Query(None, description="Filtrar por código de alumno o DNI"),
    q: Optional[str] = Query(None, description="Búsqueda por número de boleto, código, comprador o persona que recoge"),
    evento_id: Optional[int] = Query(None, description="Filtrar por evento determinado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Busca tickets por número de boleto físico, código de alumno/DNI, nombre del comprador o persona que recoge.
    Devuelve todos los datos financieros (monto abonado, saldo pendiente, estado y entrega).
    Requiere autenticación.
    """
    query = db.query(Ticket)
    
    if evento_id is not None:
        query = query.filter(Ticket.evento_id == evento_id)

    if numero_boleto is not None:
        query = query.filter(Ticket.numero_boleto == numero_boleto)
    elif codigo_alumno:
        query = query.filter(Ticket.codigo_alumno == codigo_alumno.strip())
    elif q:
        term = q.strip()
        # Intentar convertir término a número por si buscaron "102"
        if term.isdigit():
            num_val = int(term)
            query = query.filter(
                or_(
                    Ticket.numero_boleto == num_val,
                    Ticket.codigo_alumno.ilike(f"%{term}%"),
                    Ticket.nombre_alumno.ilike(f"%{term}%"),
                    Ticket.nombre_recolector.ilike(f"%{term}%")
                )
            )
        else:
            query = query.filter(
                or_(
                    Ticket.codigo_alumno.ilike(f"%{term}%"),
                    Ticket.nombre_alumno.ilike(f"%{term}%"),
                    Ticket.nombre_recolector.ilike(f"%{term}%")
                )
            )
    
    return query.order_by(Ticket.numero_boleto.asc()).all()

@router.post("/confirmar-entrega", response_model=TicketOut)
def confirmar_entrega_boleto(
    datos: ConfirmarEntregaPaymentRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Confirma la entrega física de un boleto mediante su número impreso.
    Si el boleto ya fue entregado previamente, retorna HTTP 400 con la fecha exacta.
    Permite ingresar un cobro adicional en puerta si el ticket estaba parcialmente pagado o separado.
    Requiere autenticación.
    """
    ticket = db.query(Ticket).filter(Ticket.numero_boleto == datos.numero_boleto).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ningún boleto físico con el número #{datos.numero_boleto}."
        )

    if ticket.entregado:
        fecha_str = ticket.fecha_hora_entrega.strftime("%d/%m/%Y a las %H:%M:%S") if ticket.fecha_hora_entrega else "fecha desconocida"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El boleto físico #{datos.numero_boleto} ya fue entregado previamente el {fecha_str}."
        )

    # Si se pagó un saldo adicional durante la entrega
    if datos.monto_cobrado_adicional and datos.monto_cobrado_adicional > 0:
        ticket.monto_pagado += datos.monto_cobrado_adicional
        if ticket.monto_pagado >= ticket.monto_total:
            ticket.monto_pagado = ticket.monto_total
            ticket.monto_pendiente = 0.0
            ticket.estado = "pagado"
        else:
            ticket.monto_pendiente = max(0.0, ticket.monto_total - ticket.monto_pagado)
            ticket.estado = "parcialmente_pagado"

    if datos.metodo_pago_entrega and datos.metodo_pago_entrega != "ninguno":
        ticket.metodo_pago = datos.metodo_pago_entrega

    ticket.entregado = True
    ticket.fecha_hora_entrega = datetime.utcnow()

    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("", response_model=List[TicketOut])
def listar_todos_tickets(
    evento_id: Optional[int] = None,
    estado: Optional[str] = None,
    entregado: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos los tickets con filtros opcionales por evento, estado y entregado.
    """
    query = db.query(Ticket)
    if evento_id is not None:
        query = query.filter(Ticket.evento_id == evento_id)
    if estado is not None:
        query = query.filter(Ticket.estado == estado)
    if entregado is not None:
        query = query.filter(Ticket.entregado == entregado)

    return query.order_by(Ticket.numero_boleto.asc()).all()

@router.get("/{ticket_id}", response_model=TicketOut)
def obtener_ticket_por_id(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene los datos de un ticket por su ID primario.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado"
        )
    return ticket
