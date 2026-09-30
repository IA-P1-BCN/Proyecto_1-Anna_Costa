import json
import os
import secrets
from pathlib import Path

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from taximetro.logger import get_logger

logger = get_logger(__name__)

RUTA_USUARIOS_DEFECTO = Path(__file__).resolve().parent.parent / "data" / "usuarios.json"
DURACION_TOKEN_SEGUNDOS = 8 * 60 * 60


class CredencialesInvalidasError(Exception):
    pass


class TokenInvalidoError(Exception):
    pass


class CredencialesNoValidasError(ValueError):
    pass


def validar_credenciales_nuevas(username, password):
    username = (username or "").strip()
    if not 3 <= len(username) <= 30:
        raise CredencialesNoValidasError("El usuario debe tener entre 3 y 30 caracteres.")
    if len(password or "") < 8:
        raise CredencialesNoValidasError("La contraseña debe tener al menos 8 caracteres.")
    return username


def _clave_secreta():
    return os.environ.get("TAXIMETRO_SECRET_KEY") or secrets.token_hex(32)


def _hash_de(registro):
    return registro["password_hash"] if isinstance(registro, dict) else registro


def _rol_de(registro):
    return registro.get("rol", "taxista") if isinstance(registro, dict) else "taxista"


class GestorUsuarios:
    def __init__(self, ruta_usuarios=RUTA_USUARIOS_DEFECTO, clave_secreta=None):
        self.ruta_usuarios = Path(ruta_usuarios)
        self.ruta_usuarios.parent.mkdir(parents=True, exist_ok=True)
        self._serializador = URLSafeTimedSerializer(clave_secreta or _clave_secreta())
        if not self.ruta_usuarios.exists():
            self._escribir_usuarios({})

    def _leer_usuarios(self):
        return json.loads(self.ruta_usuarios.read_text(encoding="utf-8"))

    def _escribir_usuarios(self, usuarios):
        self.ruta_usuarios.write_text(json.dumps(usuarios, indent=2), encoding="utf-8")

    def existe_algun_usuario(self):
        return len(self._leer_usuarios()) > 0

    def existe_usuario(self, username):
        return username in self._leer_usuarios()

    def crear_usuario(self, username, password):
        usuarios = self._leer_usuarios()
        rol = "responsable" if not usuarios else "taxista"
        usuarios[username] = {"password_hash": generate_password_hash(password), "rol": rol}
        self._escribir_usuarios(usuarios)
        logger.info("Usuario creado: %s (rol=%s)", username, rol)
        return rol

    def verificar_credenciales(self, username, password):
        usuarios = self._leer_usuarios()
        registro = usuarios.get(username)
        hash_guardado = _hash_de(registro) if registro else None
        if not hash_guardado or not check_password_hash(hash_guardado, password):
            logger.warning("Intento de login fallido para usuario=%s", username)
            raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")
        logger.info("Login correcto: %s", username)
        return _rol_de(registro)

    def emitir_token(self, username, rol):
        return self._serializador.dumps({"username": username, "rol": rol})

    def datos_del_token(self, token):
        try:
            datos = self._serializador.loads(token, max_age=DURACION_TOKEN_SEGUNDOS)
        except SignatureExpired as exc:
            raise TokenInvalidoError("El token ha caducado, vuelve a iniciar sesión.") from exc
        except BadSignature as exc:
            raise TokenInvalidoError("Token inválido.") from exc
        return {"username": datos["username"], "rol": datos.get("rol", "taxista")}
