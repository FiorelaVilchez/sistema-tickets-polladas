import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import Ticket
from app.routers import auth, eventos, tickets

# Crear las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión de Tickets",
    description="API Backend en FastAPI para la emisión y verificación de tickets con código QR.",
    version="1.0.0"
)

# Configurar CORS (permitir accesos desde frontend local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta de archivos estáticos para acceder a los QR en /static/qrcodes/...
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(os.path.join(STATIC_DIR, "qrcodes"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Incluir routers de la API
app.include_router(auth.router)
app.include_router(eventos.router)
app.include_router(tickets.router)

@app.get("/", tags=["General"])
def inicio():
    return {
        "mensaje": "Bienvenido a la API del Sistema de Tickets",
        "documentacion": "/docs",
        "login": "/auth/login"
    }

@app.get("/ticket/{codigo_unico}", tags=["Verificación Pública de Ticket"])
def verificar_ticket_publico(codigo_unico: str, db: Session = Depends(get_db)):
    """
    Ruta pública para verificar el estado de un ticket al escanear su código QR.
    No requiere autenticación.
    """
    ticket = db.query(Ticket).filter(Ticket.codigo_unico == codigo_unico).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado o inválido"
        )
    
    return {
        "valido": True,
        "codigo_unico": ticket.codigo_unico,
        "evento": ticket.evento.nombre if ticket.evento else "Desconocido",
        "nombre_alumno": ticket.nombre_alumno,
        "codigo_alumno": ticket.codigo_alumno,
        "estado": ticket.estado,
        "entregado": ticket.entregado,
        "fecha_hora_entrega": ticket.fecha_hora_entrega.isoformat() if ticket.fecha_hora_entrega else None,
        "qr_image_url": ticket.qr_image_url
    }
