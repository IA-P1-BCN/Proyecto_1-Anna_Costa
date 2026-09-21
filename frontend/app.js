const estadoEl = document.getElementById("estado");
const importeEl = document.getElementById("importe");
const mensajeEl = document.getElementById("mensaje");
const historialBody = document.getElementById("historial-body");

const btnIniciar = document.getElementById("btn-iniciar");
const btnParado = document.getElementById("btn-parado");
const btnMovimiento = document.getElementById("btn-movimiento");
const btnFinalizar = document.getElementById("btn-finalizar");

let carreraId = null;
let intervalo = null;

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

async function llamarApi(path, options) {
  const respuesta = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!respuesta.ok) {
    const detalle = await respuesta.json().catch(() => ({}));
    throw new Error(detalle.detail || `Error ${respuesta.status}`);
  }
  return respuesta.json();
}

async function iniciarCarrera() {
  try {
    mostrarMensaje("");
    const carrera = await llamarApi("/carreras", { method: "POST" });
    carreraId = carrera.id;
    actualizarPanel(carrera);
    activarControles(true);
    intervalo = setInterval(refrescarCarreraActual, 1000);
    await cargarHistorial();
  } catch (error) {
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
    activarControles(false);
    clearInterval(intervalo);
    carreraId = null;
    await cargarHistorial();
  } catch (error) {
    mostrarMensaje(`No se pudo finalizar la carrera: ${error.message}`);
  }
}

async function refrescarCarreraActual() {
  if (!carreraId) return;
  try {
    const carrera = await llamarApi(`/carreras/${carreraId}`);
    actualizarPanel(carrera);
  } catch (error) {
    clearInterval(intervalo);
    mostrarMensaje(`Se perdió la conexión con la carrera: ${error.message}`);
  }
}

async function cargarHistorial() {
  try {
    const carreras = await llamarApi("/carreras");
    historialBody.innerHTML = "";
    carreras.forEach((carrera) => {
      const fila = document.createElement("tr");
      fila.innerHTML = `
        <td>${carrera.id}</td>
        <td>${carrera.en_curso ? "En curso" : "Finalizada"}</td>
        <td>${carrera.importe_en_vivo.toFixed(2)} €</td>
      `;
      historialBody.appendChild(fila);
    });
  } catch (error) {
    mostrarMensaje(`No se pudo cargar el historial: ${error.message}`);
  }
}

btnIniciar.addEventListener("click", iniciarCarrera);
btnParado.addEventListener("click", () => cambiarEstado("parado"));
btnMovimiento.addEventListener("click", () => cambiarEstado("movimiento"));
btnFinalizar.addEventListener("click", finalizarCarrera);

cargarHistorial();
