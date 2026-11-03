"""Capa de base de datos del sistema bancario.

Por defecto usa SQLite (archivo banco.db junto a este archivo). Si existe la
variable de entorno DATABASE_URL con una URL de PostgreSQL, usa PostgreSQL.

Los saldos y montos se guardan en centavos (enteros) para evitar errores de
redondeo con decimales.
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USA_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))
RUTA_SQLITE = os.getenv("SQLITE_PATH") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "banco.db"
)

if USA_POSTGRES:
    import psycopg2
    import psycopg2.extras

    ERRORES_INTEGRIDAD = (sqlite3.IntegrityError, psycopg2.IntegrityError)
else:
    ERRORES_INTEGRIDAD = (sqlite3.IntegrityError,)

# Límite por operación: R$ 100.000.000.000,00
MONTO_MAXIMO_CENTAVOS = 10**13

# Usuarios de ejemplo que se crean solo cuando la base de datos está vacía
USUARIOS_INICIALES = [
    ("Juan Pérez", "juan.perez@example.com", "password123"),
    ("María López", "maria.lopez@example.com", "password456"),
    ("Kevin Martínez", "kevin.martinez@example.com", "password789"),
]
SALDO_INICIAL_CENTAVOS = 10000  # R$ 100,00


class ErrorBanco(Exception):
    """Error de negocio con mensaje para el usuario y código HTTP."""

    def __init__(self, detalle, status=400):
        super().__init__(detalle)
        self.detalle = detalle
        self.status = status


# ---------------------------------------------------------------------------
# Conexión
# ---------------------------------------------------------------------------

class _Conexion:
    """Envoltorio mínimo para usar la misma sintaxis en SQLite y PostgreSQL.

    Las consultas se escriben con "?" como marcador de parámetros.
    """

    def __init__(self):
        if USA_POSTGRES:
            self._c = psycopg2.connect(DATABASE_URL)
        else:
            self._c = sqlite3.connect(RUTA_SQLITE, timeout=15)
            self._c.row_factory = sqlite3.Row
            self._c.execute("PRAGMA foreign_keys = ON")

    def _cursor(self):
        if USA_POSTGRES:
            return self._c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return self._c.cursor()

    @staticmethod
    def _sql(sql):
        return sql.replace("?", "%s") if USA_POSTGRES else sql

    def ejecutar(self, sql, params=()):
        """Ejecuta una instrucción y devuelve las filas afectadas."""
        cur = self._cursor()
        try:
            cur.execute(self._sql(sql), params)
            return cur.rowcount
        finally:
            cur.close()

    def consultar(self, sql, params=()):
        cur = self._cursor()
        try:
            cur.execute(self._sql(sql), params)
            return cur.fetchall()
        finally:
            cur.close()

    def uno(self, sql, params=()):
        filas = self.consultar(sql, params)
        return filas[0] if filas else None


@contextmanager
def conexion():
    """Abre una conexión; confirma al salir bien y deshace todo si hay error."""
    db = _Conexion()
    try:
        yield db
        db._c.commit()
    except BaseException:
        db._c.rollback()
        raise
    finally:
        db._c.close()


# ---------------------------------------------------------------------------
# Contraseñas
# ---------------------------------------------------------------------------

_SCRYPT = dict(n=2**14, r=8, p=1, dklen=32)


def hash_contrasena(contrasena):
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(contrasena.encode("utf-8"), salt=sal, **_SCRYPT)
    return f"scrypt${sal.hex()}${h.hex()}"


def verificar_contrasena(contrasena, almacenado):
    try:
        esquema, sal_hex, hash_hex = almacenado.split("$")
        if esquema != "scrypt":
            return False
        h = hashlib.scrypt(
            contrasena.encode("utf-8"), salt=bytes.fromhex(sal_hex), **_SCRYPT
        )
    except (ValueError, TypeError, AttributeError):
        return False
    return hmac.compare_digest(h.hex(), hash_hex)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalizar_correo(correo):
    return correo.strip().lower()


def a_centavos(monto):
    """Convierte un monto en reales (float) a centavos enteros."""
    try:
        centavos = int(
            (Decimal(str(monto)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        )
    except (ArithmeticError, ValueError):
        raise ErrorBanco("Monto inválido")

    if centavos <= 0:
        raise ErrorBanco("El monto mínimo es R$ 0,01")
    if centavos > MONTO_MAXIMO_CENTAVOS:
        raise ErrorBanco("El monto es demasiado grande")
    return centavos


def _usuario_por_correo(db, correo, detalle="Usuario no encontrado"):
    usuario = db.uno(
        "SELECT * FROM usuarios WHERE correo = ?", (_normalizar_correo(correo),)
    )
    if usuario is None:
        raise ErrorBanco(detalle, 404)
    return usuario


def _saldo_actual(db, usuario_id):
    fila = db.uno("SELECT saldo_centavos FROM usuarios WHERE id = ?", (usuario_id,))
    return fila["saldo_centavos"] / 100


def _registrar_movimiento(db, usuario_id, tipo, centavos, otra_persona):
    db.ejecutar(
        "INSERT INTO movimientos "
        "(usuario_id, tipo, monto_centavos, otra_persona, fecha) "
        "VALUES (?, ?, ?, ?, ?)",
        (usuario_id, tipo, centavos, otra_persona, _ahora()),
    )


def _debitar(db, usuario_id, centavos):
    """Resta saldo solo si alcanza. La condición va en el propio UPDATE para
    que sea seguro aunque lleguen varias peticiones al mismo tiempo."""
    afectadas = db.ejecutar(
        "UPDATE usuarios SET saldo_centavos = saldo_centavos - ? "
        "WHERE id = ? AND saldo_centavos >= ?",
        (centavos, usuario_id, centavos),
    )
    if afectadas == 0:
        raise ErrorBanco("Saldo insuficiente")


def _acreditar(db, usuario_id, centavos):
    db.ejecutar(
        "UPDATE usuarios SET saldo_centavos = saldo_centavos + ? WHERE id = ?",
        (centavos, usuario_id),
    )


# ---------------------------------------------------------------------------
# Inicialización
# ---------------------------------------------------------------------------

def _esquema():
    pk = "SERIAL PRIMARY KEY" if USA_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    return [
        f"""CREATE TABLE IF NOT EXISTS usuarios (
            id {pk},
            nombre TEXT NOT NULL UNIQUE,
            cpf TEXT UNIQUE,
            correo TEXT NOT NULL UNIQUE,
            contrasena_hash TEXT NOT NULL,
            saldo_centavos BIGINT NOT NULL DEFAULT 0 CHECK (saldo_centavos >= 0),
            creado_en TEXT NOT NULL
        )""",
        f"""CREATE TABLE IF NOT EXISTS movimientos (
            id {pk},
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            tipo TEXT NOT NULL,
            monto_centavos BIGINT NOT NULL,
            otra_persona TEXT,
            fecha TEXT NOT NULL
        )""",
        f"""CREATE TABLE IF NOT EXISTS chaves_pix (
            id {pk},
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            tipo TEXT NOT NULL,
            valor TEXT NOT NULL UNIQUE,
            creada_en TEXT NOT NULL,
            UNIQUE (usuario_id, tipo)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_movimientos_usuario "
        "ON movimientos(usuario_id)",
    ]


def init_db():
    """Crea las tablas si no existen y carga los usuarios de ejemplo."""
    with conexion() as db:
        if not USA_POSTGRES:
            # WAL permite leer y escribir a la vez sin bloqueos largos
            db.consultar("PRAGMA journal_mode = WAL")

        for sentencia in _esquema():
            db.ejecutar(sentencia)

        total = db.uno("SELECT COUNT(*) AS total FROM usuarios")["total"]
        if total == 0:
            for nombre, correo, contrasena in USUARIOS_INICIALES:
                db.ejecutar(
                    "INSERT INTO usuarios "
                    "(nombre, cpf, correo, contrasena_hash, saldo_centavos, creado_en) "
                    "VALUES (?, NULL, ?, ?, ?, ?)",
                    (
                        nombre,
                        correo,
                        hash_contrasena(contrasena),
                        SALDO_INICIAL_CENTAVOS,
                        _ahora(),
                    ),
                )


# ---------------------------------------------------------------------------
# Operaciones del banco
# ---------------------------------------------------------------------------

def crear_usuario(nombre, cpf, correo, contrasena):
    nombre = nombre.strip()
    cpf = cpf.strip()
    correo = _normalizar_correo(correo)

    if not nombre:
        raise ErrorBanco("El nombre de usuario es obligatorio")

    # El CPF debe tener exactamente 11 caracteres y todos deben ser dígitos 0-9
    if len(cpf) != 11 or not all(c in "0123456789" for c in cpf):
        raise ErrorBanco("El CPF debe tener exactamente 11 números")

    if not correo:
        raise ErrorBanco("El correo electrónico es obligatorio")

    if not contrasena:
        raise ErrorBanco("La contraseña es obligatoria")

    with conexion() as db:
        if db.uno("SELECT 1 AS x FROM usuarios WHERE correo = ?", (correo,)):
            raise ErrorBanco("El correo ya está registrado")

        if db.uno("SELECT 1 AS x FROM usuarios WHERE cpf = ?", (cpf,)):
            raise ErrorBanco("El CPF ya está registrado")

        if db.uno(
            "SELECT 1 AS x FROM usuarios WHERE lower(nombre) = lower(?)", (nombre,)
        ):
            raise ErrorBanco("El nombre de usuario ya está en uso")

        try:
            db.ejecutar(
                "INSERT INTO usuarios "
                "(nombre, cpf, correo, contrasena_hash, saldo_centavos, creado_en) "
                "VALUES (?, ?, ?, ?, 0, ?)",
                (nombre, cpf, correo, hash_contrasena(contrasena), _ahora()),
            )
        except ERRORES_INTEGRIDAD:
            # Dos registros simultáneos con los mismos datos
            raise ErrorBanco("El correo, CPF o nombre de usuario ya está registrado")

    return {"nombre": nombre, "correo": correo}


def autenticar(nombre, contrasena):
    """Devuelve los datos del usuario si las credenciales son correctas."""
    with conexion() as db:
        usuario = db.uno("SELECT * FROM usuarios WHERE nombre = ?", (nombre.strip(),))

    if usuario is None or not verificar_contrasena(
        contrasena, usuario["contrasena_hash"]
    ):
        return None

    return {"nombre": usuario["nombre"], "correo": usuario["correo"]}


def obtener_saldo(correo):
    with conexion() as db:
        usuario = _usuario_por_correo(db, correo)
        return {
            "nombre": usuario["nombre"],
            "saldo": usuario["saldo_centavos"] / 100,
        }


def depositar(correo, monto):
    centavos = a_centavos(monto)

    with conexion() as db:
        usuario = _usuario_por_correo(db, correo)
        _acreditar(db, usuario["id"], centavos)
        _registrar_movimiento(db, usuario["id"], "depósito", centavos, None)
        return {"saldo": _saldo_actual(db, usuario["id"])}


def retirar(correo, contrasena, monto):
    centavos = a_centavos(monto)

    with conexion() as db:
        usuario = _usuario_por_correo(db, correo)

        if not verificar_contrasena(contrasena, usuario["contrasena_hash"]):
            raise ErrorBanco("Contraseña incorrecta. No se realizó el retiro.", 401)

        _debitar(db, usuario["id"], centavos)
        _registrar_movimiento(db, usuario["id"], "retiro", centavos, None)
        return {"saldo": _saldo_actual(db, usuario["id"])}


def _mover_dinero(db, origen, destino, centavos, tipo_envio, tipo_recibo):
    """Pasa dinero de una cuenta a otra y registra los dos movimientos."""
    # Siempre se modifica primero la cuenta con id menor: evita bloqueos
    # cruzados si dos personas se envían dinero entre sí al mismo tiempo.
    pasos = [("debitar", origen), ("acreditar", destino)]
    if origen["id"] > destino["id"]:
        pasos.reverse()

    for accion, usuario in pasos:
        if accion == "debitar":
            _debitar(db, usuario["id"], centavos)
        else:
            _acreditar(db, usuario["id"], centavos)

    _registrar_movimiento(db, origen["id"], tipo_envio, centavos, destino["nombre"])
    _registrar_movimiento(db, destino["id"], tipo_recibo, centavos, origen["nombre"])

    return {"saldo": _saldo_actual(db, origen["id"])}


def transferir(correo_origen, correo_destino, monto):
    centavos = a_centavos(monto)

    with conexion() as db:
        origen = _usuario_por_correo(db, correo_origen, "Cuenta de origen no encontrada")
        destino = _usuario_por_correo(
            db, correo_destino, "Cuenta de destino no encontrada"
        )

        if origen["id"] == destino["id"]:
            raise ErrorBanco("No puedes transferir dinero a tu propia cuenta")

        return _mover_dinero(
            db, origen, destino, centavos,
            "transferencia enviada", "transferencia recibida",
        )


def obtener_historico(correo):
    with conexion() as db:
        usuario = _usuario_por_correo(db, correo)

        filas = db.consultar(
            "SELECT tipo, monto_centavos, otra_persona, fecha "
            "FROM movimientos WHERE usuario_id = ? ORDER BY id",
            (usuario["id"],),
        )

        return {
            "nombre": usuario["nombre"],
            "historico": [
                {
                    "tipo": f["tipo"],
                    "monto": f["monto_centavos"] / 100,
                    "otra_persona": f["otra_persona"],
                    "fecha": f["fecha"],
                }
                for f in filas
            ],
        }


# ---------------------------------------------------------------------------
# PIX (simulado)
# ---------------------------------------------------------------------------

TIPOS_CHAVE = ("cpf", "email", "aleatoria")

_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalizar_chave(chave):
    """Devuelve (tipo, valor) a partir de lo que escribió el usuario.

    Acepta CPF con o sin puntos y guion, correos y chaves aleatorias (UUID).
    """
    texto = chave.strip().lower()
    solo_digitos = texto.replace(".", "").replace("-", "").replace(" ", "")

    if _UUID.match(texto):
        return "aleatoria", texto
    if _EMAIL.match(texto):
        return "email", texto
    if len(solo_digitos) == 11 and all(c in "0123456789" for c in solo_digitos):
        return "cpf", solo_digitos

    raise ErrorBanco(
        "Chave PIX inválida. Usa un CPF (11 números), un correo "
        "o una chave aleatoria."
    )


def _dueno_de_chave(db, valor):
    return db.uno(
        "SELECT u.* FROM chaves_pix c "
        "JOIN usuarios u ON u.id = c.usuario_id "
        "WHERE c.valor = ?",
        (valor,),
    )


def listar_chaves(correo):
    with conexion() as db:
        usuario = _usuario_por_correo(db, correo)
        filas = db.consultar(
            "SELECT tipo, valor FROM chaves_pix WHERE usuario_id = ? ORDER BY id",
            (usuario["id"],),
        )
        return {"chaves": [{"tipo": f["tipo"], "valor": f["valor"]} for f in filas]}


def crear_chave(correo, tipo):
    if tipo not in TIPOS_CHAVE:
        raise ErrorBanco("Tipo de chave inválido")

    with conexion() as db:
        usuario = _usuario_por_correo(db, correo)

        if db.uno(
            "SELECT 1 AS x FROM chaves_pix WHERE usuario_id = ? AND tipo = ?",
            (usuario["id"], tipo),
        ):
            raise ErrorBanco("Ya tienes una chave de ese tipo")

        if tipo == "cpf":
            if not usuario["cpf"]:
                raise ErrorBanco("Tu cuenta no tiene CPF registrado")
            valor = usuario["cpf"]
        elif tipo == "email":
            valor = usuario["correo"]
        else:
            valor = str(uuid.uuid4())

        try:
            db.ejecutar(
                "INSERT INTO chaves_pix (usuario_id, tipo, valor, creada_en) "
                "VALUES (?, ?, ?, ?)",
                (usuario["id"], tipo, valor, _ahora()),
            )
        except ERRORES_INTEGRIDAD:
            raise ErrorBanco("Esa chave ya está registrada")

    return {"tipo": tipo, "valor": valor}


def eliminar_chave(correo, chave):
    _, valor = normalizar_chave(chave)

    with conexion() as db:
        usuario = _usuario_por_correo(db, correo)
        afectadas = db.ejecutar(
            "DELETE FROM chaves_pix WHERE usuario_id = ? AND valor = ?",
            (usuario["id"], valor),
        )
        if afectadas == 0:
            raise ErrorBanco("Chave PIX no encontrada", 404)


def consultar_chave(chave):
    """Dice a quién pertenece una chave, para confirmar antes de enviar."""
    tipo, valor = normalizar_chave(chave)

    with conexion() as db:
        dueno = _dueno_de_chave(db, valor)
        if dueno is None:
            raise ErrorBanco("Chave PIX no encontrada", 404)
        return {"nombre": dueno["nombre"], "tipo": tipo}


def enviar_pix(correo_origen, chave, contrasena, monto):
    centavos = a_centavos(monto)
    _, valor = normalizar_chave(chave)

    with conexion() as db:
        origen = _usuario_por_correo(db, correo_origen, "Cuenta de origen no encontrada")

        if not verificar_contrasena(contrasena, origen["contrasena_hash"]):
            raise ErrorBanco("Contraseña incorrecta. No se envió el PIX.", 401)

        destino = _dueno_de_chave(db, valor)
        if destino is None:
            raise ErrorBanco("Chave PIX no encontrada", 404)

        if destino["id"] == origen["id"]:
            raise ErrorBanco("No puedes enviarte un PIX a ti mismo")

        resultado = _mover_dinero(
            db, origen, destino, centavos, "pix enviado", "pix recibido"
        )
        resultado["destinatario"] = destino["nombre"]
        return resultado