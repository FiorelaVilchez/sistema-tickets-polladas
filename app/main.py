import os
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import Ticket
from app.routers import auth, eventos, tickets, estudiantes

# Crear las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión de Tickets",
    description="API Backend en FastAPI para la emisión y entrega de boletos físicos numerados (del 1 al 1000).",
    version="2.0.0"
)

# Configurar CORS (permitir accesos desde cualquier origen en la red local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios estáticos
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(STATIC_DIR, exist_ok=True)

# Montar imágenes estáticas en /static
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Montar frontend estático en /app
app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Incluir routers de la API
app.include_router(auth.router)
app.include_router(eventos.router)
app.include_router(tickets.router)
app.include_router(estudiantes.router)

@app.get("/", tags=["General"])
def inicio():
    """
    Redirige automáticamente al panel web del frontend.
    """
    return RedirectResponse(url="/app/")

@app.get("/styles.css", include_in_schema=False)
def get_root_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "styles.css"))

@app.get("/app.js", include_in_schema=False)
def get_root_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"))
