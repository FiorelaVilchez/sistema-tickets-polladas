from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    activo = Column(Boolean, default=True, nullable=False)

    # Relación con tickets
    tickets = relationship("Ticket", back_populates="evento", cascade="all, delete-orphan")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    codigo_unico = Column(String(100), unique=True, index=True, nullable=False)
    evento_id = Column(Integer, ForeignKey("eventos.id"), nullable=False)
    nombre_alumno = Column(String(100), nullable=False)
    codigo_alumno = Column(String(50), nullable=False)
    estado = Column(String(20), default="no_vendido", nullable=False) # no_vendido | separado | vendido
    fecha_hora_entrega = Column(DateTime, nullable=True, default=None)
    entregado = Column(Boolean, default=False, nullable=False)
    qr_image_url = Column(String(255), nullable=True)

    # Relación con evento
    evento = relationship("Evento", back_populates="tickets")
