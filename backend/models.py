"""Modelos de datos persistidos en Neon."""

import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from database import Base


class Carrera(Base):
    __tablename__ = "carreras"

    id = Column(Integer, primary_key=True, index=True)
    estado = Column(String, nullable=False, default="parado")
    importe_acumulado = Column(Float, nullable=False, default=0.0)
    en_curso = Column(Boolean, nullable=False, default=True)
    inicio = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    fin = Column(DateTime, nullable=True)
    ultimo_cambio = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
