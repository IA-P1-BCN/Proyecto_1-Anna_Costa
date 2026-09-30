def registrar_y_loguear(cliente, username="responsable", password="clave-segura-123"):
    cliente.post("/auth/registro", json={"username": username, "password": password})
    respuesta = cliente.post("/auth/login", json={"username": username, "password": password})
    return respuesta.json()["token"]


def cabeceras(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_no_requiere_token(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200


def test_endpoints_de_carrera_requieren_token(cliente):
    respuesta = cliente.post("/carreras")
    assert respuesta.status_code == 401


def test_login_devuelve_username_y_rol(cliente):
    cliente.post("/auth/registro", json={"username": "jefa", "password": "clave-jefa-123"})
    respuesta = cliente.post("/auth/login", json={"username": "jefa", "password": "clave-jefa-123"})
    cuerpo = respuesta.json()
    assert cuerpo["username"] == "jefa"
    assert cuerpo["rol"] == "responsable"


def test_carreras_devuelven_el_conductor_que_las_hizo(cliente):
    token = registrar_y_loguear(cliente, username="conductor_x", password="clave-x-12345")
    respuesta = cliente.post("/carreras", headers=cabeceras(token))
    assert respuesta.json()["usuario"] == "conductor_x"


def test_registro_login_y_flujo_completo_de_carrera(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.post("/carreras", headers=cabeceras(token))
    assert respuesta.status_code == 201
    carrera = respuesta.json()
    assert carrera["estado"] == "parado"

    respuesta = cliente.patch(
        f"/carreras/{carrera['id']}/estado", headers=cabeceras(token), json={"estado": "movimiento"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "movimiento"

    respuesta = cliente.post(f"/carreras/{carrera['id']}/finalizar", headers=cabeceras(token))
    assert respuesta.status_code == 200
    assert respuesta.json()["en_curso"] is False


def test_no_se_puede_iniciar_otra_carrera_con_una_en_curso(cliente):
    token = registrar_y_loguear(cliente)
    carrera = cliente.post("/carreras", headers=cabeceras(token)).json()

    respuesta = cliente.post("/carreras", headers=cabeceras(token))
    assert respuesta.status_code == 409

    cliente.post(f"/carreras/{carrera['id']}/finalizar", headers=cabeceras(token))
    respuesta = cliente.post("/carreras", headers=cabeceras(token))
    assert respuesta.status_code == 201


def test_historial_incluye_carreras_finalizadas(cliente):
    token = registrar_y_loguear(cliente)
    carrera = cliente.post("/carreras", headers=cabeceras(token)).json()
    cliente.post(f"/carreras/{carrera['id']}/finalizar", headers=cabeceras(token))

    respuesta = cliente.get("/carreras", headers=cabeceras(token))
    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1


def test_no_se_puede_registrar_el_mismo_username_dos_veces(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post(
        "/auth/registro", json={"username": "responsable", "password": "otra-clave-123"}
    )
    assert respuesta.status_code == 409


def test_registro_rechaza_usuario_o_password_demasiado_cortos(cliente):
    respuesta = cliente.post("/auth/registro", json={"username": "  ", "password": "clave-larga-1"})
    assert respuesta.status_code == 400

    respuesta = cliente.post("/auth/registro", json={"username": "conductor", "password": "corta"})
    assert respuesta.status_code == 400


def test_registro_quita_los_espacios_del_usuario(cliente):
    cliente.post("/auth/registro", json={"username": "  jefa  ", "password": "clave-jefa-123"})
    respuesta = cliente.post("/auth/login", json={"username": "jefa", "password": "clave-jefa-123"})
    assert respuesta.status_code == 200


def test_el_responsable_puede_finalizar_la_carrera_de_otro(cliente):
    token_responsable = registrar_y_loguear(cliente, username="jefa", password="clave-jefa-123")
    token_taxista = registrar_y_loguear(cliente, username="conductor_b", password="clave-b-12345")
    carrera = cliente.post("/carreras", headers=cabeceras(token_taxista)).json()

    respuesta = cliente.post(
        f"/carreras/{carrera['id']}/finalizar", headers=cabeceras(token_responsable)
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["en_curso"] is False
    assert respuesta.json()["usuario"] == "conductor_b"


def test_se_pueden_registrar_varios_usuarios_distintos(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post(
        "/auth/registro", json={"username": "otro", "password": "otra-clave-123"}
    )
    assert respuesta.status_code == 201


def test_login_con_password_incorrecta_devuelve_401(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post("/auth/login", json={"username": "responsable", "password": "mal"})
    assert respuesta.status_code == 401


def test_cambiar_estado_de_carrera_finalizada_devuelve_409(cliente):
    token = registrar_y_loguear(cliente)
    carrera = cliente.post("/carreras", headers=cabeceras(token)).json()
    cliente.post(f"/carreras/{carrera['id']}/finalizar", headers=cabeceras(token))

    respuesta = cliente.patch(
        f"/carreras/{carrera['id']}/estado", headers=cabeceras(token), json={"estado": "movimiento"}
    )
    assert respuesta.status_code == 409


def test_carrera_inexistente_devuelve_404(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.get("/carreras/9999", headers=cabeceras(token))
    assert respuesta.status_code == 404


def test_token_invalido_es_rechazado(cliente):
    respuesta = cliente.get("/carreras", headers={"Authorization": "Bearer token-falso"})
    assert respuesta.status_code == 401


def test_cada_usuario_solo_ve_su_propio_historial(cliente):
    token_a = registrar_y_loguear(cliente, username="conductor_a", password="clave-a-12345")
    token_b = registrar_y_loguear(cliente, username="conductor_b", password="clave-b-12345")

    carrera_a = cliente.post("/carreras", headers=cabeceras(token_a)).json()
    cliente.post(f"/carreras/{carrera_a['id']}/finalizar", headers=cabeceras(token_a))

    historial_a = cliente.get("/carreras", headers=cabeceras(token_a)).json()
    historial_b = cliente.get("/carreras", headers=cabeceras(token_b)).json()
    assert len(historial_a) == 1
    assert len(historial_b) == 0


def test_el_responsable_ve_el_historial_de_todos(cliente):
    token_responsable = registrar_y_loguear(
        cliente, username="jefa_flota", password="clave-jefa-12345"
    )
    token_taxista = registrar_y_loguear(cliente, username="conductor_b", password="clave-b-12345")

    carrera_taxista = cliente.post("/carreras", headers=cabeceras(token_taxista)).json()
    cliente.post(f"/carreras/{carrera_taxista['id']}/finalizar", headers=cabeceras(token_taxista))

    historial_responsable = cliente.get("/carreras", headers=cabeceras(token_responsable)).json()
    historial_taxista = cliente.get("/carreras", headers=cabeceras(token_taxista)).json()
    assert len(historial_responsable) == 1
    assert len(historial_taxista) == 1

    respuesta = cliente.get(
        f"/carreras/{carrera_taxista['id']}", headers=cabeceras(token_responsable)
    )
    assert respuesta.status_code == 200


def test_no_se_puede_acceder_a_la_carrera_de_otro_usuario(cliente):
    token_a = registrar_y_loguear(cliente, username="conductor_a", password="clave-a-12345")
    token_b = registrar_y_loguear(cliente, username="conductor_b", password="clave-b-12345")

    carrera_a = cliente.post("/carreras", headers=cabeceras(token_a)).json()

    respuesta = cliente.get(f"/carreras/{carrera_a['id']}", headers=cabeceras(token_b))
    assert respuesta.status_code == 404

    respuesta = cliente.patch(
        f"/carreras/{carrera_a['id']}/estado",
        headers=cabeceras(token_b),
        json={"estado": "movimiento"},
    )
    assert respuesta.status_code == 404


def test_ver_tarifas_devuelve_los_valores_por_defecto(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.get("/tarifas", headers=cabeceras(token))
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["tarifa_parado"] > 0
    assert cuerpo["tarifa_movimiento"] > 0


def test_responsable_puede_actualizar_tarifas(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.patch(
        "/tarifas",
        headers=cabeceras(token),
        json={"tarifa_parado": 0.05, "tarifa_movimiento": 0.09},
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"tarifa_parado": 0.05, "tarifa_movimiento": 0.09}

    respuesta = cliente.get("/tarifas", headers=cabeceras(token))
    assert respuesta.json() == {"tarifa_parado": 0.05, "tarifa_movimiento": 0.09}


def test_taxista_no_puede_actualizar_tarifas(cliente):
    registrar_y_loguear(cliente, username="jefa", password="clave-jefa-12345")
    token_taxista = registrar_y_loguear(cliente, username="conductor_c", password="clave-c-12345")

    respuesta = cliente.patch(
        "/tarifas",
        headers=cabeceras(token_taxista),
        json={"tarifa_parado": 0.05, "tarifa_movimiento": 0.09},
    )
    assert respuesta.status_code == 403


def test_actualizar_tarifas_con_valor_negativo_falla(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.patch(
        "/tarifas",
        headers=cabeceras(token),
        json={"tarifa_parado": -1, "tarifa_movimiento": 0.09},
    )
    assert respuesta.status_code == 400


def test_tarifa_actualizada_afecta_a_carreras_nuevas(cliente):
    token = registrar_y_loguear(cliente)
    cliente.patch(
        "/tarifas",
        headers=cabeceras(token),
        json={"tarifa_parado": 1000.0, "tarifa_movimiento": 1000.0},
    )
    carrera = cliente.post("/carreras", headers=cabeceras(token)).json()
    respuesta = cliente.get(f"/carreras/{carrera['id']}", headers=cabeceras(token))
    assert respuesta.json()["importe_en_vivo"] > 0


def test_cambiar_tarifas_no_recalcula_lo_ya_recorrido(cliente):
    token = registrar_y_loguear(cliente)
    cliente.patch(
        "/tarifas",
        headers=cabeceras(token),
        json={"tarifa_parado": 100000.0, "tarifa_movimiento": 100000.0},
    )
    carrera = cliente.post("/carreras", headers=cabeceras(token)).json()
    cliente.patch(
        "/tarifas",
        headers=cabeceras(token),
        json={"tarifa_parado": 0.001, "tarifa_movimiento": 0.001},
    )
    respuesta = cliente.get(f"/carreras/{carrera['id']}", headers=cabeceras(token))
    assert respuesta.json()["importe_en_vivo"] > 1
