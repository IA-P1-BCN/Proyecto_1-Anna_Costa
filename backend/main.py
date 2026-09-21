"""
API REST del Taxímetro Digital — TaxiTech Solutions.

Expone la misma lógica de tarifas de `taximeter.py` (Fase 1), pero persistida
en base de datos (Neon Postgres) en lugar de en memoria, para poder ser
consumida por el frontend web y por futuras integraciones.

Tarifas vigentes (Zona EMT Madrid, junio 2025):
  - Parado o velocidad < 20 km/h: 0.02 €/segundo
  - En movimiento:                0.05 €/segundo
"""

import datetime
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Carrera
from schemas import CambioEstado, CarreraOut

TARIFA_PARADO = 0.02
TARIFA_MOVIMIENTO = 0.05

app = FastAPI(title="TaxiTech Solutions — Taxímetro API")

allowed_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


def _tarifa(estado: str) -> float:
    return TARIFA_PARADO if estado == "parado" else TARIFA_MOVIMIENTO


def _acumular_hasta_ahora(carrera: Carrera) -> None:
    ahora = datetime.datetime.utcnow()
    segundos_transcurridos = (ahora - carrera.ultimo_cambio).total_seconds()
    carrera.importe_acumulado += segundos_transcurridos * _tarifa(carrera.estado)
    carrera.ultimo_cambio = ahora


def _con_importe_en_vivo(carrera: Carrera) -> Carrera:
    if carrera.en_curso:
        ahora = datetime.datetime.utcnow()
        segundos_transcurridos = (ahora - carrera.ultimo_cambio).total_seconds()
        carrera.importe_en_vivo = round(
            carrera.importe_acumulado + segundos_transcurridos * _tarifa(carrera.estado), 2
        )
    else:
        carrera.importe_en_vivo = round(carrera.importe_acumulado, 2)
    return carrera


def _obtener_carrera_activa(carrera_id: int, db: Session) -> Carrera:
    carrera = db.get(Carrera, carrera_id)
    if carrera is None:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    if not carrera.en_curso:
        raise HTTPException(status_code=409, detail="La carrera ya ha finalizado")
    return carrera


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/carreras", response_model=CarreraOut, status_code=201)
def iniciar_carrera(db: Session = Depends(get_db)):
    ahora = datetime.datetime.utcnow()
    carrera = Carrera(
        estado="parado",
        importe_acumulado=0.0,
        en_curso=True,
        inicio=ahora,
        ultimo_cambio=ahora,
    )
    db.add(carrera)
    db.commit()
    db.refresh(carrera)
    return _con_importe_en_vivo(carrera)


@app.patch("/carreras/{carrera_id}/estado", response_model=CarreraOut)
def cambiar_estado(carrera_id: int, cambio: CambioEstado, db: Session = Depends(get_db)):
    carrera = _obtener_carrera_activa(carrera_id, db)
    if cambio.estado != carrera.estado:
        _acumular_hasta_ahora(carrera)
        carrera.estado = cambio.estado
        db.commit()
        db.refresh(carrera)
    return _con_importe_en_vivo(carrera)


@app.post("/carreras/{carrera_id}/finalizar", response_model=CarreraOut)
def finalizar_carrera(carrera_id: int, db: Session = Depends(get_db)):
    carrera = _obtener_carrera_activa(carrera_id, db)
    _acumular_hasta_ahora(carrera)
    carrera.en_curso = False
    carrera.fin = datetime.datetime.utcnow()
    db.commit()
    db.refresh(carrera)
    return _con_importe_en_vivo(carrera)


@app.get("/carreras", response_model=list[CarreraOut])
def listar_carreras(db: Session = Depends(get_db)):
    carreras = db.query(Carrera).order_by(Carrera.inicio.desc()).all()
    return [_con_importe_en_vivo(c) for c in carreras]


@app.get("/carreras/{carrera_id}", response_model=CarreraOut)
def obtener_carrera(carrera_id: int, db: Session = Depends(get_db)):
    carrera = db.get(Carrera, carrera_id)
    if carrera is None:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    return _con_importe_en_vivo(carrera)
