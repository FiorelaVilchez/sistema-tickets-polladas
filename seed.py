import sys
import os

# Agregar directorio actual al sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.database import engine, SessionLocal, Base
from app.models import Usuario, Evento, Ticket
from app.auth import get_password_hash

def seed_database():
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Crear usuario admin por defecto si no existe ninguno
        user_count = db.query(Usuario).count()
        if user_count == 0:
            admin_user = Usuario(
                username="admin",
                password_hash=get_password_hash("admin123")
            )
            db.add(admin_user)
            print("[OK] Usuario por defecto creado -> Username: admin | Password: admin123")
        else:
            print(f"[INFO] Ya existen {user_count} usuarios en la base de datos.")

        # 2. Crear eventos de prueba si no existen
        evento_count = db.query(Evento).count()
        if evento_count == 0:
            evento1 = Evento(
                nombre="Pollada 2026",
                fecha=datetime(2026, 10, 15, 12, 0, 0),
                activo=True
            )
            evento2 = Evento(
                nombre="Cachimbeada 2026",
                fecha=datetime(2026, 11, 20, 20, 0, 0),
                activo=True
            )
            db.add_all([evento1, evento2])
            db.commit()
            print("[OK] Eventos iniciales creados: 'Pollada 2026' y 'Cachimbeada 2026'")
        else:
            print(f"[INFO] Ya existen {evento_count} eventos en la base de datos.")

        db.commit()
        print("\nBase de datos inicializada correctamente.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error al inicializar la base de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
