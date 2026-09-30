import pytest

from taximetro.auth import GestorUsuarios
from taximetro.cli import autenticar


@pytest.fixture
def gestor(tmp_path):
    return GestorUsuarios(tmp_path / "usuarios.json", clave_secreta="clave-de-test")


def test_primer_arranque_crea_usuario(gestor, monkeypatch, capsys):
    entradas = iter(["taxista1"])
    monkeypatch.setattr("builtins.input", lambda _: next(entradas))
    monkeypatch.setattr("getpass.getpass", lambda _: "clave-segura-123")

    username = autenticar(gestor)

    assert username == "taxista1"
    assert gestor.existe_algun_usuario()
    assert "creado" in capsys.readouterr().out.lower()


def test_login_con_credenciales_correctas(gestor, monkeypatch, capsys):
    gestor.crear_usuario("taxista1", "clave-segura-123")
    monkeypatch.setattr("builtins.input", lambda _: "taxista1")
    monkeypatch.setattr("getpass.getpass", lambda _: "clave-segura-123")

    username = autenticar(gestor)

    assert username == "taxista1"
    assert "bienvenido" in capsys.readouterr().out.lower()


def test_login_con_credenciales_incorrectas_reintenta_y_luego_bloquea(gestor, monkeypatch):
    gestor.crear_usuario("taxista1", "clave-segura-123")
    monkeypatch.setattr("builtins.input", lambda _: "taxista1")
    monkeypatch.setattr("getpass.getpass", lambda _: "clave-incorrecta")

    with pytest.raises(SystemExit):
        autenticar(gestor)


def test_login_se_recupera_tras_un_fallo(gestor, monkeypatch):
    gestor.crear_usuario("taxista1", "clave-segura-123")
    intentos_password = iter(["clave-mal", "clave-segura-123"])
    monkeypatch.setattr("builtins.input", lambda _: "taxista1")
    monkeypatch.setattr("getpass.getpass", lambda _: next(intentos_password))

    username = autenticar(gestor)

    assert username == "taxista1"


def test_primer_arranque_repite_si_las_credenciales_no_son_validas(gestor, monkeypatch, capsys):
    usuarios = iter(["", "taxista1"])
    claves = iter(["corta", "clave-segura-123"])
    monkeypatch.setattr("builtins.input", lambda _: next(usuarios))
    monkeypatch.setattr("getpass.getpass", lambda _: next(claves))

    username = autenticar(gestor)

    assert username == "taxista1"
    assert "entre 3 y 30" in capsys.readouterr().out
