from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket, Evento, Usuario
from app.schemas import TicketCreate, TicketUpdate, TicketOut
from app.auth import get_current_user
from app.utils import generar_codigo_unico, generar_qr_code

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def crear_ticket(
    ticket_in: TicketCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo ticket para un evento determinado.
    - Genera automáticamente el `codigo_unico`
    - Genera automáticamente la imagen QR con la URL http://localhost:8000/ticket/{codigo_unico}
    - Requiere autenticación.
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

    # 1. Generar código único
    codigo_unico = generar_codigo_unico(db, evento)

    # 2. Obtener base URL de la petición actual (por defecto http://localhost:8000)
    base_url = str(request.base_url).rstrip("/")
    
    # 3. Generar imagen QR
    qr_image_url = generar_qr_code(codigo_unico=codigo_unico, host_base_url=base_url)

    # 4. Crear instancia en base de datos
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
    Obtiene la lista de tickets. Filtros opcionales por evento_id, estado y entregado.
    Requiere autenticación.
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
    Requiere autenticación.
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
    Si se marca `entregado=True`, asigna la fecha y hora actual automáticamente.
    Requiere autenticación.
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
    Marca un ticket como entregado, registrando fecha_hora_entrega actual y estado 'vendido'.
    Requiere autenticación.
    """
    db_ticket = db.query(Ticket).filter(Ticket.codigo_unico == codigo_unico).first()
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado"
        )
    
    if db_ticket.entregado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ticket ya ha sido entregado anteriormente"
        )

    db_ticket.entregado = True
    db_ticket.estado = "vendido"
    db_ticket.fecha_hora_entrega = datetime.utcnow()

    db.commit()
    db.refresh(db_ticket)
    return db_ticket
