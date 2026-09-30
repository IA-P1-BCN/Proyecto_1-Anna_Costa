const pantallaLogin = document.getElementById("pantalla-login");
const pantallaTaximetro = document.getElementById("pantalla-taximetro");
const formLogin = document.getElementById("form-login");
const formRegistro = document.getElementById("form-registro");
const btnMostrarRegistro = document.getElementById("btn-mostrar-registro");
const mensajeLoginEl = document.getElementById("mensaje-login");
const btnLogout = document.getElementById("btn-logout");

const estadoEl = document.getElementById("estado");
const importeEl = document.getElementById("importe");
const mensajeEl = document.getElementById("mensaje");
const historialBody = document.getElementById("historial-body");

const btnIniciar = document.getElementById("btn-iniciar");
const btnParado = document.getElementById("btn-parado");
const btnMovimiento = document.getElementById("btn-movimiento");
const btnFinalizar = document.getElementById("btn-finalizar");

document.querySelectorAll(".boton-ver-clave").forEach((boton) => {
  const input = document.getElementById(boton.dataset.input);
  if (!input) return;
  boton.addEventListener("click", () => {
    const mostrar = input.type === "password";
    input.type = mostrar ? "text" : "password";
    boton.setAttribute("aria-pressed", String(mostrar));
    boton.setAttribute("aria-label", mostrar ? "Ocultar contraseña" : "Mostrar contraseña");
    boton.title = mostrar ? "Ocultar contraseña" : "Mostrar contraseña";
    boton.querySelector(".icono-ver").hidden = mostrar;
    boton.querySelector(".icono-ocultar").hidden = !mostrar;
  });
});

const nombreUsuarioEl = document.getElementById("nombre-usuario");
const rolUsuarioEl = document.getElementById("rol-usuario");
const resumenConductoresEl = document.getElementById("resumen-conductores");
const listaResumenConductoresEl = document.getElementById("lista-resumen-conductores");
const totalGeneralEl = document.getElementById("total-general");
const panelTarifasEl = document.getElementById("panel-tarifas");
const formTarifas = document.getElementById("form-tarifas");
const mensajeTarifasEl = document.getElementById("mensaje-tarifas");
const inputTarifaParado = document.getElementById("input-tarifa-parado");
const inputTarifaMovimiento = document.getElementById("input-tarifa-movimiento");

let token = null;
let nombreUsuario = null;
let rolUsuario = null;
let carreraId = null;
let intervalo = null;

try {
  token = sessionStorage.getItem("taximetro_token");
  nombreUsuario = sessionStorage.getItem("taximetro_usuario");
  rolUsuario = sessionStorage.getItem("taximetro_rol");
} catch {
  token = null;
  nombreUsuario = null;
  rolUsuario = null;
}

function guardarSesion(valorToken, valorUsuario, valorRol) {
  token = valorToken;
  nombreUsuario = valorUsuario;
  rolUsuario = valorRol;
  try {
    sessionStorage.setItem("taximetro_token", valorToken);
    sessionStorage.setItem("taximetro_usuario", valorUsuario);
    sessionStorage.setItem("taximetro_rol", valorRol);
  } catch {}
}

function limpiarSesion() {
  token = null;
  nombreUsuario = null;
  rolUsuario = null;
  try {
    sessionStorage.removeItem("taximetro_token");
    sessionStorage.removeItem("taximetro_usuario");
    sessionStorage.removeItem("taximetro_rol");
  } catch {}
}

function mostrarMensaje(texto) {
  mensajeEl.textContent = texto || "";
}

function actualizarPanel(carrera) {
  estadoEl.textContent = carrera.en_curso ? carrera.estado.toUpperCase() : "FINALIZADA";
  estadoEl.className = "estado " + (carrera.en_curso ? carrera.estado : "inactivo");
  importeEl.textContent = `${carrera.importe_en_vivo.toFixed(2)} €`;
}

function activarControles(enCurso) {
  btnIniciar.disabled = enCurso;
  btnParado.disabled = !enCurso;
  btnMovimiento.disabled = !enCurso;
  btnFinalizar.disabled = !enCurso;
}

function mostrarLogin() {
  resetearPanel();
  pantallaTaximetro.hidden = true;
  pantallaLogin.hidden = false;
}

async function cargarPanelTarifas() {
  if (rolUsuario !== "responsable") {
    panelTarifasEl.hidden = true;
    return;
  }
  panelTarifasEl.hidden = false;
  try {
    const tarifas = await llamarApi("/tarifas");
    inputTarifaParado.value = tarifas.tarifa_parado;
    inputTarifaMovimiento.value = tarifas.tarifa_movimiento;
  } catch (error) {
    mensajeTarifasEl.textContent = `No se pudieron cargar las tarifas: ${error.message}`;
  }
}

function seguirCarrera(carrera) {
  carreraId = carrera.id;
  actualizarPanel(carrera);
  activarControles(true);
  clearInterval(intervalo);
  intervalo = setInterval(refrescarCarreraActual, 1000);
}

function resetearPanel() {
  clearInterval(intervalo);
  carreraId = null;
  estadoEl.textContent = "Sin carrera";
  estadoEl.className = "estado inactivo";
  importeEl.textContent = "0.00 €";
  activarControles(false);
}

function mostrarTaximetro() {
  pantallaLogin.hidden = true;
  pantallaTaximetro.hidden = false;
  if (nombreUsuarioEl) nombreUsuarioEl.textContent = nombreUsuario || "";
  if (rolUsuarioEl) {
    rolUsuarioEl.textContent = rolUsuario === "responsable" ? "responsable de flota" : "taxista";
  }
  resetearPanel();
  cargarHistorial();
  cargarPanelTarifas();
}

async function llamarApi(path, options = {}) {
  const respuesta = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!respuesta.ok) {
    if (respuesta.status === 401) {
      limpiarSesion();
      mostrarLogin();
    }
    const detalle = await respuesta.json().catch(() => ({}));
    throw new Error(detalle.detail || `Error ${respuesta.status}`);
  }
  return respuesta.json();
}

async function iniciarCarrera() {
  btnIniciar.disabled = true;
  try {
    mostrarMensaje("");
    const carrera = await llamarApi("/carreras", { method: "POST" });
    seguirCarrera(carrera);
    await cargarHistorial();
  } catch (error) {
    // Si ya había una en curso (otra pestaña, sesión anterior), la retomamos.
    if (token) await cargarHistorial();
    activarControles(Boolean(carreraId));
    mostrarMensaje(`No se pudo iniciar la carrera: ${error.message}`);
  }
}

async function cambiarEstado(nuevoEstado) {
  if (!carreraId) return;
  try {
    const carrera = await llamarApi(`/carreras/${carreraId}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: nuevoEstado }),
    });
    actualizarPanel(carrera);
  } catch (error) {
    mostrarMensaje(`No se pudo cambiar de estado: ${error.message}`);
  }
}

async function finalizarCarrera() {
  if (!carreraId) return;
  try {
    const carrera = await llamarApi(`/carreras/${carreraId}/finalizar`, { method: "POST" });
    actualizarPanel(carrera);
    resetearControlesTrasFinalizar();
    await cargarHistorial();
  } catch (error) {
    mostrarMensaje(`No se pudo finalizar la carrera: ${error.message}`);
  }
}

let refrescando = false;
let sinConexion = false;

async function refrescarCarreraActual() {
  if (!carreraId || refrescando) return;
  const id = carreraId;
  refrescando = true;
  try {
    const carrera = await llamarApi(`/carreras/${id}`);
    // Mientras esperábamos, la carrera pudo finalizarse o cambiar el usuario.
    if (carreraId !== id) return;
    if (sinConexion) {
      sinConexion = false;
      mostrarMensaje("");
    }
    actualizarPanel(carrera);
    if (!carrera.en_curso) {
      resetearControlesTrasFinalizar();
      await cargarHistorial();
    }
  } catch (error) {
    if (carreraId !== id) return;
    sinConexion = true;
    mostrarMensaje(`Sin conexión con la carrera, reintentando: ${error.message}`);
  } finally {
    refrescando = false;
  }
}

function resetearControlesTrasFinalizar() {
  activarControles(false);
  clearInterval(intervalo);
  carreraId = null;
}

function mostrarResumenPorConductor(carreras) {
  const totales = new Map();
  let totalGeneral = 0;

  carreras.forEach((carrera) => {
    const conductor = carrera.usuario || "Desconocido";
    totales.set(conductor, (totales.get(conductor) || 0) + carrera.importe_en_vivo);
    totalGeneral += carrera.importe_en_vivo;
  });

  listaResumenConductoresEl.innerHTML = "";
  totales.forEach((total, conductor) => {
    const item = document.createElement("li");
    item.innerHTML = `<span></span><span>${total.toFixed(2)} €</span>`;
    item.firstElementChild.textContent = conductor;
    listaResumenConductoresEl.appendChild(item);
  });
  totalGeneralEl.textContent = `${totalGeneral.toFixed(2)} €`;
  resumenConductoresEl.hidden = totales.size < 2;
}

async function cargarHistorial() {
  try {
    const carreras = await llamarApi("/carreras");
    historialBody.innerHTML = "";
    carreras.forEach((carrera) => {
      const fila = document.createElement("tr");
      fila.innerHTML = `
        <td>${carrera.id}</td>
        <td></td>
        <td>${carrera.en_curso ? "En curso" : "Finalizada"}</td>
        <td>${carrera.importe_en_vivo.toFixed(2)} €</td>
      `;
      fila.children[1].textContent = carrera.usuario || "—";
      historialBody.appendChild(fila);
    });
    mostrarResumenPorConductor(carreras);

    const activa = carreras.find((carrera) => carrera.en_curso && carrera.usuario === nombreUsuario);
    if (activa && !carreraId) seguirCarrera(activa);
  } catch (error) {
    mostrarMensaje(`No se pudo cargar el historial: ${error.message}`);
  }
}

btnIniciar.addEventListener("click", iniciarCarrera);
btnParado.addEventListener("click", () => cambiarEstado("parado"));
btnMovimiento.addEventListener("click", () => cambiarEstado("movimiento"));
btnFinalizar.addEventListener("click", finalizarCarrera);

btnMostrarRegistro.addEventListener("click", () => {
  formRegistro.hidden = !formRegistro.hidden;
});

formLogin.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  mensajeLoginEl.textContent = "";
  const username = document.getElementById("input-usuario").value.trim();
  const btnLogin = document.getElementById("btn-login");
  btnLogin.disabled = true;
  btnLogin.textContent = "Entrando…";
  try {
    const { token: nuevoToken, rol } = await llamarApi("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username,
        password: document.getElementById("input-password").value,
      }),
    });
    guardarSesion(nuevoToken, username, rol);
    mostrarTaximetro();
  } catch (error) {
    mensajeLoginEl.textContent = error.message;
  } finally {
    btnLogin.disabled = false;
    btnLogin.textContent = "Entrar";
  }
});

formRegistro.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  mensajeLoginEl.textContent = "";
  const username = document.getElementById("input-registro-usuario").value.trim();
  const password = document.getElementById("input-registro-password").value;
  const btnRegistro = document.getElementById("btn-registro");
  btnRegistro.disabled = true;
  try {
    await llamarApi("/auth/registro", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    const { token: nuevoToken, rol } = await llamarApi("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    guardarSesion(nuevoToken, username, rol);
    mostrarTaximetro();
  } catch (error) {
    mensajeLoginEl.textContent = error.message;
  } finally {
    btnRegistro.disabled = false;
  }
});

btnLogout.addEventListener("click", async () => {
  // La carrera se cobra en el servidor: cerrar sesión no la detiene.
  const finalizar =
    carreraId &&
    confirm(
      "Tienes una carrera en curso y seguirá contando aunque cierres sesión.\n\n" +
        "Aceptar: finalizarla ahora.\nCancelar: dejarla en marcha.",
    );
  if (finalizar) {
    await finalizarCarrera();
    if (carreraId) return;
  }
  limpiarSesion();
  mostrarLogin();
});

formTarifas.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  mensajeTarifasEl.textContent = "";
  try {
    await llamarApi("/tarifas", {
      method: "PATCH",
      body: JSON.stringify({
        tarifa_parado: Number(inputTarifaParado.value),
        tarifa_movimiento: Number(inputTarifaMovimiento.value),
      }),
    });
    mensajeTarifasEl.textContent = "Tarifas actualizadas.";
  } catch (error) {
    mensajeTarifasEl.textContent = `No se pudieron guardar: ${error.message}`;
  }
});

const avisoServidorEl = document.getElementById("aviso-servidor");
const avisoServidorTextoEl = document.getElementById("aviso-servidor-texto");

// El backend (Render, plan gratuito) se duerme tras un rato sin uso y tarda
// unos segundos en arrancar: avisamos y esperamos a que /health responda.
async function esperarServidor() {
  if (!avisoServidorEl) return;
  const inicio = Date.now();
  while (Date.now() - inicio < 120000) {
    try {
      const respuesta = await fetch(`${API_BASE}/health`, { cache: "no-store" });
      if (respuesta.ok) {
        avisoServidorEl.classList.add("listo");
        avisoServidorTextoEl.textContent = "Servidor listo.";
        setTimeout(() => avisoServidorEl.classList.add("oculto"), 1500);
        setTimeout(() => (avisoServidorEl.hidden = true), 2000);
        return;
      }
    } catch {}
    await new Promise((resolver) => setTimeout(resolver, 3000));
  }
  avisoServidorTextoEl.textContent = "El servidor no responde. Recarga la página en unos segundos.";
}

esperarServidor();

const pieAnioEl = document.getElementById("pie-anio");
if (pieAnioEl) pieAnioEl.textContent = new Date().getFullYear();

if (token) {
  mostrarTaximetro();
} else {
  mostrarLogin();
}
