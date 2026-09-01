from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Evento, Usuario
from app.schemas import EventoCreate, EventoUpdate, EventoOut
from app.auth import get_current_user

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.post("", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
def crear_evento(
    evento_in: EventoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo evento (ej. 'Pollada 2026', 'Cachimbeada 2026'). Requiere autenticación.
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
    Obtiene la lista de todos los eventos. Filtro opcional por 'activo'. Requiere autenticación.
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
    Obtiene los detalles de un evento específico por su ID. Requiere autenticación.
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
    Actualiza la información de un evento existente. Requiere autenticación.
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
