"""Esquemas Pydantic de entrada/salida de la API."""

import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class CambioEstado(BaseModel):
    estado: Literal["parado", "movimiento"]


class CarreraOut(BaseModel):
    id: int
    estado: str
    importe_acumulado: float
    importe_en_vivo: float = 0.0
    en_curso: bool
    inicio: datetime.datetime
    fin: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
