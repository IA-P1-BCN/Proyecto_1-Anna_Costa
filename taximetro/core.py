import time

ESTADO_PARADO = "parado"
ESTADO_MOVIMIENTO = "movimiento"

ESTADOS_VALIDOS = {ESTADO_PARADO, ESTADO_MOVIMIENTO}

TARIFA_PARADO_DEFECTO = 0.02  # €/segundo
TARIFA_MOVIMIENTO_DEFECTO = 0.05  # €/segundo


class EstadoInvalidoError(ValueError):
    pass


class CarreraNoIniciadaError(RuntimeError):
    pass


class CarreraEnCursoError(RuntimeError):
    pass


class Taximetro:
    """Gestiona el estado y el cálculo de tarifa de una única carrera."""

    def __init__(
        self,
        tarifa_parado=TARIFA_PARADO_DEFECTO,
        tarifa_movimiento=TARIFA_MOVIMIENTO_DEFECTO,
        reloj=time.time,
    ):
        self.tarifa_parado = tarifa_parado
        self.tarifa_movimiento = tarifa_movimiento
        self._reloj = reloj

        self.estado = None
        self.importe_acumulado = 0.0
        self.instante_inicio = None
        self.instante_ultimo_cambio = None
        self.en_curso = False

    def _tarifa_actual(self):
        return self.tarifa_parado if self.estado == ESTADO_PARADO else self.tarifa_movimiento

    def _acumular_hasta_ahora(self):
        ahora = self._reloj()
        segundos_transcurridos = ahora - self.instante_ultimo_cambio
        self.importe_acumulado += segundos_transcurridos * self._tarifa_actual()
        self.instante_ultimo_cambio = ahora

    def iniciar_carrera(self):
        if self.en_curso:
            raise CarreraEnCursoError("Ya hay una carrera en curso.")
        ahora = self._reloj()
        self.estado = ESTADO_PARADO
        self.importe_acumulado = 0.0
        self.instante_inicio = ahora
        self.instante_ultimo_cambio = ahora
        self.en_curso = True

    def cambiar_estado(self, nuevo_estado):
        if nuevo_estado not in ESTADOS_VALIDOS:
            raise EstadoInvalidoError(f"Estado desconocido: {nuevo_estado!r}")
        if not self.en_curso:
            raise CarreraNoIniciadaError("No hay ninguna carrera en curso.")
        if nuevo_estado == self.estado:
            return False
        self._acumular_hasta_ahora()
        self.estado = nuevo_estado
        return True

    def cambiar_tarifas(self, tarifa_parado, tarifa_movimiento):
        # Lo ya recorrido se cobra con la tarifa anterior.
        if self.en_curso:
            self._acumular_hasta_ahora()
        self.tarifa_parado = tarifa_parado
        self.tarifa_movimiento = tarifa_movimiento

    def importe_actual(self):
        if not self.en_curso:
            return self.importe_acumulado
        ahora = self._reloj()
        segundos_transcurridos = ahora - self.instante_ultimo_cambio
        return self.importe_acumulado + segundos_transcurridos * self._tarifa_actual()

    def duracion_actual(self):
        if not self.en_curso:
            return 0.0
        return self._reloj() - self.instante_inicio

    def finalizar_carrera(self):
        if not self.en_curso:
            raise CarreraNoIniciadaError("No hay ninguna carrera en curso.")
        self._acumular_hasta_ahora()
        self.en_curso = False
        resumen = {
            "instante_inicio": self.instante_inicio,
            "instante_fin": self.instante_ultimo_cambio,
            "duracion_segundos": self.instante_ultimo_cambio - self.instante_inicio,
            "importe_total": round(self.importe_acumulado, 2),
        }
        return resumen
