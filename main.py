from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas (y los usuarios de ejemplo) al arrancar el servidor
    database.init_db()
    yield


app = FastAPI(title="Sistema Bancario", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "null",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "https://xkevkx2007-creator.github.io",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


def _http_error(error: database.ErrorBanco) -> HTTPException:
    return HTTPException(status_code=error.status, detail=error.detalle)


# Datos recibidos desde el frontend
class UsuarioEntrada(BaseModel):
    nombre: str
    cpf: str
    correo: str
    contraseña: str


class LoginEntrada(BaseModel):
    nombre: str
    contraseña: str


class DepositoEntrada(BaseModel):
    correo: str
    monto: float = Field(gt=0, allow_inf_nan=False)


class RetiroEntrada(BaseModel):
    correo: str
    contraseña: str
    monto: float = Field(gt=0, allow_inf_nan=False)


class TransferenciaEntrada(BaseModel):
    correo_origen: str
    correo_destino: str
    monto: float = Field(gt=0, allow_inf_nan=False)


class ChaveCrearEntrada(BaseModel):
    correo: str
    tipo: str


class ChaveEliminarEntrada(BaseModel):
    correo: str
    chave: str


class PixEntrada(BaseModel):
    correo_origen: str
    chave: str
    contraseña: str
    monto: float = Field(gt=0, allow_inf_nan=False)


# Página de prueba de la API
@app.get("/")
def inicio():
    return {"mensaje": "API bancaria funcionando"}


# Crear cuenta
@app.post("/usuarios")
def crear_cuenta(datos: UsuarioEntrada):

    try:
        usuario = database.crear_usuario(
            datos.nombre, datos.cpf, datos.correo, datos.contraseña
        )
    except database.ErrorBanco as error:
        return {"error": error.detalle}

    return {
        "mensaje": "Cuenta creada exitosamente",
        "nombre": usuario["nombre"]
    }


# Iniciar sesión
@app.post("/login")
def iniciar_sesion(datos: LoginEntrada):

    usuario = database.autenticar(datos.nombre, datos.contraseña)

    if usuario is None:
        return {"error": "Usuario o contraseña incorrectos"}

    return {
        "mensaje": "Inicio de sesión exitoso",
        "nombre": usuario["nombre"],
        "correo": usuario["correo"]
    }


@app.get("/saldo/{correo}")
def consultar_saldo(correo: str):

    try:
        return database.obtener_saldo(correo)
    except database.ErrorBanco as error:
        raise _http_error(error)


@app.post("/depositar")
def depositar(datos: DepositoEntrada):

    try:
        resultado = database.depositar(datos.correo, datos.monto)
    except database.ErrorBanco as error:
        raise _http_error(error)

    return {
        "mensaje": "Depósito realizado exitosamente",
        "saldo": resultado["saldo"]
    }


@app.post("/retirar")
def retirar(datos: RetiroEntrada):

    try:
        resultado = database.retirar(
            datos.correo, datos.contraseña, datos.monto
        )
    except database.ErrorBanco as error:
        raise _http_error(error)

    return {
        "mensaje": "Retiro realizado exitosamente",
        "saldo": resultado["saldo"]
    }


@app.post("/transferir")
def transferir(datos: TransferenciaEntrada):

    try:
        resultado = database.transferir(
            datos.correo_origen, datos.correo_destino, datos.monto
        )
    except database.ErrorBanco as error:
        raise _http_error(error)

    return {
        "mensaje": "Transferencia realizada exitosamente",
        "saldo": resultado["saldo"]
    }


@app.get("/historico/{correo}")
def consultar_historico(correo: str):

    try:
        return database.obtener_historico(correo)
    except database.ErrorBanco as error:
        raise _http_error(error)


# ---------------- PIX (simulado) ----------------

@app.get("/pix/chaves/{correo}")
def listar_chaves(correo: str):

    try:
        return database.listar_chaves(correo)
    except database.ErrorBanco as error:
        raise _http_error(error)


@app.post("/pix/chaves")
def crear_chave(datos: ChaveCrearEntrada):

    try:
        chave = database.crear_chave(datos.correo, datos.tipo)
    except database.ErrorBanco as error:
        raise _http_error(error)

    return {
        "mensaje": "Chave PIX registrada exitosamente",
        "chave": chave
    }


@app.post("/pix/chaves/eliminar")
def eliminar_chave(datos: ChaveEliminarEntrada):

    try:
        database.eliminar_chave(datos.correo, datos.chave)
    except database.ErrorBanco as error:
        raise _http_error(error)

    return {"mensaje": "Chave PIX eliminada"}


@app.get("/pix/consultar/{chave}")
def consultar_chave(chave: str):

    try:
        return database.consultar_chave(chave)
    except database.ErrorBanco as error:
        raise _http_error(error)


@app.post("/pix/enviar")
def enviar_pix(datos: PixEntrada):

    try:
        resultado = database.enviar_pix(
            datos.correo_origen, datos.chave, datos.contraseña, datos.monto
        )
    except database.ErrorBanco as error:
        raise _http_error(error)

    return {
        "mensaje": f"PIX enviado a {resultado['destinatario']}",
        "saldo": resultado["saldo"]
    }