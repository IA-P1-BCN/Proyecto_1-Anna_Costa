import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class CambioEstado(BaseModel):
    estado: Literal["parado", "movimiento"]


class CarreraOut(BaseModel):
    id: int
    usuario: Optional[str] = None
    estado: str
    importe_acumulado: float
    importe_en_vivo: float = 0.0
    en_curso: bool
    inicio: datetime.datetime
    fin: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RegistroUsuario(BaseModel):
    username: str
    password: str


class LoginUsuario(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    token: str
    username: str
    rol: str


class TarifasOut(BaseModel):
    tarifa_parado: float
    tarifa_movimiento: float


class TarifasUpdate(BaseModel):
    tarifa_parado: float
    tarifa_movimiento: float
