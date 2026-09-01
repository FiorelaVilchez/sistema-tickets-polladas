from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# ----------------- JWT SCHEMAS -----------------
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ----------------- USUARIO SCHEMAS -----------------
class UsuarioBase(BaseModel):
    username: str

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioOut(UsuarioBase):
    id: int

    class Config:
        from_attributes = True

# ----------------- EVENTO SCHEMAS -----------------
class EventoBase(BaseModel):
    nombre: str
    fecha: Optional[datetime] = Field(default_factory=datetime.utcnow)
    activo: bool = True

class EventoCreate(EventoBase):
    pass

class EventoUpdate(BaseModel):
    nombre: Optional[str] = None
    fecha: Optional[datetime] = None
    activo: Optional[bool] = None

class EventoOut(EventoBase):
    id: int

    class Config:
        from_attributes = True

# ----------------- TICKET SCHEMAS -----------------
class TicketCreate(BaseModel):
    evento_id: int
    nombre_alumno: str
    codigo_alumno: str
    estado: Optional[str] = "no_vendido" # no_vendido | separado | vendido

class TicketUpdate(BaseModel):
    nombre_alumno: Optional[str] = None
    codigo_alumno: Optional[str] = None
    estado: Optional[str] = None # no_vendido | separado | vendido
    entregado: Optional[bool] = None

class TicketEntrega(BaseModel):
    entregado: bool = True

class TicketOut(BaseModel):
    id: int
    codigo_unico: str
    evento_id: int
    nombre_alumno: str
    codigo_alumno: str
    estado: str
    fecha_hora_entrega: Optional[datetime] = None
    entregado: bool
    qr_image_url: Optional[str] = None
    evento: Optional[EventoOut] = None

    class Config:
        from_attributes = True
