# Sistema de Gestión de Tickets (FastAPI + SQLAlchemy)

Backend completo en **FastAPI** con **SQLite** y **SQLAlchemy** para la administración, emisión, autenticación JWT, entrega y reporte de tickets para eventos ("Pollada 2026", "Cachimbeada 2026", etc.).

---

## 🚀 Características y Funcionalidades

- **Modelos SQLAlchemy**: `Usuario`, `Evento` y `Ticket`.
- **Autenticación JWT**: Login seguro (`/auth/login`) con contraseñas encriptadas mediante `bcrypt`.
- **Registrar Venta / Ticket Adicional**: `POST /tickets/registrar-venta` genera el `codigo_unico` y el código QR PNG en `static/qrcodes/`.
- **Búsqueda Avanzada de Tickets**: `GET /tickets/buscar` permite buscar por `codigo_alumno` o `codigo_unico`.
- **Confirmación de Entrega con Control Anti-Duplicado**: `POST /tickets/confirmar-entrega` marca el ticket como entregado registrando la fecha/hora actual del servidor y rechaza entregas duplicadas con error HTTP 400.
- **KPIs y Métricas por Evento**: `GET /eventos/{evento_id}/kpis` calcula cantidad de tickets vendidos, separados (no recogidos), no vendidos y entregados.
- **Exportación en Excel y CSV**:
  - `GET /eventos/{evento_id}/exportar/excel` (genera archivo `.xlsx` con `openpyxl`).
  - `GET /eventos/{evento_id}/exportar/csv` (genera archivo `.csv`).
- **Verificación Pública de QR**: `GET /ticket/{codigo_unico}` accesible sin autenticación al escanear con la cámara del celular.

---

## 📁 Estructura del Proyecto

```
sistema-tickets/
├── app/
│   ├── __init__.py
│   ├── main.py          # Servidor principal FastAPI
│   ├── database.py      # Conexión SQLAlchemy y gestión de la sesión SQLite
│   ├── models.py        # Modelos ORM (Usuario, Evento, Ticket)
│   ├── schemas.py       # Esquemas Pydantic
│   ├── auth.py          # Autenticación JWT y hash de contraseñas con bcrypt
│   ├── utils.py         # Autogeneración de código único y creador de QR PNG
│   └── routers/
│       ├── __init__.py
│       ├── auth.py      # Endpoints /auth/login, /auth/me y /auth/registro
│       ├── eventos.py   # CRUD, KPIs y Exportación Excel/CSV (/eventos)
│       └── tickets.py   # Registro de venta, búsqueda, entrega y tickets (/tickets)
├── static/
│   └── qrcodes/         # Carpeta donde se guardan las imágenes QR generadas
├── seed.py              # Script para inicializar BD y usuario admin
├── test_new_endpoints.py# Suite de pruebas automatizadas para todos los endpoints
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
   *Esto creará la base de datos `sistema_tickets.db`, eventos de prueba y el usuario predeterminado:*
   - **Usuario**: `admin`
   - **Contraseña**: `admin123`

3. **Iniciar el servidor en modo desarrollo**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Ejecutar Suite de Pruebas**:
   ```bash
   python test_new_endpoints.py
   ```

---

## 📌 Documentación Interactiva de API

Accede con el servidor en ejecución a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🔑 Autenticación JWT

1. Envía una petición `POST` a `/auth/login` con:
   - `username`: `admin`
   - `password`: `admin123`
2. Copia el token JWT en las peticiones agregando la cabecera:
   `Authorization: Bearer <tu_token_jwt>`

---

## 🎟️ Resumen de Nuevos Endpoints

### 1. Registrar Venta / Vender Ticket Adicional
`POST /tickets/registrar-venta`
```json
{
  "evento_id": 1,
  "nombre_alumno": "Carlos Mendoza",
  "codigo_alumno": "202400111",
  "estado": "vendido"
}
```

### 2. Buscar Ticket
`GET /tickets/buscar?codigo_alumno=202400111`
`GET /tickets/buscar?codigo_unico=POLL-0001-A9F2`

### 3. Confirmar Entrega (Anti-Duplicados)
`POST /tickets/confirmar-entrega`
```json
{
  "codigo_unico": "POLL-0001-A9F2"
}
```
*Si ya fue entregado, devuelve error HTTP 400 con la fecha exacta de entrega previa.*

### 4. KPIs por Evento
`GET /eventos/1/kpis`
```json
{
  "evento_id": 1,
  "nombre_evento": "Pollada 2026",
  "total_tickets": 25,
  "vendidos": 18,
  "separados": 5,
  "no_vendidos": 2,
  "entregados": 12
}
```

### 5. Exportar a Excel
`GET /eventos/1/exportar/excel` -> Descarga archivo `tickets_Pollada_2026.xlsx`

### 6. Exportar a CSV
`GET /eventos/1/exportar/csv` -> Descarga archivo `tickets_Pollada_2026.csv`
