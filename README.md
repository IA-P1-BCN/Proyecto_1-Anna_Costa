<img width="11520" height="3456" alt="Copia de Banner notebooks" src="https://github.com/user-attachments/assets/1c187a02-2294-4f4b-ba84-63766c051a15" />

# 🚕 TaxiTech Solutions — Sistema de Taxímetro Digital

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Estado](https://img.shields.io/badge/Estado-Desplegado-brightgreen)
![Sprint](https://img.shields.io/badge/Sprint-1-orange)
![Prioridad](https://img.shields.io/badge/Prioridad-Alta-red)

</div>

---

> **Proyecto:** `TTX-247` — Modernización del sistema de facturación en flota

> **Cliente:** TaxiTech Solutions S.L. *(empresa de gestión de flotas de taxi, Madrid)*

> **Equipo asignado:** Backend Squad — Nuevas incorporaciones

> **Deadline:** Una semana a partir de la fecha de inicio del proyecto.

---

## 🔗 Demo en vivo

- **App:** [taxy-py.vercel.app](https://taxy-py.vercel.app/)
- **API:** [taximetro-api.onrender.com/health](https://taximetro-api.onrender.com/health)

El backend está en el plan gratuito de Render: si lleva un rato sin uso, la
primera petición puede tardar unos segundos en "despertar" (cold start).
Un workflow (`.github/workflows/keep-alive.yml`) le hace ping de 08:00 a
24:00 para mantenerlo despierto; fuera de ese horario, ábrela un par de
minutos antes de una demo en directo.

---

## 📩 Contexto del Encargo

El equipo de operaciones de **TaxiTech Solutions** lleva desde 2018 usando taxímetros físicos de la marca Hale modelo T200. El fabricante dejó de dar soporte en 2023 y los dispositivos están empezando a fallar en flota.

La dirección ha tomado la decisión de **migrar a un sistema 100% software** antes de Q3 2025. El CTO ha abierto este proyecto piloto para validar el concepto con un **prototipo funcional** antes de comprometer presupuesto con un proveedor externo.

Tu equipo ha sido asignado para desarrollar el prototipo.

---

## 🗣️ Briefing del Cliente

> *"Necesitamos algo que los taxistas puedan arrancar al inicio del turno y que calcule lo que le cuesta al pasajero en tiempo real. Cuando el taxi está parado en un semáforo, el contador sigue corriendo pero más despacio. En marcha, corre más rápido. Al llegar al destino, el taxista pulsa un botón, sale el total, y listo. Nos gustaría también poder ver un histórico de carreras del día. Si puede tener contraseña para que no lo toquen los pasajeros, mejor. Y si en el futuro se puede ver desde el móvil o una tablet en el taxi, perfecto."*
> — Director de Operaciones, TaxiTech Solutions

**Tarifas vigentes (Zona EMT Madrid, junio 2025):**
- Taxi **parado o velocidad < 20 km/h**: `0.02 €/segundo`
- Taxi **en movimiento**: `0.05 €/segundo`

---

## 📋 Historias de Usuario

El equipo de producto ha desglosado el briefing en las siguientes historias. Están priorizadas por el cliente usando MoSCoW.

| ID | Historia | Prioridad |
|----|----------|-----------|
| US-01 | Como taxista, quiero iniciar una carrera con un solo comando para empezar a cobrar desde el momento de arranque | Must |
| US-02 | Como taxista, quiero cambiar el estado entre "parado" y "en movimiento" para que la tarifa se ajuste | Must |
| US-03 | Como taxista, quiero finalizar la carrera y ver el total en euros para cobrar al pasajero | Must |
| US-04 | Como taxista, quiero poder iniciar otra carrera sin cerrar el programa para no perder tiempo entre servicios | Must |
| US-05 | Como responsable de flota, quiero ver el histórico de carreras del día para cuadrar caja | Should |
| US-06 | Como técnico, quiero que el sistema genere logs de operación para diagnosticar errores en producción | Should |
| US-07 | Como técnico, quiero poder cambiar las tarifas en un fichero de configuración sin redeployar | Should |
| US-08 | Como responsable de flota, quiero que el sistema requiera contraseña para protegerlo de manipulaciones | Could |
| US-09 | Como taxista, quiero una interfaz visual con botones grandes para usarlo fácilmente con el móvil o tablet | Could |

---

## 📊 Fases de Entrega

El proyecto se divide en **4 fases incrementales**. Cada fase es un entregable autónomo y funcional.

---

### 🟢 Fase 1 — MVP Funcional (US-01 a US-04)

El primer entregable es un CLI operativo que cubra el flujo completo de una carrera. El cliente necesita validar la lógica de tarifas antes de avanzar con cualquier otra funcionalidad.

El sistema debe arrancar desde terminal, presentar las instrucciones de uso, y permitir al conductor gestionar el estado del vehículo mediante comandos de teclado. La tarifa se acumula de forma continua en función del estado activo y el tiempo transcurrido. Al finalizar la carrera, el importe total se muestra en euros con dos decimales. El proceso no debe cerrarse entre carreras: el conductor necesita encadenar servicios sin interrupciones.

**Requisitos funcionales:**

- Al arrancar, el sistema debe explicar al conductor cómo usarlo sin necesidad de documentación externa
- El conductor debe poder indicar en cada momento si el vehículo está parado o en movimiento
- El importe se acumula de forma continua según el estado activo y el tiempo transcurrido, aplicando la tarifa correspondiente en cada tramo
- Al cerrar la carrera, el sistema muestra el importe total a cobrar
- El sistema debe permitir encadenar carreras de forma inmediata, sin interrupciones entre servicios

---

### 🟡 Fase 2 — Observabilidad y Persistencia (US-05, US-06, US-07)

El cliente ha solicitado que el sistema sea auditable y que los datos sobrevivan al cierre de la aplicación. Esta fase añade trazabilidad operativa y persistencia de negocio.

El sistema debe registrar todos los eventos relevantes —arranque, cambios de estado, cierre de carrera, errores— en un log estructurado accesible para el equipo técnico. El historial de carreras debe escribirse en disco de forma incremental y estar disponible en la siguiente sesión sin intervención manual. Las tarifas deben poder modificarse mediante un fichero de configuración externo, sin necesidad de tocar el código ni redeployar.

**Requisitos funcionales:**

- El sistema debe registrar en todo momento qué está ocurriendo: arranque, cambios de estado del vehículo, cierre de carrera y cualquier error. Ese registro debe ser accesible para el equipo técnico sin necesidad de intervenir en el proceso en ejecución
- Al finalizar cada carrera, los datos relevantes —fecha, duración e importe— deben quedar guardados de forma permanente y estar disponibles en sesiones posteriores sin ninguna acción manual
- Las tarifas deben poder actualizarse sin modificar el código ni redeployar la aplicación
- La lógica de cálculo de tarifas debe estar cubierta por tests automatizados

---

### 🟠 Fase 3 — Arquitectura y Experiencia de Usuario (US-08, US-09)

Con el MVP validado, el cliente quiere una versión del sistema que pueda mantenerse a largo plazo y que resulte usable para conductores con poca experiencia técnica. Esta fase implica una refactorización estructural y la incorporación de una interfaz gráfica.

El código debe reorganizarse bajo un modelo orientado a objetos con responsabilidades claramente delimitadas entre componentes. El acceso al sistema debe protegerse mediante autenticación por contraseña, almacenada de forma segura. La interfaz gráfica debe ser funcional en una tablet montada en el vehículo: botones grandes, estado visible de un vistazo y contador actualizado en tiempo real sin que la interfaz se bloquee.

**Requisitos funcionales:**

- El código debe estar organizado de forma que cada componente tenga una responsabilidad clara y pueda modificarse o sustituirse sin afectar al resto del sistema
- El acceso a la aplicación debe estar protegido por contraseña. Las credenciales deben almacenarse de forma segura: ningún valor sensible puede guardarse en texto plano
- La interfaz gráfica debe ser funcional en una tablet montada en el vehículo: estado del taxi visible de un vistazo, importe actualizado en tiempo real e interacción táctil cómoda. La interfaz no debe bloquearse en ningún momento durante el uso

---

### 🔴 Fase 4 — Versión de Producción

Esta fase convierte el prototipo en un sistema desplegable. El cliente quiere poder instalar la aplicación en los vehículos de la flota sin dependencias manuales, y acceder al historial de operaciones desde cualquier dispositivo conectado a la red del taxi.

El historial migra de fichero plano a base de datos relacional. La lógica de negocio se expone mediante una API REST que puede ser consumida tanto por la interfaz web incluida como por integraciones futuras. El sistema completo debe poder desplegarse con un único comando.

**Requisitos funcionales:**

- El historial de carreras debe almacenarse en una base de datos que garantice integridad y permita consultas estructuradas
- La lógica de negocio debe exponerse a través de una API que permita iniciar carreras, cambiar su estado, finalizarlas y consultar el historial. Esta API debe poder ser consumida por cualquier cliente web o móvil en el futuro
- El sistema debe incluir un panel web accesible desde el navegador para que el responsable de flota pueda consultar el historial sin instalar nada
- El despliegue debe poder realizarse con un único comando, sin configuración manual del entorno. Los datos deben sobrevivir a reinicios del sistema

---

## ✅ Estado actual del proyecto

Las cuatro fases están implementadas sobre el mismo paquete `taximetro/`,
reutilizando la lógica de negocio entre el CLI y la API:

| Fase | Historias | Estado | Dónde está |
| --- | --- | --- | --- |
| 1 — MVP funcional | US-01 a US-04 | ✅ | [`taximetro/core.py`](taximetro/core.py), [`taximetro/cli.py`](taximetro/cli.py) |
| 2 — Observabilidad y persistencia | US-05, US-06, US-07 | ✅ | [`taximetro/logger.py`](taximetro/logger.py), [`taximetro/storage.py`](taximetro/storage.py), [`taximetro/config.py`](taximetro/config.py) |
| 3 — Arquitectura y UX | US-08, US-09 | ✅ | [`taximetro/auth.py`](taximetro/auth.py), [`web/`](web/) |
| 4 — Producción | — | ✅ | [`taximetro/api.py`](taximetro/api.py) (API REST + BD SQLite + web servida) |

## 🌐 Arquitectura de despliegue (Render + Vercel)

El repositorio contiene **dos implementaciones** del mismo taxímetro:

- [`taximetro/`](taximetro/) + [`web/`](web/): la referencia usada para desarrollar y probar
  las 4 fases (Flask + SQLite, 64 tests, Docker). Pensada para self-host
  (`docker compose up`) o para correr en local.
- [`backend/`](backend/) + [`frontend/`](frontend/): lo que se **despliega de verdad**, en la
  cuenta personal (`costanna`), no en el repositorio de la organización:
  - `backend/` — FastAPI + Postgres (Neon), desplegado en **Render**
    (`render.yaml`, `rootDir: backend`).
  - `frontend/` — HTML/JS estático, desplegado en **Vercel**, apuntando a
    la URL de Render (`frontend/config.js`).

Ambas implementaciones cubren las mismas historias de usuario: auth con
contraseña hasheada, roles (**responsable de flota** ve el historial de
todos los conductores con el total de cada uno y el total general;
**taxista** solo el suyo — el primer usuario que se registra en cada
instalación es automáticamente el responsable), tarifas cambiables en
caliente desde un panel en la propia web (sin redeploy: `backend/` las
guarda en la base de datos y `taximetro/` las escribe en `config.json`)
y logging estructurado. El historial muestra inicio, duración e importe
de cada carrera y lo recaudado hoy. 104 tests automatizados en total
(64 en `tests/` + 40 en `backend/tests/`).

`SECRET_KEY` se configura como variable de entorno en Render (ver
`backend/.env.example`) — conviene fijarlo explícitamente (con
`generateValue: true` en `render.yaml` si se usa Blueprint) para que los
tokens no caduquen en cada reinicio del servicio.

**Al hacer `git push`, el remoto es `origin` (`github.com/costanna/...`).**
El remoto `upstream` (`Factoria-F5-madrid/project-py-taximetro`) es solo
de referencia del enunciado y no debe recibir pushes de este trabajo.

Notas de alcance del prototipo:

- La API Flask modela **un taxi por instancia** (un `Taximetro` en memoria
  por proceso), suficiente para validar el concepto; escalar a flota implica
  un `Taximetro` por vehículo/sesión, no un cambio de arquitectura. Mientras
  hay una carrera en curso no se puede iniciar otra, y solo su conductor o
  el responsable de flota pueden cambiarla de estado o finalizarla. El
  backend desplegado sí lleva una carrera por conductor.
- El historial usa **SQLite** (cumple "base de datos que garantiza
  integridad y permite consultas estructuradas" sin añadir infraestructura
  para un prototipo de este tamaño); migrar a Postgres es cambiar una
  cadena de conexión si el volumen lo pidiera.
- Los tokens de sesión se firman con una clave por proceso
  (`TAXIMETRO_SECRET_KEY` opcional) y caducan a las 8h (un turno).

## 🚀 Puesta en marcha

### Con Docker (un único comando, sin configurar el entorno)

```bash
docker compose up --build          # o: make docker-up
```

Abre `http://localhost:5000`. El historial y los usuarios se guardan en
volúmenes (`taximetro_data`, `taximetro_logs`) que sobreviven a reinicios
del contenedor. Las tarifas viven en `config.json`, montado desde esta
carpeta: se pueden cambiar desde el panel web o editando el fichero y
reiniciando el contenedor. El contenedor sirve la aplicación con gunicorn.

### En local (desarrollo)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
make install                       # o: pip install -r requirements-dev.txt
make precommit-install              # activa los hooks de lint/format en cada commit
```

`requirements.txt` tiene solo las dependencias de producción (las que usa
la imagen Docker); `requirements-dev.txt` añade encima pytest, requests,
black, flake8, isort y pre-commit para desarrollar.

**CLI (Fase 1), pide usuario/contraseña la primera vez que se ejecuta:**

```bash
python taximeter.py
```

**API + interfaz web (Fase 3/4)** — abre `http://localhost:5000`:

```bash
make run-api                        # o: python run_api.py
```

La primera vez, da de alta el usuario responsable de flota desde la propia
web (pantalla de login) o con:

```bash
curl -X POST http://localhost:5000/api/auth/registro \
     -H "Content-Type: application/json" \
     -d '{"username": "responsable", "password": "cambia-esto"}'
```

**Backend FastAPI + frontend (lo que corre en Render/Vercel), en local:**

```bash
cd backend
pip install -r requirements-dev.txt
cp .env.example .env                # rellena DATABASE_URL (Neon) y SECRET_KEY
uvicorn main:app --reload           # http://localhost:8000

# en otra terminal: sirve frontend/ con cualquier servidor estático
# y ajusta API_BASE en frontend/config.js a http://localhost:8000
```

**Tests (unitarios, integración y end-to-end):**

```bash
make test                           # o: pytest -v          (taximetro/)
pytest backend/tests -v             #                        (backend/)
```

**Lint y formato:**

```bash
make lint                           # comprueba
make format                         # corrige
```

El pipeline de CI (`.github/workflows/ci.yml`) ejecuta lint + toda la
suite de tests en cada push y PR a `main`, en Python 3.11 y 3.12, y
comprueba que `docker compose up` levanta la web.

> **Windows:** el código usa emoji en los mensajes de consola. Si
> `flake8`/`black` avisan de un error de codificación al leer algún
> fichero, activa el modo UTF-8 de Python una vez por sesión:
> `set PYTHONUTF8=1` (CMD) o `$env:PYTHONUTF8=1` (PowerShell). En Linux/Mac
> no hace falta. `make` no viene instalado en Windows por defecto: usa los
> comandos `python -m ...` equivalentes que aparecen arriba, o instala
> `make` con Chocolatey/Scoop/WSL si prefieres los atajos del Makefile.

Cómo trabaja el equipo (ramas, commits, PRs, Definition of Done) está en
[CONTRIBUTING.md](CONTRIBUTING.md).

---

## 🛠️ Restricciones Técnicas

El lenguaje de desarrollo es **Python**. Más allá de eso, la elección de librerías, frameworks y herramientas queda en manos del equipo, que deberá justificar sus decisiones técnicas en la documentación del proyecto.

Se requiere control de versiones con **Git y GitHub** desde el inicio. La gestión de tareas debe ser visible en un tablero **GitHub Projects** con una columna por fase.

---

## 📦 Entregables por Fase

Cada fase debe entregarse con:

1. Repositorio de GitHub con el código fuente del proyecto
2. Demo en directo
3. Enlace al tablero Kanban actualizado

---

## 📚 Recursos

### Documentación oficial de Python
- [`time` — Python stdlib](https://docs.python.org/3/library/time.html)
- [`logging` — Python stdlib](https://docs.python.org/3/library/logging.html)
- [`unittest` — Python stdlib](https://docs.python.org/3/library/unittest.html)
- [`tkinter` — GUI básica](https://docs.python.org/3/library/tkinter.html)

### Guías de referencia
- [Real Python — OOP en Python](https://realpython.com/python3-object-oriented-programming/)
- [Real Python — Testing](https://realpython.com/pytest-python-testing/)
- [Real Python — Logging](https://realpython.com/python-logging/)
- [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/) — formato de mensajes de commit

### Solución
[Solución proyecto](https://github.com/Factoria-F5-madrid/stn-taximetro)
