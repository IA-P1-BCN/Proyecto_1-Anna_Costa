(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const bannerConexion = $("banner-conexion");
  const pantallaLogin = $("pantalla-login");
  const pantallaTaximetro = $("pantalla-taximetro");
  const formLogin = $("form-login");
  const botonLogin = $("boton-login");
  const botonLoginTexto = botonLogin.querySelector(".boton__texto");
  const botonLoginSpinner = botonLogin.querySelector(".spinner");
  const botonMostrarRegistro = $("boton-mostrar-registro");
  const formRegistro = $("form-registro");
  const errorLogin = $("error-login");
  const errorAccion = $("error-accion");
  const chipEstado = $("chip-estado");
  const botonLogout = $("boton-logout");
  const nombreUsuarioEl = $("nombre-usuario");
  const rolUsuarioEl = $("rol-usuario");
  const importeActual = $("importe-actual");
  const duracionActual = $("duracion-actual");
  const totalHoy = $("total-hoy");
  const listaHistorial = $("lista-historial");
  const resumenConductoresEl = $("resumen-conductores");
  const listaResumenConductoresEl = $("lista-resumen-conductores");
  const panelTarifasEl = $("panel-tarifas");
  const formTarifas = $("form-tarifas");
  const mensajeTarifasEl = $("mensaje-tarifas");
  const inputTarifaParado = $("input-tarifa-parado");
  const inputTarifaMovimiento = $("input-tarifa-movimiento");

  const botonIniciar = $("boton-iniciar");
  const botonParado = $("boton-parado");
  const botonMovimiento = $("boton-movimiento");
  const botonFinalizar = $("boton-finalizar");

  document.querySelectorAll(".boton-ver-clave").forEach((boton) => {
    const input = document.getElementById(boton.dataset.input);
    if (!input) return;
    boton.addEventListener("click", () => {
      const mostrar = input.type === "password";
      input.type = mostrar ? "text" : "password";
      boton.setAttribute("aria-pressed", String(mostrar));
      boton.setAttribute("aria-label", mostrar ? "Ocultar contraseña" : "Mostrar contraseña");
      boton.title = mostrar ? "Ocultar contraseña" : "Mostrar contraseña";
      boton.textContent = mostrar ? "Ocultar" : "Ver";
    });
  });

  let token = null;
  let nombreUsuario = null;
  let rolUsuario = null;
  let intervaloActualizacion = null;
  let fallosConsecutivos = 0;
  let errorAccionTimeout = null;
  let ultimoEstado = {
    en_curso: false,
    conductor: null,
    estado: null,
    importe_actual: 0,
    duracion_actual: 0,
  };

  const UMBRAL_FALLOS_PARA_AVISO = 3;

  class ErrorApi extends Error {
    constructor(mensaje, { status = null, esErrorRed = false } = {}) {
      super(mensaje);
      this.status = status;
      this.esErrorRed = esErrorRed;
    }
  }

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
    } catch {
    }
  }

  function limpiarSesion() {
    token = null;
    nombreUsuario = null;
    rolUsuario = null;
    try {
      sessionStorage.removeItem("taximetro_token");
      sessionStorage.removeItem("taximetro_usuario");
      sessionStorage.removeItem("taximetro_rol");
    } catch {
    }
  }

  async function llamarApi(ruta, opciones = {}) {
    let respuesta;
    try {
      respuesta = await fetch(ruta, {
        ...opciones,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(opciones.headers || {}),
        },
      });
    } catch {
      throw new ErrorApi("Sin conexión con el taxímetro.", { esErrorRed: true });
    }
    const cuerpo = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) {
      if (respuesta.status === 401) {
        limpiarSesion();
        mostrarLogin();
      }
      throw new ErrorApi(cuerpo.error || `Error ${respuesta.status}`, { status: respuesta.status });
    }
    return cuerpo;
  }

  function formatearDuracion(segundos) {
    const total = Math.max(0, Math.round(segundos));
    const mm = Math.floor(total / 60).toString().padStart(2, "0");
    const ss = (total % 60).toString().padStart(2, "0");
    return `${mm}:${ss}`;
  }

  function pulsarImporte() {
    importeActual.classList.remove("actualizado");
    void importeActual.offsetWidth;
    importeActual.classList.add("actualizado");
  }

  function actualizarEstadoUI(estado) {
    const {
      en_curso: enCurso,
      conductor = null,
      estado: estadoTaxi,
      importe_actual: importe,
      duracion_actual: duracion = 0,
    } = estado;
    ultimoEstado = {
      en_curso: enCurso,
      conductor,
      estado: estadoTaxi,
      importe_actual: importe,
      duracion_actual: duracion,
    };
    // La carrera de otro conductor solo puede tocarla el responsable de flota.
    const ajena =
      enCurso && conductor && conductor !== nombreUsuario && rolUsuario !== "responsable";

    const nuevoValor = Number(importe).toFixed(2);
    if (importeActual.textContent !== nuevoValor) {
      importeActual.textContent = nuevoValor;
      pulsarImporte();
    }

    duracionActual.hidden = !enCurso;
    if (enCurso) duracionActual.textContent = formatearDuracion(duracion);

    botonIniciar.disabled = enCurso;
    botonParado.disabled = !enCurso || ajena || estadoTaxi === "parado";
    botonMovimiento.disabled = !enCurso || ajena || estadoTaxi === "movimiento";
    botonFinalizar.disabled = !enCurso || ajena;

    if (enCurso && estadoTaxi) {
      chipEstado.hidden = false;
      chipEstado.textContent = estadoTaxi.toUpperCase();
      chipEstado.className = `chip chip--${estadoTaxi}`;
    } else {
      chipEstado.hidden = true;
    }
  }

  function mostrarBannerConexion(mensaje) {
    bannerConexion.textContent = mensaje;
    bannerConexion.hidden = false;
  }

  function ocultarBannerConexion() {
    bannerConexion.hidden = true;
  }

  function mostrarErrorAccion(mensaje) {
    errorAccion.textContent = mensaje;
    errorAccion.hidden = false;
    clearTimeout(errorAccionTimeout);
    errorAccionTimeout = setTimeout(() => {
      errorAccion.hidden = true;
    }, 4000);
  }

  function mostrarLogin() {
    detenerActualizacionEnVivo();
    pantallaTaximetro.hidden = true;
    pantallaLogin.hidden = false;
    chipEstado.hidden = true;
    botonLogout.hidden = true;
    if (nombreUsuarioEl) nombreUsuarioEl.textContent = "";
    if (rolUsuarioEl) rolUsuarioEl.textContent = "";
    ocultarBannerConexion();
  }

  async function cargarPanelTarifas() {
    if (rolUsuario !== "responsable") {
      panelTarifasEl.hidden = true;
      return;
    }
    panelTarifasEl.hidden = false;
    try {
      const tarifas = await llamarApi("/api/tarifas");
      inputTarifaParado.value = tarifas.tarifa_parado;
      inputTarifaMovimiento.value = tarifas.tarifa_movimiento;
    } catch (error) {
      mensajeTarifasEl.textContent = `No se pudieron cargar las tarifas: ${error.message}`;
    }
  }

  async function mostrarTaximetro() {
    pantallaLogin.hidden = true;
    pantallaTaximetro.hidden = false;
    botonLogout.hidden = false;
    if (rolUsuarioEl) {
      rolUsuarioEl.textContent = rolUsuario === "responsable" ? "responsable de flota" : "taxista";
    }
    if (nombreUsuarioEl) nombreUsuarioEl.textContent = nombreUsuario || "";
    await sincronizarEstadoActual();
    cargarHistorial();
    cargarPanelTarifas();
  }

  async function sincronizarEstadoActual() {
    pantallaTaximetro.setAttribute("aria-busy", "true");
    try {
      const datos = await llamarApi("/api/carreras/actual");
      fallosConsecutivos = 0;
      ocultarBannerConexion();
      actualizarEstadoUI(datos);
      if (datos.en_curso) iniciarActualizacionEnVivo();
    } catch (error) {
      if (error.esErrorRed) mostrarBannerConexion("No se pudo conectar con el taxímetro.");
    } finally {
      pantallaTaximetro.removeAttribute("aria-busy");
    }
  }

  function iniciarActualizacionEnVivo() {
    detenerActualizacionEnVivo();
    intervaloActualizacion = setInterval(async () => {
      try {
        const datos = await llamarApi("/api/carreras/actual");
        fallosConsecutivos = 0;
        ocultarBannerConexion();
        actualizarEstadoUI(datos);
        if (!datos.en_curso) detenerActualizacionEnVivo();
      } catch (error) {
        if (error.esErrorRed) {
          fallosConsecutivos += 1;
          if (fallosConsecutivos >= UMBRAL_FALLOS_PARA_AVISO) {
            mostrarBannerConexion("Sin conexión con el taxímetro. Reintentando…");
          }
        } else if (error.status !== 401) {
          detenerActualizacionEnVivo();
        }
      }
    }, 1000);
  }

  function detenerActualizacionEnVivo() {
    if (intervaloActualizacion) {
      clearInterval(intervaloActualizacion);
      intervaloActualizacion = null;
    }
  }

  function mostrarResumenPorConductor(carreras) {
    const totales = new Map();
    carreras.forEach((carrera) => {
      const conductor = carrera.usuario || "Desconocido";
      totales.set(conductor, (totales.get(conductor) || 0) + carrera.importe_total);
    });

    listaResumenConductoresEl.innerHTML = "";
    totales.forEach((total, conductor) => {
      const item = document.createElement("li");
      item.innerHTML = `<span></span><span>${total.toFixed(2)} €</span>`;
      item.firstElementChild.textContent = conductor;
      listaResumenConductoresEl.appendChild(item);
    });
    resumenConductoresEl.hidden = totales.size < 2;
  }

  async function cargarHistorial() {
    try {
      const { carreras, total_recaudado_hoy: totalHoyValor } = await llamarApi(
        "/api/carreras/historial?limite=10"
      );
      totalHoy.textContent = Number(totalHoyValor).toFixed(2);
      mostrarResumenPorConductor(carreras);
      listaHistorial.innerHTML = "";
      carreras.forEach((carrera) => {
        const item = document.createElement("li");
        const hora = new Date(carrera.fecha_fin).toLocaleTimeString("es-ES", {
          hour: "2-digit",
          minute: "2-digit",
        });
        item.innerHTML = `<span></span><span>${carrera.importe_total.toFixed(2)} €</span>`;
        item.firstElementChild.textContent = `${carrera.usuario || "—"} · ${hora}`;
        listaHistorial.appendChild(item);
      });
    } catch {
    }
  }

  async function manejarAccion(boton, accion) {
    boton.disabled = true;
    try {
      await accion();
    } catch (error) {
      mostrarErrorAccion(error.message || "No se ha podido completar la acción.");
      actualizarEstadoUI(ultimoEstado);
    }
  }

  formLogin.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    errorLogin.hidden = true;
    botonLogin.disabled = true;
    botonLoginSpinner.hidden = false;
    botonLoginTexto.textContent = "Entrando…";
    const username = $("input-usuario").value.trim();
    try {
      const { token: nuevoToken, rol } = await llamarApi("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          username,
          password: $("input-password").value,
        }),
      });
      guardarSesion(nuevoToken, username, rol);
      await mostrarTaximetro();
    } catch (error) {
      errorLogin.textContent = error.message;
      errorLogin.hidden = false;
    } finally {
      botonLogin.disabled = false;
      botonLoginSpinner.hidden = true;
      botonLoginTexto.textContent = "Entrar";
    }
  });

  botonMostrarRegistro.addEventListener("click", () => {
    formRegistro.hidden = !formRegistro.hidden;
  });

  formRegistro.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    errorLogin.hidden = true;
    const username = $("input-registro-usuario").value.trim();
    const password = $("input-registro-password").value;
    try {
      await llamarApi("/api/auth/registro", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      const { token: nuevoToken, rol } = await llamarApi("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      guardarSesion(nuevoToken, username, rol);
      await mostrarTaximetro();
    } catch (error) {
      errorLogin.textContent = error.message;
      errorLogin.hidden = false;
    }
  });

  botonLogout.addEventListener("click", () => {
    limpiarSesion();
    mostrarLogin();
  });

  formTarifas.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    mensajeTarifasEl.textContent = "";
    try {
      await llamarApi("/api/tarifas", {
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

  botonIniciar.addEventListener("click", () =>
    manejarAccion(botonIniciar, async () => {
      const datos = await llamarApi("/api/carreras/iniciar", { method: "POST" });
      actualizarEstadoUI(datos);
      iniciarActualizacionEnVivo();
    })
  );

  botonParado.addEventListener("click", () =>
    manejarAccion(botonParado, async () => {
      const datos = await llamarApi("/api/carreras/estado", {
        method: "POST",
        body: JSON.stringify({ estado: "parado" }),
      });
      actualizarEstadoUI(datos);
    })
  );

  botonMovimiento.addEventListener("click", () =>
    manejarAccion(botonMovimiento, async () => {
      const datos = await llamarApi("/api/carreras/estado", {
        method: "POST",
        body: JSON.stringify({ estado: "movimiento" }),
      });
      actualizarEstadoUI(datos);
    })
  );

  botonFinalizar.addEventListener("click", () =>
    manejarAccion(botonFinalizar, async () => {
      await llamarApi("/api/carreras/finalizar", { method: "POST" });
      detenerActualizacionEnVivo();
      actualizarEstadoUI({ en_curso: false, estado: null, importe_actual: 0, duracion_actual: 0 });
      cargarHistorial();
    })
  );

  window.addEventListener("offline", () => mostrarBannerConexion("Sin conexión a internet."));
  window.addEventListener("online", () => {
    fallosConsecutivos = 0;
    if (token) sincronizarEstadoActual();
    else ocultarBannerConexion();
  });

  const pieAnio = $("pie-anio");
  if (pieAnio) pieAnio.textContent = new Date().getFullYear();

  if (token) {
    mostrarTaximetro();
  } else {
    mostrarLogin();
  }
})();
