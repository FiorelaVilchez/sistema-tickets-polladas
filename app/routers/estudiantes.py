from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EstudianteMatriculado, Usuario
from app.schemas import EstudianteOut
from app.auth import get_current_user

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes Matriculados"])

@router.get("/buscar", response_model=List[EstudianteOut])
def buscar_estudiantes_matriculados(
    q: str = Query(..., min_length=1, description="Buscar por código de alumno o nombre completo"),
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Busca estudiantes en la lista oficial de matriculados (EstudiantesMatriculados.xlsx).
    Permite autocompletar código, nombre, carrera y ciclo.
    Requiere autenticación.
    """
    term = q.strip()
    query = db.query(EstudianteMatriculado).filter(
        or_(
            EstudianteMatriculado.codigo.ilike(f"%{term}%"),
            EstudianteMatriculado.nombre.ilike(f"%{term}%")
        )
    ).limit(limit)
    
    return query.all()

@router.get("/{codigo}", response_model=EstudianteOut)
def obtener_estudiante_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene los datos de un estudiante matriculado por su código de 6 dígitos.
    Requiere autenticación.
    """
    estudiante = db.query(EstudianteMatriculado).filter(EstudianteMatriculado.codigo == codigo.strip()).first()
    if not estudiante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estudiante no encontrado en la lista de matriculados"
        )
    return estudiante
