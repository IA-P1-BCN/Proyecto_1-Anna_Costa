# Guía de despliegue — Render + Neon + Vercel

Este documento explica cómo desplegar la API (`backend/`) en **Render**, la base
de datos en **Neon** y el frontend estático (`frontend/`) en **Vercel**.

## 1. Base de datos — Neon

1. Crea una cuenta/proyecto en [neon.tech](https://neon.tech).
2. En el dashboard del proyecto, copia el **Connection string** (formato
   `postgresql://usuario:password@host/dbname?sslmode=require`).
3. Guarda ese valor, lo necesitarás como `DATABASE_URL` en Render.

No hace falta crear tablas a mano: la API las crea automáticamente al
arrancar (`Base.metadata.create_all`).

## 2. Backend — Render

1. En [render.com](https://render.com), **New > Web Service**, conecta este
   repositorio.
2. Si Render detecta el `render.yaml` de la raíz, usará esta configuración
   automáticamente (Blueprint). Si prefieres configurarlo a mano:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Añade las variables de entorno del servicio:
   - `DATABASE_URL`: la cadena de conexión de Neon.
   - `ALLOWED_ORIGINS`: de momento puedes poner `*`; luego lo restringes al
     dominio de Vercel (paso 4).
4. Despliega. Comprueba que funciona visitando `https://<tu-servicio>.onrender.com/health`
   (debe devolver `{"status": "ok"}`) y la documentación interactiva en
   `https://<tu-servicio>.onrender.com/docs`.

## 3. Frontend — Vercel

1. En [vercel.com](https://vercel.com), **Add New > Project**, importa este
   repositorio.
2. En la configuración del proyecto, fija **Root Directory** = `frontend`.
   Es un sitio estático: no necesita build command ni framework preset.
3. Antes de desplegar (o justo después, y vuelves a desplegar), edita
   [`frontend/config.js`](frontend/config.js) y sustituye `API_BASE` por la
   URL real de tu servicio en Render:

   ```js
   const API_BASE = "https://<tu-servicio>.onrender.com";
   ```

4. Despliega. Vercel te dará una URL tipo `https://tu-proyecto.vercel.app`.

## 4. Cerrar el círculo — CORS

Vuelve a Render y actualiza la variable `ALLOWED_ORIGINS` del backend con la
URL final de Vercel (puedes poner varias separadas por comas):

```
ALLOWED_ORIGINS=https://tu-proyecto.vercel.app
```

Guarda y deja que Render redespliegue el servicio.

## 5. Probar en local (opcional, antes de desplegar)

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # y edita DATABASE_URL con tu Neon
export $(cat .env | xargs)  # en Windows usa `set` o un gestor de .env
uvicorn main:app --reload
```

Frontend: abre `frontend/index.html` con la extensión "Live Server" de VSCode
(o cualquier servidor estático), con `API_BASE` apuntando a
`http://localhost:8000`.
