import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from database import Base


def ahora_utc() -> datetime.datetime:
    # Las columnas DateTime no guardan zona horaria: UTC sin tzinfo.
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class Carrera(Base):
    __tablename__ = "carreras"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String, nullable=True, index=True)
    estado = Column(String, nullable=False, default="parado")
    importe_acumulado = Column(Float, nullable=False, default=0.0)
    en_curso = Column(Boolean, nullable=False, default=True)
    inicio = Column(DateTime, nullable=False, default=ahora_utc)
    fin = Column(DateTime, nullable=True)
    ultimo_cambio = Column(DateTime, nullable=False, default=ahora_utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    rol = Column(String, nullable=False, default="taxista")


class Tarifas(Base):
    __tablename__ = "tarifas"

    id = Column(Integer, primary_key=True)
    tarifa_parado = Column(Float, nullable=False)
    tarifa_movimiento = Column(Float, nullable=False)
