import os
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import auth
from config import cargar_tarifas
from database import Base, engine, get_db
from logger import get_logger
from models import Carrera, Tarifas, ahora_utc
from schemas import (
    CambioEstado,
    CarreraOut,
    LoginUsuario,
    RegistroUsuario,
    TarifasOut,
    TarifasUpdate,
    TokenOut,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Taximetro API arrancada.")
    yield


app = FastAPI(title="TaxiTech Solutions — Taxímetro API", lifespan=lifespan)

allowed_origins = [
    origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class Identidad:
    username: str
    rol: str


def _obtener_tarifas(db: Session) -> Tarifas:
    fila = db.query(Tarifas).order_by(Tarifas.id).first()
    if fila is None:
        semilla = cargar_tarifas()
        fila = Tarifas(
            tarifa_parado=semilla["tarifa_parado"],
            tarifa_movimiento=semilla["tarifa_movimiento"],
        )
        db.add(fila)
        db.commit()
        db.refresh(fila)
    return fila


def _tarifa(estado: str, tarifas: Tarifas) -> float:
    return tarifas.tarifa_parado if estado == "parado" else tarifas.tarifa_movimiento


def _acumular_hasta_ahora(carrera: Carrera, tarifas: Tarifas) -> None:
    ahora = ahora_utc()
    segundos_transcurridos = (ahora - carrera.ultimo_cambio).total_seconds()
    carrera.importe_acumulado += segundos_transcurridos * _tarifa(carrera.estado, tarifas)
    carrera.ultimo_cambio = ahora


def _con_importe_en_vivo(carrera: Carrera, tarifas: Tarifas) -> Carrera:
    if carrera.en_curso:
        ahora = ahora_utc()
        segundos_transcurridos = (ahora - carrera.ultimo_cambio).total_seconds()
        carrera.importe_en_vivo = round(
            carrera.importe_acumulado + segundos_transcurridos * _tarifa(carrera.estado, tarifas), 2
        )
    else:
        carrera.importe_en_vivo = round(carrera.importe_acumulado, 2)
    return carrera


def _obtener_carrera_propia(carrera_id: int, db: Session, identidad: Identidad) -> Carrera:
    carrera = db.get(Carrera, carrera_id)
    es_ajena = carrera is not None and carrera.usuario != identidad.username
    if carrera is None or (es_ajena and identidad.rol != "responsable"):
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    return carrera


def _obtener_carrera_activa(carrera_id: int, db: Session, identidad: Identidad) -> Carrera:
    carrera = _obtener_carrera_propia(carrera_id, db, identidad)
    if not carrera.en_curso:
        raise HTTPException(status_code=409, detail="La carrera ya ha finalizado")
    return carrera


def requiere_token(authorization: str = Header(default="")) -> Identidad:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta el token de autenticación.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        datos = auth.datos_del_token(token)
    except auth.TokenInvalidoError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return Identidad(username=datos["username"], rol=datos["rol"])


def requiere_responsable(identidad: Identidad = Depends(requiere_token)) -> Identidad:
    if identidad.rol != "responsable":
        raise HTTPException(
            status_code=403, detail="Solo el responsable de flota puede hacer esto."
        )
    return identidad


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/registro", status_code=201)
def registro(datos: RegistroUsuario, db: Session = Depends(get_db)):
    username = datos.username.strip()
    if not 3 <= len(username) <= 30:
        raise HTTPException(
            status_code=400, detail="El usuario debe tener entre 3 y 30 caracteres."
        )
    if len(datos.password) < 8:
        raise HTTPException(
            status_code=400, detail="La contraseña debe tener al menos 8 caracteres."
        )
    if auth.existe_usuario(db, username):
        raise HTTPException(status_code=409, detail="Ese usuario ya existe.")
    auth.crear_usuario(db, username, datos.password)
    return {"mensaje": "Usuario creado."}


@app.post("/auth/login", response_model=TokenOut)
def login(datos: LoginUsuario, db: Session = Depends(get_db)):
    try:
        usuario_db = auth.verificar_credenciales(db, datos.username, datos.password)
    except auth.CredencialesInvalidasError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {
        "token": auth.emitir_token(usuario_db.username, usuario_db.rol),
        "username": usuario_db.username,
        "rol": usuario_db.rol,
    }


@app.get("/tarifas", response_model=TarifasOut)
def ver_tarifas(db: Session = Depends(get_db), identidad: Identidad = Depends(requiere_token)):
    return _obtener_tarifas(db)


@app.patch("/tarifas", response_model=TarifasOut)
def actualizar_tarifas(
    datos: TarifasUpdate,
    db: Session = Depends(get_db),
    identidad: Identidad = Depends(requiere_responsable),
):
    if datos.tarifa_parado <= 0 or datos.tarifa_movimiento <= 0:
        raise HTTPException(status_code=400, detail="Las tarifas deben ser positivas.")
    fila = _obtener_tarifas(db)
    # Lo ya recorrido por las carreras en curso se cobra con la tarifa anterior.
    for carrera in db.query(Carrera).filter(Carrera.en_curso.is_(True)):
        _acumular_hasta_ahora(carrera, fila)
    fila.tarifa_parado = datos.tarifa_parado
    fila.tarifa_movimiento = datos.tarifa_movimiento
    db.commit()
    db.refresh(fila)
    logger.info(
        "[%s] Tarifas actualizadas: parado=%.3f movimiento=%.3f",
        identidad.username,
        fila.tarifa_parado,
        fila.tarifa_movimiento,
    )
    return fila


@app.post("/carreras", response_model=CarreraOut, status_code=201)
def iniciar_carrera(db: Session = Depends(get_db), identidad: Identidad = Depends(requiere_token)):
    activa = (
        db.query(Carrera)
        .filter(Carrera.usuario == identidad.username, Carrera.en_curso.is_(True))
        .first()
    )
    if activa is not None:
        raise HTTPException(status_code=409, detail="Ya tienes una carrera en curso.")
    ahora = ahora_utc()
    carrera = Carrera(
        usuario=identidad.username,
        estado="parado",
        importe_acumulado=0.0,
        en_curso=True,
        inicio=ahora,
        ultimo_cambio=ahora,
    )
    db.add(carrera)
    db.commit()
    db.refresh(carrera)
    logger.info("[%s] Carrera #%s iniciada.", identidad.username, carrera.id)
    return _con_importe_en_vivo(carrera, _obtener_tarifas(db))


@app.patch("/carreras/{carrera_id}/estado", response_model=CarreraOut)
def cambiar_estado(
    carrera_id: int,
    cambio: CambioEstado,
    db: Session = Depends(get_db),
    identidad: Identidad = Depends(requiere_token),
):
    carrera = _obtener_carrera_activa(carrera_id, db, identidad)
    tarifas = _obtener_tarifas(db)
    if cambio.estado != carrera.estado:
        _acumular_hasta_ahora(carrera, tarifas)
        carrera.estado = cambio.estado
        db.commit()
        db.refresh(carrera)
        logger.info("[%s] Carrera #%s -> %s", identidad.username, carrera_id, cambio.estado)
    return _con_importe_en_vivo(carrera, tarifas)


@app.post("/carreras/{carrera_id}/finalizar", response_model=CarreraOut)
def finalizar_carrera(
    carrera_id: int,
    db: Session = Depends(get_db),
    identidad: Identidad = Depends(requiere_token),
):
    carrera = _obtener_carrera_activa(carrera_id, db, identidad)
    tarifas = _obtener_tarifas(db)
    _acumular_hasta_ahora(carrera, tarifas)
    carrera.en_curso = False
    carrera.fin = ahora_utc()
    db.commit()
    db.refresh(carrera)
    logger.info(
        "[%s] Carrera #%s finalizada: %.2f €",
        identidad.username,
        carrera_id,
        carrera.importe_acumulado,
    )
    return _con_importe_en_vivo(carrera, tarifas)


@app.get("/carreras", response_model=list[CarreraOut])
def listar_carreras(db: Session = Depends(get_db), identidad: Identidad = Depends(requiere_token)):
    consulta = db.query(Carrera)
    if identidad.rol != "responsable":
        consulta = consulta.filter(Carrera.usuario == identidad.username)
    carreras = consulta.order_by(Carrera.inicio.desc()).all()
    tarifas = _obtener_tarifas(db)
    return [_con_importe_en_vivo(c, tarifas) for c in carreras]


@app.get("/carreras/{carrera_id}", response_model=CarreraOut)
def obtener_carrera(
    carrera_id: int,
    db: Session = Depends(get_db),
    identidad: Identidad = Depends(requiere_token),
):
    carrera = _obtener_carrera_propia(carrera_id, db, identidad)
    return _con_importe_en_vivo(carrera, _obtener_tarifas(db))
