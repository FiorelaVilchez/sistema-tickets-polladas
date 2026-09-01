import os
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
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

os.makedirs(os.path.join(STATIC_DIR, "qrcodes"), exist_ok=True)

# Montar imágenes estáticas de QRs en /static
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Montar frontend estático en /app
app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Incluir routers de la API
app.include_router(auth.router)
app.include_router(eventos.router)
app.include_router(tickets.router)

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

@app.get("/ticket/{codigo_unico}", tags=["Verificación Pública de Ticket"])
def verificar_ticket_publico(codigo_unico: str, request: Request, format: str = None, db: Session = Depends(get_db)):
    """
    Ruta pública para verificar el estado de un ticket al escanear su código QR.
    Devuelve un certificado HTML estético en navegadores móviles/escritorio
    o JSON si se requiere explícitamente vía API.
    """
    ticket = db.query(Ticket).filter(Ticket.codigo_unico == codigo_unico).first()
    
    # Respuesta JSON para consumo vía API o Swagger
    accept_header = request.headers.get("accept", "")
    if format == "json" or "application/json" in accept_header:
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado o inválido")
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

    # Vista HTML estilizada para escaneo desde la cámara del celular
    if not ticket:
        html_invalid = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ticket Inválido - Sistema de Tickets</title>
            <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
                .card {{ background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 20px; padding: 40px 24px; text-align: center; max-width: 400px; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
                .icon {{ font-size: 50px; color: #f43f5e; margin-bottom: 16px; }}
                h2 {{ font-size: 24px; font-weight: 800; margin-bottom: 8px; color: #f43f5e; }}
                p {{ color: #94a3b8; font-size: 14px; line-height: 1.5; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="icon">✖</div>
                <h2>Ticket No Encontrado</h2>
                <p>El código <strong>{codigo_unico}</strong> no está registrado en el sistema o es inválido.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_invalid, status_code=404)

    # Datos del ticket válido
    evento_nombre = ticket.evento.nombre if ticket.evento else "Evento"
    estado_color = "#10b981" if ticket.estado == "vendido" else ("#f59e0b" if ticket.estado == "separado" else "#f43f5e")
    entregado_bg = "#06b6d4" if ticket.entregado else "#64748b"
    entregado_texto = f"Entregado el {ticket.fecha_hora_entrega.strftime('%d/%m/%Y %H:%M:%S')}" if ticket.entregado else "Pendiente de Entrega"

    html_valid = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Certificado de Ticket - {ticket.codigo_unico}</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: 'Plus Jakarta Sans', sans-serif;
                background: #0b0f19;
                background-image: radial-gradient(at 50% 0%, rgba(99, 102, 241, 0.2) 0px, transparent 70%);
                color: #f8fafc;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                padding: 20px;
            }}
            .ticket-card {{
                background: rgba(26, 34, 52, 0.85);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
                padding: 32px 24px;
                max-width: 420px;
                width: 100%;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
                position: relative;
                overflow: hidden;
            }}
            .ticket-card::before {{
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; height: 6px;
                background: linear-gradient(90deg, #6366f1, #10b981, #06b6d4);
            }}
            .badge-valid {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: rgba(16, 185, 129, 0.15);
                color: #10b981;
                border: 1px solid rgba(16, 185, 129, 0.3);
                padding: 6px 16px;
                border-radius: 999px;
                font-size: 13px;
                font-weight: 700;
                text-transform: uppercase;
                margin-bottom: 20px;
            }}
            .code-title {{
                font-size: 28px;
                font-weight: 800;
                letter-spacing: 2px;
                color: #6366f1;
                margin-bottom: 6px;
            }}
            .event-title {{
                font-size: 16px;
                color: #94a3b8;
                font-weight: 600;
                margin-bottom: 24px;
            }}
            .details-box {{
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 20px;
                text-align: left;
                margin-bottom: 24px;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
            .detail-row:last-child {{ border-bottom: none; }}
            .label {{ color: #94a3b8; font-size: 13px; font-weight: 500; }}
            .value {{ font-size: 14px; font-weight: 700; color: #f8fafc; }}
            .status-pill {{
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                background: {estado_color}22;
                color: {estado_color};
                border: 1px solid {estado_color}55;
            }}
            .delivery-badge {{
                display: block;
                padding: 12px;
                border-radius: 12px;
                background: {entregado_bg}22;
                color: {entregado_bg};
                border: 1px solid {entregado_bg}44;
                font-weight: 700;
                font-size: 14px;
            }}
            .footer-seal {{
                font-size: 12px;
                color: #64748b;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="ticket-card">
            <div class="badge-valid">✔ TICKET VÁLIDO</div>
            <div class="code-title">{ticket.codigo_unico}</div>
            <div class="event-title">{evento_nombre}</div>

            <div class="details-box">
                <div class="detail-row">
                    <span class="label">Alumno:</span>
                    <span class="value">{ticket.nombre_alumno}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Código Alumno:</span>
                    <span class="value">{ticket.codigo_alumno}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Estado Venta:</span>
                    <span class="status-pill">{ticket.estado}</span>
                </div>
            </div>

            <div class="delivery-badge">
                {entregado_texto}
            </div>

            <div class="footer-seal">
                Verificación Oficial • Sistema de Eventos 2026
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_valid)
