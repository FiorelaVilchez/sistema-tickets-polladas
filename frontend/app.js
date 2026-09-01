/**
 * SISTEMA DE TICKETS - FRONTEND JAVASCRIPT VANILLA
 */

// API Base URL
const API_BASE = window.location.origin;

// Estado Global
let token = localStorage.getItem('token') || null;
let currentEvents = [];
let selectedEventId = null;
let html5QrcodeScanner = null;
let currentTicketForDelivery = null;

// Helper para Toast Notifications
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-circle-exclamation' : 'fa-triangle-exclamation');
  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
  
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// Headers de Autenticación
function getHeaders(isJson = true) {
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (isJson) {
    headers['Content-Type'] = 'application/json';
  }
  return headers;
}

// Navegación entre Pantallas (SPA)
function switchScreen(screenName) {
  document.querySelectorAll('.screen-view').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.nav-tab, .mobile-nav-item').forEach(el => el.classList.remove('active'));

  const targetScreen = document.getElementById(`screen-${screenName}`);
  if (targetScreen) {
    targetScreen.classList.remove('hidden');
  }

  // Activar pestañas de navegación
  document.querySelectorAll(`[data-screen="${screenName}"]`).forEach(el => el.classList.add('active'));

  // Cerrar escáner si se navega a otra pantalla
  if (screenName !== 'entrega' && html5QrcodeScanner) {
    stopScanner();
  }

  // Cargar datos según la pantalla
  if (screenName === 'dashboard' && selectedEventId) {
    loadDashboard(selectedEventId);
  }
}

// Checkear sesión activa
async function checkAuth() {
  if (!token) {
    document.getElementById('main-header').classList.add('hidden');
    switchScreen('login');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
    if (res.ok) {
      const user = await res.json();
      document.getElementById('user-display').innerHTML = `<i class="fa-solid fa-circle-user"></i> ${user.username}`;
      document.getElementById('main-header').classList.remove('hidden');
      await loadEvents();
      switchScreen('dashboard');
    } else {
      logout();
    }
  } catch (err) {
    console.error('Error al verificar sesión:', err);
    logout();
  }
}

// Login
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const usernameInput = document.getElementById('login-username').value;
  const passwordInput = document.getElementById('login-password').value;
  const errorBox = document.getElementById('login-error');

  errorBox.classList.add('hidden');

  const formData = new URLSearchParams();
  formData.append('username', usernameInput);
  formData.append('password', passwordInput);

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      token = data.access_token;
      localStorage.setItem('token', token);
      showToast('¡Bienvenido al sistema!', 'success');
      await checkAuth();
    } else {
      const error = await res.json();
      errorBox.textContent = error.detail || 'Credenciales incorrectas';
      errorBox.classList.remove('hidden');
    }
  } catch (err) {
    errorBox.textContent = 'Error de conexión con el servidor.';
    errorBox.classList.remove('hidden');
  }
});

// Logout
function logout() {
  token = null;
  localStorage.removeItem('token');
  document.getElementById('main-header').classList.add('hidden');
  switchScreen('login');
  showToast('Sesión cerrada correctamente', 'success');
}
document.getElementById('btn-logout').addEventListener('click', logout);

// Toggle Mostrar Contraseña
document.getElementById('btn-toggle-pwd').addEventListener('click', () => {
  const pwdInput = document.getElementById('login-password');
  const icon = document.querySelector('#btn-toggle-pwd i');
  if (pwdInput.type === 'password') {
    pwdInput.type = 'text';
    icon.className = 'fa-solid fa-eye-slash';
  } else {
    pwdInput.type = 'password';
    icon.className = 'fa-solid fa-eye';
  }
});

// Cargar Eventos
async function loadEvents() {
  try {
    const res = await fetch(`${API_BASE}/eventos`, { headers: getHeaders() });
    if (res.ok) {
      currentEvents = await res.json();
      
      const globalSelect = document.getElementById('global-event-select');
      const ventaSelect = document.getElementById('venta-evento-select');
      const adicionalSelect = document.getElementById('adicional-evento-select');

      globalSelect.innerHTML = '';
      ventaSelect.innerHTML = '';
      adicionalSelect.innerHTML = '';

      if (currentEvents.length === 0) {
        globalSelect.innerHTML = '<option value="">Sin eventos activos</option>';
        return;
      }

      currentEvents.forEach(evt => {
        const opt = `<option value="${evt.id}">${evt.nombre}</option>`;
        globalSelect.innerHTML += opt;
        ventaSelect.innerHTML += opt;
        adicionalSelect.innerHTML += opt;
      });

      selectedEventId = currentEvents[0].id;
      globalSelect.value = selectedEventId;
    }
  } catch (err) {
    console.error('Error al cargar eventos:', err);
  }
}

// Selector Global de Eventos
document.getElementById('global-event-select').addEventListener('change', (e) => {
  selectedEventId = e.target.value;
  loadDashboard(selectedEventId);
});

// Cargar Dashboard & KPIs
async function loadDashboard(eventId) {
  if (!eventId) return;

  try {
    // 1. Cargar KPIs
    const resKpi = await fetch(`${API_BASE}/eventos/${eventId}/kpis`, { headers: getHeaders() });
    if (resKpi.ok) {
      const kpi = await resKpi.json();
      document.getElementById('kpi-event-name').textContent = kpi.nombre_evento;
      document.getElementById('kpi-total').textContent = kpi.total_tickets;
      document.getElementById('kpi-vendidos').textContent = kpi.vendidos;
      document.getElementById('kpi-separados').textContent = kpi.separados;
      document.getElementById('kpi-no-vendidos').textContent = kpi.no_vendidos;
      document.getElementById('kpi-entregados').textContent = kpi.entregados;
    }

    // 2. Cargar Lista de Tickets del Evento
    const resTickets = await fetch(`${API_BASE}/tickets?evento_id=${eventId}`, { headers: getHeaders() });
    if (resTickets.ok) {
      const tickets = await resTickets.json();
      renderTicketsTable(tickets);
    }
  } catch (err) {
    console.error('Error al cargar dashboard:', err);
  }
}

// Renderizar Tabla de Tickets
function renderTicketsTable(tickets) {
  const tbody = document.getElementById('tickets-table-body');
  tbody.innerHTML = '';

  if (tickets.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">No hay tickets registrados en este evento.</td></tr>';
    return;
  }

  tickets.forEach(t => {
    const estadoClass = `badge-${t.estado}`;
    const entregadoBadge = t.entregado ? '<span class="badge badge-entregado"><i class="fa-solid fa-check"></i> Sí</span>' : '<span class="badge badge-no_vendido">No</span>';
    const fechaEntrega = t.fecha_hora_entrega ? new Date(t.fecha_hora_entrega).toLocaleString() : '-';

    const row = document.createElement('tr');
    row.innerHTML = `
      <td><strong>${t.codigo_unico}</strong></td>
      <td>${t.nombre_alumno}</td>
      <td>${t.codigo_alumno}</td>
      <td><span class="badge ${estadoClass}">${t.estado}</span></td>
      <td>${entregadoBadge}</td>
      <td>${fechaEntrega}</td>
    `;
    tbody.appendChild(row);
  });
}

// Filtro de Búsqueda en Tabla del Dashboard
document.getElementById('table-search-input').addEventListener('input', (e) => {
  const term = e.target.value.toLowerCase();
  const rows = document.querySelectorAll('#tickets-table-body tr');
  rows.forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(term) ? '' : 'none';
  });
});

// Exportar Excel
document.getElementById('btn-export-excel').addEventListener('click', async () => {
  if (!selectedEventId) return;
  try {
    const res = await fetch(`${API_BASE}/eventos/${selectedEventId}/exportar/excel`, { headers: getHeaders(false) });
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tickets_evento_${selectedEventId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast('Archivo Excel descargado', 'success');
    }
  } catch (err) {
    showToast('Error al descargar archivo Excel', 'error');
  }
});

// Exportar CSV
document.getElementById('btn-export-csv').addEventListener('click', async () => {
  if (!selectedEventId) return;
  try {
    const res = await fetch(`${API_BASE}/eventos/${selectedEventId}/exportar/csv`, { headers: getHeaders(false) });
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tickets_evento_${selectedEventId}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast('Archivo CSV descargado', 'success');
    }
  } catch (err) {
    showToast('Error al descargar archivo CSV', 'error');
  }
});

// Registrar Nueva Venta
document.getElementById('venta-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const payload = {
    evento_id: parseInt(document.getElementById('venta-evento-select').value),
    nombre_alumno: document.getElementById('venta-nombre').value,
    codigo_alumno: document.getElementById('venta-codigo').value,
    estado: document.getElementById('venta-estado').value
  };

  try {
    const res = await fetch(`${API_BASE}/tickets/registrar-venta`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const ticket = await res.json();
      showToast('¡Venta registrada exitosamente!', 'success');

      // Renderizar resultado con QR
      document.getElementById('res-codigo-unico').textContent = ticket.codigo_unico;
      document.getElementById('res-nombre-alumno').textContent = ticket.nombre_alumno;
      document.getElementById('res-codigo-alumno').textContent = ticket.codigo_alumno;
      document.getElementById('res-qr-image').src = ticket.qr_image_url;

      const estadoBadge = document.getElementById('res-estado-badge');
      estadoBadge.className = `badge badge-${ticket.estado}`;
      estadoBadge.textContent = ticket.estado;

      document.getElementById('ticket-result-card').classList.remove('hidden');

      // Limpiar formulario
      document.getElementById('venta-nombre').value = '';
      document.getElementById('venta-codigo').value = '';
    } else {
      const err = await res.json();
      showToast(err.detail || 'Error al registrar venta', 'error');
    }
  } catch (err) {
    showToast('Error de conexión', 'error');
  }
});

// Imprimir / Guardar QR
document.getElementById('btn-print-ticket').addEventListener('click', () => {
  const qrImgSrc = document.getElementById('res-qr-image').src;
  const codigo = document.getElementById('res-codigo-unico').textContent;
  const printWin = window.open('', '_blank');
  printWin.document.write(`
    <html>
      <head><title>Ticket ${codigo}</title></head>
      <body style="text-align:center; font-family:sans-serif; padding:20px;">
        <h2>${codigo}</h2>
        <img src="${qrImgSrc}" style="width:200px; height:200px;">
        <p>Ticket verificado - Sistema de Eventos</p>
        <script>window.onload = function() { window.print(); window.close(); }</script>
      </body>
    </html>
  `);
});

// Entrega & Escáner QR
document.getElementById('entrega-search-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = document.getElementById('entrega-query').value.trim();
  if (query) {
    await searchTicketsForDelivery(query);
  }
});

async function searchTicketsForDelivery(query) {
  try {
    const res = await fetch(`${API_BASE}/tickets/buscar?q=${encodeURIComponent(query)}`, { headers: getHeaders() });
    if (res.ok) {
      const tickets = await res.json();
      renderSearchResults(tickets);
    }
  } catch (err) {
    showToast('Error al buscar ticket', 'error');
  }
}

function renderSearchResults(tickets) {
  const container = document.getElementById('entrega-results-container');
  container.innerHTML = '';

  if (tickets.length === 0) {
    container.innerHTML = '<div class="alert alert-warning text-center">No se encontraron tickets con el criterio ingresado.</div>';
    return;
  }

  tickets.forEach(t => {
    const card = document.createElement('div');
    card.className = 'glass-panel ticket-found-card';

    const estadoBadge = `<span class="badge badge-${t.estado}">${t.estado}</span>`;
    const entregadoBadge = t.entregado 
      ? `<span class="badge badge-entregado"><i class="fa-solid fa-box-check"></i> ENTREGADO</span>`
      : `<span class="badge badge-no_vendido"><i class="fa-solid fa-clock"></i> PENDIENTE DE ENTREGA</span>`;

    const fechaEntregaInfo = t.fecha_hora_entrega 
      ? `<p class="text-sm text-muted"><strong>Fecha Entrega:</strong> ${new Date(t.fecha_hora_entrega).toLocaleString()}</p>` 
      : '';

    card.innerHTML = `
      <div class="ticket-found-header">
        <h4>${t.codigo_unico}</h4>
        <div>${estadoBadge} ${entregadoBadge}</div>
      </div>
      <div class="ticket-found-info">
        <p><strong>Alumno:</strong> ${t.nombre_alumno}</p>
        <p><strong>Código Alumno:</strong> ${t.codigo_alumno}</p>
        ${fechaEntregaInfo}
      </div>
      <div class="ticket-found-actions">
        ${!t.entregado ? `<button class="btn btn-emerald btn-confirm-entrega" data-codigo="${t.codigo_unico}" data-nombre="${t.nombre_alumno}">
          <i class="fa-solid fa-check-double"></i> Confirmar Entrega
        </button>` : `<button class="btn btn-secondary" disabled><i class="fa-solid fa-check"></i> Ya Entregado</button>`}
        
        <button class="btn btn-secondary btn-vender-adicional" data-nombre="${t.nombre_alumno}" data-codigo="${t.codigo_alumno}">
          <i class="fa-solid fa-plus"></i> Vender Ticket Adicional
        </button>
      </div>
    `;

    container.appendChild(card);
  });

  // Listener para botones de entrega
  document.querySelectorAll('.btn-confirm-entrega').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const codigo = e.currentTarget.getAttribute('data-codigo');
      const alumno = e.currentTarget.getAttribute('data-nombre');
      openConfirmModal(codigo, alumno);
    });
  });

  // Listener para botones de venta adicional
  document.querySelectorAll('.btn-vender-adicional').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const nombre = e.currentTarget.getAttribute('data-nombre');
      const codigo = e.currentTarget.getAttribute('data-codigo');
      openAdicionalModal(nombre, codigo);
    });
  });
}

// Modal Confirmación de Entrega
function openConfirmModal(codigo, alumno) {
  currentTicketForDelivery = codigo;
  document.getElementById('modal-confirm-codigo').textContent = codigo;
  document.getElementById('modal-confirm-alumno').textContent = alumno;
  document.getElementById('confirm-modal').classList.remove('hidden');
}

document.getElementById('btn-cancel-entrega').addEventListener('click', () => {
  document.getElementById('confirm-modal').classList.add('hidden');
  currentTicketForDelivery = null;
});

document.getElementById('btn-proceed-entrega').addEventListener('click', async () => {
  if (!currentTicketForDelivery) return;

  try {
    const res = await fetch(`${API_BASE}/tickets/confirmar-entrega`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ codigo_unico: currentTicketForDelivery })
    });

    document.getElementById('confirm-modal').classList.add('hidden');

    if (res.ok) {
      showToast(`¡Entrega confirmada para ${currentTicketForDelivery}!`, 'success');
      // Recargar búsqueda
      await searchTicketsForDelivery(currentTicketForDelivery);
      if (selectedEventId) loadDashboard(selectedEventId);
    } else {
      const err = await res.json();
      showToast(err.detail || 'Error al confirmar la entrega', 'error');
    }
  } catch (err) {
    showToast('Error de conexión con el servidor', 'error');
  }
});

// Modal Venta Adicional
function openAdicionalModal(nombre, codigo) {
  document.getElementById('adicional-nombre').value = nombre;
  document.getElementById('adicional-codigo').value = codigo;
  document.getElementById('adicional-modal').classList.remove('hidden');
}

document.getElementById('btn-cancel-adicional').addEventListener('click', () => {
  document.getElementById('adicional-modal').classList.add('hidden');
});

document.getElementById('adicional-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    evento_id: parseInt(document.getElementById('adicional-evento-select').value),
    nombre_alumno: document.getElementById('adicional-nombre').value,
    codigo_alumno: document.getElementById('adicional-codigo').value,
    estado: document.getElementById('adicional-estado').value
  };

  try {
    const res = await fetch(`${API_BASE}/tickets/registrar-venta`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const newTicket = await res.json();
      showToast(`¡Ticket adicional ${newTicket.codigo_unico} creado!`, 'success');
      document.getElementById('adicional-modal').classList.add('hidden');
      await searchTicketsForDelivery(newTicket.codigo_alumno);
    } else {
      const err = await res.json();
      showToast(err.detail || 'Error al crear ticket adicional', 'error');
    }
  } catch (err) {
    showToast('Error de conexión', 'error');
  }
});

// Escáner de Cámara HTML5 QR Code
document.getElementById('btn-toggle-scanner').addEventListener('click', () => {
  const wrapper = document.getElementById('scanner-wrapper');
  if (wrapper.classList.contains('hidden')) {
    wrapper.classList.remove('hidden');
    startScanner();
  } else {
    stopScanner();
  }
});

document.getElementById('btn-close-scanner').addEventListener('click', () => {
  stopScanner();
});

function startScanner() {
  if (html5QrcodeScanner) return;

  html5QrcodeScanner = new Html5Qrcode("qr-reader");
  const config = { fps: 10, qrbox: { width: 250, height: 250 } };

  html5QrcodeScanner.start(
    { facingMode: "environment" },
    config,
    onScanSuccess,
    onScanFailure
  ).catch(err => {
    console.error("Error al iniciar cámara:", err);
    showToast("No se pudo iniciar la cámara del dispositivo", "error");
    stopScanner();
  });
}

function stopScanner() {
  if (html5QrcodeScanner) {
    html5QrcodeScanner.stop().then(() => {
      html5QrcodeScanner.clear();
      html5QrcodeScanner = null;
      document.getElementById('scanner-wrapper').classList.add('hidden');
    }).catch(err => {
      console.error("Error al detener cámara:", err);
      html5QrcodeScanner = null;
      document.getElementById('scanner-wrapper').classList.add('hidden');
    });
  } else {
    document.getElementById('scanner-wrapper').classList.add('hidden');
  }
}

function onScanSuccess(decodedText) {
  stopScanner();
  showToast(`QR Escaneado: ${decodedText}`, 'success');

  // Si el texto es una URL completa (http://localhost:8000/ticket/POLL-0001-XXXX) extraer el código
  let ticketCode = decodedText;
  if (decodedText.includes('/ticket/')) {
    ticketCode = decodedText.split('/ticket/')[1];
  }

  document.getElementById('entrega-query').value = ticketCode;
  searchTicketsForDelivery(ticketCode);
}

function onScanFailure(error) {
  // Ignorar fallos de escaneo frame a frame
}

// Escuchadores de pestañas de navegación
document.querySelectorAll('[data-screen]').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const screen = e.currentTarget.getAttribute('data-screen');
    switchScreen(screen);
  });
});

// Inicialización de la app
document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
});
