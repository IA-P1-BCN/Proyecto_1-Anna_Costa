import pytest


def registrar_y_loguear(cliente, username="responsable", password="clave-segura-123"):
    cliente.post("/api/auth/registro", json={"username": username, "password": password})
    respuesta = cliente.post("/api/auth/login", json={"username": username, "password": password})
    return respuesta.get_json()["token"]


def cabeceras(token):
    return {"Authorization": f"Bearer {token}"}


def test_endpoints_de_carrera_requieren_token(cliente):
    respuesta = cliente.post("/api/carreras/iniciar")
    assert respuesta.status_code == 401


def test_login_devuelve_username_y_rol(cliente):
    cliente.post("/api/auth/registro", json={"username": "jefa", "password": "clave-jefa-123"})
    respuesta = cliente.post(
        "/api/auth/login", json={"username": "jefa", "password": "clave-jefa-123"}
    )
    cuerpo = respuesta.get_json()
    assert cuerpo["username"] == "jefa"
    assert cuerpo["rol"] == "responsable"


def test_registro_login_y_flujo_completo_de_carrera(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.post("/api/carreras/iniciar", headers=cabeceras(token))
    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "parado"

    respuesta = cliente.post(
        "/api/carreras/estado", headers=cabeceras(token), json={"estado": "movimiento"}
    )
    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "movimiento"

    respuesta = cliente.post("/api/carreras/finalizar", headers=cabeceras(token))
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert "importe_total" in cuerpo
    assert cuerpo["importe_total"] >= 0


def test_actual_incluye_duracion_de_la_carrera_en_curso(cliente):
    token = registrar_y_loguear(cliente)
    cliente.post("/api/carreras/iniciar", headers=cabeceras(token))

    respuesta = cliente.get("/api/carreras/actual", headers=cabeceras(token))
    assert respuesta.status_code == 200
    assert "duracion_actual" in respuesta.get_json()


def test_historial_incluye_carreras_finalizadas(cliente):
    token = registrar_y_loguear(cliente)
    cliente.post("/api/carreras/iniciar", headers=cabeceras(token))
    cliente.post("/api/carreras/finalizar", headers=cabeceras(token))

    respuesta = cliente.get("/api/carreras/historial", headers=cabeceras(token))
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert len(cuerpo["carreras"]) == 1


def test_no_se_puede_registrar_el_mismo_username_dos_veces(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post(
        "/api/auth/registro", json={"username": "responsable", "password": "otra-clave-123"}
    )
    assert respuesta.status_code == 409


def test_se_pueden_registrar_varios_usuarios_distintos(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post(
        "/api/auth/registro", json={"username": "otro", "password": "otra-clave-123"}
    )
    assert respuesta.status_code == 201


def test_login_con_password_incorrecta_devuelve_401(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post(
        "/api/auth/login", json={"username": "responsable", "password": "incorrecta"}
    )
    assert respuesta.status_code == 401


def test_cambiar_estado_sin_carrera_en_curso_devuelve_409(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.post(
        "/api/carreras/estado", headers=cabeceras(token), json={"estado": "movimiento"}
    )
    assert respuesta.status_code == 409


def test_estado_invalido_devuelve_400(cliente):
    token = registrar_y_loguear(cliente)
    cliente.post("/api/carreras/iniciar", headers=cabeceras(token))
    respuesta = cliente.post(
        "/api/carreras/estado", headers=cabeceras(token), json={"estado": "volando"}
    )
    assert respuesta.status_code == 400


def test_el_responsable_ve_el_historial_de_todos(cliente):
    token_responsable = registrar_y_loguear(
        cliente, username="jefa_flota", password="clave-jefa-123"
    )
    cliente.post("/api/carreras/iniciar", headers=cabeceras(token_responsable))
    cliente.post("/api/carreras/finalizar", headers=cabeceras(token_responsable))

    token_taxista = registrar_y_loguear(cliente, username="conductor_b", password="clave-b-123")
    cliente.post("/api/carreras/iniciar", headers=cabeceras(token_taxista))
    cliente.post("/api/carreras/finalizar", headers=cabeceras(token_taxista))

    historial_responsable = cliente.get(
        "/api/carreras/historial", headers=cabeceras(token_responsable)
    ).get_json()
    historial_taxista = cliente.get(
        "/api/carreras/historial", headers=cabeceras(token_taxista)
    ).get_json()
    assert len(historial_responsable["carreras"]) == 2
    assert len(historial_taxista["carreras"]) == 1


def test_cada_usuario_solo_ve_su_propio_historial(cliente):
    token_a = registrar_y_loguear(cliente, username="conductor_a", password="clave-a-123")
    token_b = registrar_y_loguear(cliente, username="conductor_b", password="clave-b-123")

    cliente.post("/api/carreras/iniciar", headers=cabeceras(token_a))
    cliente.post("/api/carreras/finalizar", headers=cabeceras(token_a))

    historial_a = cliente.get("/api/carreras/historial", headers=cabeceras(token_a)).get_json()
    historial_b = cliente.get("/api/carreras/historial", headers=cabeceras(token_b)).get_json()
    assert len(historial_a["carreras"]) == 1
    assert len(historial_b["carreras"]) == 0


def test_token_invalido_es_rechazado(cliente):
    respuesta = cliente.get(
        "/api/carreras/historial", headers={"Authorization": "Bearer token-falso"}
    )
    assert respuesta.status_code == 401


@pytest.mark.parametrize("dos_apps_independientes", [True])
def test_dos_apps_no_comparten_estado(dos_apps_independientes, tmp_path):
    from taximetro.api import create_app

    app_a = create_app(
        ruta_bd=tmp_path / "a.db",
        ruta_usuarios=tmp_path / "a_usuarios.json",
        ruta_config=tmp_path / "no_existe.json",
    )
    app_b = create_app(
        ruta_bd=tmp_path / "b.db",
        ruta_usuarios=tmp_path / "b_usuarios.json",
        ruta_config=tmp_path / "no_existe.json",
    )

    cliente_a = app_a.test_client()
    cliente_b = app_b.test_client()

    token_a = registrar_y_loguear(cliente_a, username="conductor_a", password="clave-a-123")

    respuesta = cliente_b.get("/api/carreras/historial", headers=cabeceras(token_a))
    assert respuesta.status_code == 401


def test_ver_tarifas_devuelve_los_valores_actuales(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.get("/api/tarifas", headers=cabeceras(token))
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert cuerpo["tarifa_parado"] > 0
    assert cuerpo["tarifa_movimiento"] > 0


def test_responsable_puede_actualizar_tarifas(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.patch(
        "/api/tarifas",
        headers=cabeceras(token),
        json={"tarifa_parado": 0.05, "tarifa_movimiento": 0.09},
    )
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"tarifa_parado": 0.05, "tarifa_movimiento": 0.09}

    respuesta = cliente.get("/api/tarifas", headers=cabeceras(token))
    assert respuesta.get_json() == {"tarifa_parado": 0.05, "tarifa_movimiento": 0.09}


def test_taxista_no_puede_actualizar_tarifas(cliente):
    registrar_y_loguear(cliente, username="jefa", password="clave-jefa-123")
    token_taxista = registrar_y_loguear(cliente, username="conductor_c", password="clave-c-123")

    respuesta = cliente.patch(
        "/api/tarifas",
        headers=cabeceras(token_taxista),
        json={"tarifa_parado": 0.05, "tarifa_movimiento": 0.09},
    )
    assert respuesta.status_code == 403


def test_actualizar_tarifas_con_valor_negativo_falla(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.patch(
        "/api/tarifas",
        headers=cabeceras(token),
        json={"tarifa_parado": -1, "tarifa_movimiento": 0.09},
    )
    assert respuesta.status_code == 400


def test_registro_rechaza_usuario_o_password_demasiado_cortos(cliente):
    respuesta = cliente.post(
        "/api/auth/registro", json={"username": "  ", "password": "clave-larga-1"}
    )
    assert respuesta.status_code == 400

    respuesta = cliente.post(
        "/api/auth/registro", json={"username": "conductor", "password": "corta"}
    )
    assert respuesta.status_code == 400


def test_iniciar_con_una_carrera_en_curso_no_la_pisa(app, cliente, reloj_falso):
    app.config["taximetro"]._reloj = reloj_falso
    token = registrar_y_loguear(cliente)
    cliente.post("/api/carreras/iniciar", headers=cabeceras(token))
    reloj_falso.avanzar(10)

    respuesta = cliente.post("/api/carreras/iniciar", headers=cabeceras(token))
    assert respuesta.status_code == 409

    actual = cliente.get("/api/carreras/actual", headers=cabeceras(token)).get_json()
    assert actual["importe_actual"] == pytest.approx(0.20)


def test_un_taxista_no_puede_tocar_la_carrera_de_otro(cliente):
    token_responsable = registrar_y_loguear(cliente, username="jefa", password="clave-jefa-123")
    token_a = registrar_y_loguear(cliente, username="conductor_a", password="clave-a-123")
    token_b = registrar_y_loguear(cliente, username="conductor_b", password="clave-b-123")
    cliente.post("/api/carreras/iniciar", headers=cabeceras(token_a))

    respuesta = cliente.post(
        "/api/carreras/estado", headers=cabeceras(token_b), json={"estado": "movimiento"}
    )
    assert respuesta.status_code == 403
    respuesta = cliente.post("/api/carreras/finalizar", headers=cabeceras(token_b))
    assert respuesta.status_code == 403

    respuesta = cliente.post("/api/carreras/finalizar", headers=cabeceras(token_responsable))
    assert respuesta.status_code == 200
    historial = cliente.get("/api/carreras/historial", headers=cabeceras(token_responsable))
    assert historial.get_json()["carreras"][0]["usuario"] == "conductor_a"


def test_cambiar_tarifas_no_recalcula_lo_ya_recorrido(app, cliente, reloj_falso):
    app.config["taximetro"]._reloj = reloj_falso
    token = registrar_y_loguear(cliente)
    cliente.post("/api/carreras/iniciar", headers=cabeceras(token))
    reloj_falso.avanzar(10)

    cliente.patch(
        "/api/tarifas", headers=cabeceras(token), json={"tarifa_parado": 5, "tarifa_movimiento": 5}
    )

    actual = cliente.get("/api/carreras/actual", headers=cabeceras(token)).get_json()
    assert actual["importe_actual"] == pytest.approx(0.20)


def test_las_tarifas_cambiadas_sobreviven_a_un_reinicio(tmp_path):
    from taximetro.api import create_app

    rutas = {
        "ruta_bd": tmp_path / "taximetro.db",
        "ruta_usuarios": tmp_path / "usuarios.json",
        "ruta_config": tmp_path / "config.json",
    }
    cliente = create_app(**rutas).test_client()
    token = registrar_y_loguear(cliente)
    cliente.patch(
        "/api/tarifas",
        headers=cabeceras(token),
        json={"tarifa_parado": 0.03, "tarifa_movimiento": 0.07},
    )

    reiniciada = create_app(**rutas)
    assert reiniciada.config["taximetro"].tarifa_parado == 0.03
    assert reiniciada.config["taximetro"].tarifa_movimiento == 0.07
