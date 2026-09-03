# 🎟️ Sistema de Gestión de Boletos Físicos Numerados (1 a 1000)

Sistema de gestión, cobranza, venta salón por salón, autocompletado de estudiantes matriculados, entrega y reporte de boletos para eventos universitarios (ej. *"Pollada 2026"*, *"Cachimbeada 2026"*).

Desarrollado con **FastAPI**, **SQLAlchemy**, **SQLite**, **JWT Auth**, **openpyxl**, y **Vanilla HTML/CSS/JS (Glassmorphic UI)**.

---

## 🎨 Características Principales

- **Boletos Físicos Numerados (1 a 1000)**: Sin códigos QR. Cada boleto se identifica por su número físico preimpreso.
- **Autocompletado de Matriculados (`EstudiantesMatriculados.xlsx`)**: Al escribir el código de alumno (6 dígitos), autocompleta instantáneamente su **Nombre**, **Carrera** (`INGENIERIA DE SISTEMAS`) y **Ciclo** desde el padrón de 550 estudiantes.
- **Soporte para Alumnos No Matriculados / Inteligencia Artificial / Externos**: Permite ingresar manualmente el Nombre, Carrera y Ciclo/DNI sin bloqueos para alumnos de otras escuelas o externas.
- **Venta Múltiple por Persona (Hasta 20 Boletos)**: Permite registrar compras múltiples asignadas a un solo código o DNI.
- **Persona Referencial que Recoge (`nombre_recolector`)**: Permite especificar quién recogerá cada una de las polladas (ej. apodos como *"Pepe"*, un amigo, o el mismo comprador).
- **Gestión Financiera & Pagos Parciales**:
  - Estados: `pagado` (100%), `parcialmente_pagado` (adelanto) y `separado` (sin pago).
  - Métodos de Pago: `efectivo`, `yape`, `plin`, `ninguno`.
  - Resaltado visual en entrega: Alerta llamativa indicando **monto abonado** y **saldo pendiente por cobrar**. Permite cobrar el saldo faltante al momento de entregar.
- **KPIs de Cobertura y Recaudación**:
  - Métrica de Cobertura: *"X de 550 estudiantes matriculados (Y%) tienen su boleto"*.
  - Indicadores de total recaudado (S/.), saldo pendiente (S/.), boletos pagados, parciales y entregados.
- **Exportación en Excel y CSV**: Descarga directa de archivos `.xlsx` y `.csv` con todas las columnas de comprador, recolector, estado, montos y entregas.

---

## ⚡ Instalación y Ejecución Rápida

### 1. Requisitos e Instalación
Abre la consola en la carpeta del proyecto y ejecuta:
```bash
pip install -r requirements.txt
```

### 2. Inicializar Base de Datos y Poblar Matriculados
Ejecuta el script para crear las tablas, el usuario administrador y cargar los 550 alumnos de `EstudiantesMatriculados.xlsx`:
```bash
python seed.py
```
- **Usuario por defecto**: `admin`
- **Contraseña por defecto**: `admin123`

### 3. Iniciar Servidor Accesible en Red Local
Ejecuta el script lanzador:
```bash
python run.py
```

Al iniciar, la consola mostrará un banner visual indicando las URLs de acceso:
```text
======================================================================
  🎟️   SISTEMA DE GESTIÓN DE TICKETS - SERVIDOR LOCAL Y RED   🎟️
======================================================================
  ► Acceso desde esta PC (Local):    http://localhost:8000
  ► Acceso desde Celular / Red Wi-Fi: http://192.168.1.50:8000
  ► Documentación Swagger API:        http://localhost:8000/docs
======================================================================
```

---

## 📱 Conexión desde Celulares en la Misma Red Wi-Fi

1. Conecta tu celular a la **misma red Wi-Fi** a la que está conectada tu computadora.
2. Abre el navegador del celular (Chrome / Safari) e ingresa a la URL proporcionada por `run.py` (ejemplo: `http://192.168.1.50:8000`).

---

## 🔄 Flujo Operativo de Uso

### 📋 1. Preventa Salón por Salón (Venta en Aula / Laptop)
1. El organizador ingresa en su laptop a `http://localhost:8000`.
2. Va a la pestaña **"Nueva Venta"**.
3. Escribe el código del alumno (6 cifras). El sistema autocompleta su **Nombre**, **Carrera** y **Ciclo** automáticamente.
4. Si el alumno desea 3 boletos, coloca cantidad `3` y boleto inicial `#101`.
5. El sistema genera los campos para ingresar quién recogerá cada pollada (`Boleto #101`: Pepe, `Boleto #102`: María, `Boleto #103`: Comprador).
6. Selecciona el estado (`pagado`, `parcialmente_pagado` o `separado`), ingresa el monto pagado y método de pago (`yape`/`plin`/`efectivo`).
7. Presiona **"Registrar y Asignar Boletos Físicos"**.

### 🎪 2. Día del Evento (Entrega de Polladas en Puerta con Celular)
1. El encargado de puerta abre `http://192.168.X.X:8000` en su celular y va a la pestaña **"Entrega de Polladas"**.
2. Escribe el número de boleto físico (ej. `101`) o busca por el apodo/nombre de la persona que recoge (`Pepe`).
3. El sistema muestra la tarjeta del boleto:
   - Si el boleto está **Parcialmente Pagado**, muestra la alerta: **⚠️ FALTA COBRAR: S/ 5.00**. Permite ingresar el cobro del saldo ahí mismo.
   - Si está **Pagado 100%**, muestra la confirmación en verde.
4. El encargado presiona **"Confirmar Entrega"**, confirmando en el cuadro modal. El servidor registra la fecha y hora exacta de entrega.
5. **Protección Anti-Duplicados**: Si se intenta entregar el boleto `#101` por segunda vez, el sistema bloquea la acción con una alerta roja indicando que ya fue entregado y la hora exacta de la entrega previa.

### 📊 3. Cierre y Exportación de Reportes
1. En el **Dashboard**, los organizadores analizan las métricas de cobertura de matriculados (ej. *"145 de 550 estudiantes (26.36%) tienen su boleto"*) y la recaudación cobrada vs. saldo pendiente.
2. Descargan el reporte consolidado en **Excel (`.xlsx`)** o **CSV (`.csv`)** con los botones correspondientes.
