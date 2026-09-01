import os
import random
import string
import qrcode
from sqlalchemy.orm import Session
from app.models import Ticket, Evento

# Asegurar que el directorio de QR exista
QR_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "qrcodes")
os.makedirs(QR_DIRECTORY, exist_ok=True)

def generar_codigo_unico(db: Session, evento: Evento) -> str:
    """
    Genera un código único con el formato EVENTO-XXXX-RANDOM
    Ejemplo: POL2026-0001-A9F2
    """
    # Obtener prefijo del nombre del evento (primeras 3-5 letras sin espacios en mayúsculas)
    prefix = "".join(e for e in evento.nombre if e.isalnum()).upper()[:4]
    if not prefix:
        prefix = "EVT"

    # Contar boletos existentes para este evento para generar un índice secuencial
    total_tickets_evento = db.query(Ticket).filter(Ticket.evento_id == evento.id).count()
    secuencia = total_tickets_evento + 1

    while True:
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        codigo = f"{prefix}-{secuencia:04d}-{random_suffix}"
        
        # Verificar que sea único en la base de datos
        existing = db.query(Ticket).filter(Ticket.codigo_unico == codigo).first()
        if not existing:
            return codigo

def generar_qr_code(codigo_unico: str, host_base_url: str = "http://localhost:8000") -> str:
    """
    Genera una imagen QR conteniendo la URL "http://localhost:8000/ticket/{codigo_unico}"
    Guarda la imagen en static/qrcodes/{codigo_unico}.png
    Retorna la URL relativa de la imagen.
    """
    contenido_qr = f"{host_base_url.rstrip('/')}/ticket/{codigo_unico}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(contenido_qr)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    filename = f"{codigo_unico}.png"
    filepath = os.path.join(QR_DIRECTORY, filename)
    img.save(filepath)

    return f"/static/qrcodes/{filename}"
