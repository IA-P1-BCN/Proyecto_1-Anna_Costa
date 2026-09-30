import pytest

from taximetro.core import (
    ESTADO_MOVIMIENTO,
    ESTADO_PARADO,
    CarreraNoIniciadaError,
    EstadoInvalidoError,
    Taximetro,
)


def crear_taximetro(reloj_falso, tarifa_parado=0.02, tarifa_movimiento=0.05):
    return Taximetro(
        tarifa_parado=tarifa_parado, tarifa_movimiento=tarifa_movimiento, reloj=reloj_falso
    )


def test_iniciar_carrera_arranca_en_parado_e_importe_cero(reloj_falso):
    taximetro = crear_taximetro(reloj_falso)
    taximetro.iniciar_carrera()
    assert taximetro.estado == ESTADO_PARADO
    assert taximetro.en_curso is True
    assert taximetro.importe_actual() == 0.0


def test_tarifa_parado_se_acumula_con_el_tiempo(reloj_falso):
    taximetro = crear_taximetro(reloj_falso, tarifa_parado=0.02)
    taximetro.iniciar_carrera()
    reloj_falso.avanzar(10)
    assert taximetro.importe_actual() == pytest.approx(0.20)


def test_cambio_a_movimiento_aplica_nueva_tarifa(reloj_falso):
    taximetro = crear_taximetro(reloj_falso, tarifa_parado=0.02, tarifa_movimiento=0.05)
    taximetro.iniciar_carrera()
    reloj_falso.avanzar(5)
    taximetro.cambiar_estado(ESTADO_MOVIMIENTO)
    reloj_falso.avanzar(4)
    assert taximetro.importe_actual() == pytest.approx(0.30)


def test_cambiar_al_mismo_estado_no_hace_nada(reloj_falso):
    taximetro = crear_taximetro(reloj_falso)
    taximetro.iniciar_carrera()
    reloj_falso.avanzar(5)
    cambiado = taximetro.cambiar_estado(ESTADO_PARADO)
    assert cambiado is False
    assert taximetro.importe_actual() == pytest.approx(0.10)


def test_cambiar_estado_invalido_lanza_error(reloj_falso):
    taximetro = crear_taximetro(reloj_falso)
    taximetro.iniciar_carrera()
    with pytest.raises(EstadoInvalidoError):
        taximetro.cambiar_estado("volando")


def test_cambiar_estado_sin_carrera_iniciada_lanza_error(reloj_falso):
    taximetro = crear_taximetro(reloj_falso)
    with pytest.raises(CarreraNoIniciadaError):
        taximetro.cambiar_estado(ESTADO_MOVIMIENTO)


def test_finalizar_carrera_sin_iniciar_lanza_error(reloj_falso):
    taximetro = crear_taximetro(reloj_falso)
    with pytest.raises(CarreraNoIniciadaError):
        taximetro.finalizar_carrera()


def test_finalizar_carrera_devuelve_resumen_correcto(reloj_falso):
    taximetro = crear_taximetro(reloj_falso, tarifa_parado=0.02, tarifa_movimiento=0.05)
    taximetro.iniciar_carrera()
    reloj_falso.avanzar(10)
    taximetro.cambiar_estado(ESTADO_MOVIMIENTO)
    reloj_falso.avanzar(20)
    resumen = taximetro.finalizar_carrera()

    assert resumen["importe_total"] == pytest.approx(1.20)
    assert resumen["duracion_segundos"] == pytest.approx(30)
    assert taximetro.en_curso is False


def test_duracion_actual_crece_mientras_la_carrera_esta_en_curso(reloj_falso):
    taximetro = crear_taximetro(reloj_falso)
    taximetro.iniciar_carrera()
    reloj_falso.avanzar(15)
    assert taximetro.duracion_actual() == pytest.approx(15)


def test_duracion_actual_es_cero_sin_carrera_en_curso(reloj_falso):
    taximetro = crear_taximetro(reloj_falso)
    assert taximetro.duracion_actual() == 0.0


def test_nueva_carrera_reinicia_el_importe(reloj_falso):
    taximetro = crear_taximetro(reloj_falso)
    taximetro.iniciar_carrera()
    reloj_falso.avanzar(10)
    taximetro.finalizar_carrera()

    taximetro.iniciar_carrera()
    assert taximetro.importe_actual() == 0.0


def test_iniciar_con_una_carrera_en_curso_lanza_error(reloj_falso):
    from taximetro.core import CarreraEnCursoError

    taximetro = Taximetro(reloj=reloj_falso)
    taximetro.iniciar_carrera()
    with pytest.raises(CarreraEnCursoError):
        taximetro.iniciar_carrera()
