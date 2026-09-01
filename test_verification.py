import os
import sys
from fastapi.testclient import TestClient

# Asegurar path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from seed import seed_database
from app.database import engine, Base

def run_tests():
    print("=== 1. Ejecutando Seed ===")
    seed_database()

    client = TestClient(app)

    print("\n=== 2. Probando Login ===")
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200, f"Login falló: {response.text}"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] Login exitoso. Token recibido correctamente.")

    print("\n=== 3. Probando Acceso Protegido sin Token ===")
    response_unauth = client.get("/eventos")
    assert response_unauth.status_code == 401, "Error: Debería retornar 401 Unauthorized"
    print("[OK] Ruta /eventos rechaza adecuadamente peticiones sin token.")

    print("\n=== 4. Obteniendo Lista de Eventos con Token ===")
    response_eventos = client.get("/eventos", headers=headers)
    assert response_eventos.status_code == 200, f"Obtener eventos falló: {response_eventos.text}"
    eventos = response_eventos.json()
    assert len(eventos) > 0, "No se encontraron eventos"
    evento_id = eventos[0]["id"]
    print(f"[OK] Lista de eventos obtenida. Usando evento ID: {evento_id} ({eventos[0]['nombre']})")

    print("\n=== 5. Creando Ticket y Verificando QR Code ===")
    ticket_payload = {
        "evento_id": evento_id,
        "nombre_alumno": "María Torres",
        "codigo_alumno": "202209999",
        "estado": "separado"
    }
    response_ticket = client.post("/tickets", json=ticket_payload, headers=headers)
    assert response_ticket.status_code == 201, f"Creación de ticket falló: {response_ticket.text}"
    ticket_data = response_ticket.json()
    
    codigo_unico = ticket_data["codigo_unico"]
    qr_image_url = ticket_data["qr_image_url"]

    print(f"[OK] Ticket creado exitosamente con código único: {codigo_unico}")
    print(f"[OK] URL del QR generado: {qr_image_url}")

    # Verificación física del archivo QR
    qr_filename = os.path.basename(qr_image_url)
    qr_filepath = os.path.join(os.path.dirname(__file__), "static", "qrcodes", qr_filename)
    assert os.path.exists(qr_filepath), f"El archivo QR no existe en la ruta física: {qr_filepath}"
    print(f"[OK] Archivo PNG verificado en el sistema de archivos: {qr_filepath}")

    print("\n=== 6. Probando Ruta Pública de Verificación de QR (/ticket/{codigo_unico}) ===")
    response_public = client.get(f"/ticket/{codigo_unico}")
    assert response_public.status_code == 200, f"Verificación pública falló: {response_public.text}"
    data_public = response_public.json()
    assert data_public["valido"] is True
    assert data_public["nombre_alumno"] == "María Torres"
    assert data_public["entregado"] is False
    print("[OK] Ruta pública de escaneo /ticket/{codigo_unico} funciona correctamente.")

    print("\n=== 7. Marcando Ticket como Entregado ===")
    response_entregado = client.post(f"/tickets/{codigo_unico}/entregar", headers=headers)
    assert response_entregado.status_code == 200, f"Entregar ticket falló: {response_entregado.text}"
    data_entregado = response_entregado.json()
    assert data_entregado["entregado"] is True
    assert data_entregado["estado"] == "vendido"
    assert data_entregado["fecha_hora_entrega"] is not None
    print(f"[OK] Ticket entregado exitosamente a las {data_entregado['fecha_hora_entrega']}.")

    print("\n=== TODAS LAS PRUEBAS AUTOMATIZADAS PASARON EXITOSAMENTE ===")

if __name__ == "__main__":
    run_tests()
