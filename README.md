# Sistema de Gestión de Tickets (FastAPI + SQLAlchemy)

Backend completo en **FastAPI** con **SQLite** y **SQLAlchemy** para la administración, emisión, autenticación JWT y validación con código QR de tickets para eventos ("Pollada 2026", "Cachimbeada 2026", etc.).

---

## 🚀 Características
- **Modelos SQLAlchemy**: `Usuario`, `Evento` y `Ticket`.
- **Autenticación JWT**: Login seguro con contraseñas encriptadas mediante `bcrypt`.
- **Generación Automática de QR**: Al crear un ticket se genera un `codigo_unico` (formato `EVENTO-0001-XXXX`) y una imagen QR PNG guardada en `/static/qrcodes/`.
- **Verificación de QR**: El QR enlaza a `http://localhost:8000/ticket/{codigo_unico}` (endpoint público para consulta al escanear con escáner/celular).
- **Rutas Protegidas**: Todas las rutas de la API, excepto login y la verificación pública del QR, requieren estar autenticado.

---

## 📁 Estructura del Proyecto

```
sistema-tickets/
├── app/
│   ├── __init__.py
│   ├── main.py          # Servidor principal FastAPI y configuración de routers
│   ├── database.py      # Conexión SQLAlchemy y gestión de la sesión SQLite
│   ├── models.py        # Modelos ORM (Usuario, Evento, Ticket)
│   ├── schemas.py       # Esquemas Pydantic para peticiones y respuestas
│   ├── auth.py          # Autenticación JWT y hash de contraseñas
│   ├── utils.py         # Autogeneración de código único y creador de QR PNG
│   └── routers/
│       ├── __init__.py
│       ├── auth.py      # Endpoints /auth/login y /auth/me
│       ├── eventos.py   # CRUD de eventos (/eventos)
│       └── tickets.py   # Gestión de tickets y entrega (/tickets)
├── static/
│   └── qrcodes/         # Carpeta donde se guardan las imágenes QR generadas
├── seed.py              # Script para inicializar BD y usuario admin
├── requirements.txt     # Dependencias del proyecto
└── README.md
```

---

## 🛠️ Instalación y Configuración

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Inicializar la base de datos y usuario admin**:
   ```bash
   python seed.py
   ```
   *Esto creará la base de datos `sistema_tickets.db`, los eventos de prueba y el usuario predeterminado:*
   - **Usuario**: `admin`
   - **Contraseña**: `admin123`

3. **Iniciar el servidor en modo desarrollo**:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 📌 Documentación Interactiva de API

Una vez iniciado el servidor, accede a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔑 Autenticación JWT

1. Envía una petición `POST` a `/auth/login` con:
   - `username`: `admin`
   - `password`: `admin123`
2. Copia el token JWT en las peticiones agregando la cabecera:
   `Authorization: Bearer <tu_token_jwt>`
*(En Swagger UI, usa el botón **Authorize** en la esquina superior derecha).*

---

## 🎟️ Ejemplo de Uso de Endpoints

### Crear un Ticket (Autenticado)
`POST /tickets`
```json
{
  "evento_id": 1,
  "nombre_alumno": "Juan Pérez",
  "codigo_alumno": "202100123",
  "estado": "no_vendido"
}
```
**Respuesta:**
```json
{
  "id": 1,
  "codigo_unico": "POLL-0001-A9F2",
  "evento_id": 1,
  "nombre_alumno": "Juan Pérez",
  "codigo_alumno": "202100123",
  "estado": "no_vendido",
  "fecha_hora_entrega": null,
  "entregado": false,
  "qr_image_url": "/static/qrcodes/POLL-0001-A9F2.png"
}
```

### Escaneo / Verificación Pública del QR
`GET /ticket/POLL-0001-A9F2` (No requiere token)
Devuelve la información de validez y entrega del ticket al escanear la imagen QR desde la cámara.

### Entregar Ticket (Autenticado)
`POST /tickets/POLL-0001-A9F2/entregar`
Marca el ticket como `entregado=true`, `estado="vendido"` y registra la fecha/hora actual.
