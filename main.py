
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Sistema Bancario")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "null",
        "http://127.0.0.1:8000",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datos temporales en memoria
usuarios = [
    {
        "nombre": "Juan Pérez",
        "correo": "juan.perez@example.com",
        "contraseña": "password123",
        "saldo": 100.0,
        "historico": []
    },
    {
        "nombre": "María López",
        "correo": "maria.lopez@example.com",
        "contraseña": "password456",
        "saldo": 100.0,
        "historico": []
    },
    {
        "nombre": "Kevin Martínez",
        "correo": "kevin.martinez@example.com",
        "contraseña": "password789",
        "saldo": 100.0,
        "historico": []
    }
]


# Datos recibidos desde el frontend
class UsuarioEntrada(BaseModel):
    nombre: str
    correo: str
    contraseña: str
    

class LoginEntrada(BaseModel):
    nombre: str
    contraseña: str



# Página de prueba de la API
@app.get("/")
def inicio():
    return {"mensaje": "API bancaria funcionando"}


# Crear cuenta
@app.post("/usuarios")
def crear_cuenta(datos: UsuarioEntrada):

    for usuario in usuarios:
        if usuario["correo"] == datos.correo:
            return {"error": "El correo ya está registrado"}

    nuevo_usuario = {
        "nombre": datos.nombre,
        "correo": datos.correo,
        "contraseña": datos.contraseña,
        "saldo": 0.0,
        "historico": []
    }

    usuarios.append(nuevo_usuario)

    return {
        "mensaje": "Cuenta creada exitosamente",
        "nombre": nuevo_usuario["nombre"]
    }


# Iniciar sesión

@app.post("/login")
def iniciar_sesion(datos: LoginEntrada):

    for usuario in usuarios:
        if (
            usuario["nombre"] == datos.nombre
            and usuario["contraseña"] == datos.contraseña
        ):
            return {
                "mensaje": "Inicio de sesión exitoso",
                "nombre": usuario["nombre"],
                "correo": usuario["correo"]
            }

    return {"error": "Usuario o contraseña incorrectos"}



from fastapi import HTTPException

@app.get("/saldo/{correo}")
def consultar_saldo(correo: str):

    for usuario in usuarios:
        if usuario["correo"] == correo:
            return {
                "nombre": usuario["nombre"],
                "saldo": usuario["saldo"]
            }

    raise HTTPException(
        status_code=404,
        detail="Usuario no encontrado"
    )



from pydantic import BaseModel, Field
from fastapi import HTTPException

class DepositoEntrada(BaseModel):
    correo: str
    monto: float = Field(gt=0, allow_inf_nan=False)


@app.post("/depositar")
def depositar(datos: DepositoEntrada):

    for usuario in usuarios:
        if usuario["correo"] == datos.correo:

            usuario["saldo"] += datos.monto

            usuario["historico"].append(
                ("depósito", datos.monto, None)
            )

            return {
                "mensaje": "Depósito realizado exitosamente",
                "saldo": usuario["saldo"]
            }

    raise HTTPException(
        status_code=404,
        detail="Usuario no encontrado"
    )


class RetiroEntrada(BaseModel):
    correo: str
    monto: float = Field(gt=0, allow_inf_nan=False)


@app.post("/retirar")
def retirar(datos: RetiroEntrada):

    for usuario in usuarios:
        if usuario["correo"] == datos.correo:

            if datos.monto > usuario["saldo"]:
                raise HTTPException(
                    status_code=400,
                    detail="Saldo insuficiente"
                )

            usuario["saldo"] -= datos.monto

            usuario["historico"].append(
                ("retiro", datos.monto, None)
            )

            return {
                "mensaje": "Retiro realizado exitosamente",
                "saldo": usuario["saldo"]
            }

    raise HTTPException(
        status_code=404,
        detail="Usuario no encontrado"
    )


class TransferenciaEntrada(BaseModel):
    correo_origen: str
    correo_destino: str
    monto: float = Field(gt=0, allow_inf_nan=False)
    
@app.post("/transferir")
def transferir(datos: TransferenciaEntrada):
    remitente = None
    destinatario = None

    for usuario in usuarios:
        if usuario["correo"] == datos.correo_origen:
            remitente = usuario

        if usuario["correo"] == datos.correo_destino:
            destinatario = usuario

    if remitente is None:
        raise HTTPException(
            status_code=404,
            detail="Cuenta de origen no encontrada"
        )

    if destinatario is None:
        raise HTTPException(
            status_code=404,
            detail="Cuenta de destino no encontrada"
        )

    if remitente["correo"] == destinatario["correo"]:
        raise HTTPException(
            status_code=400,
            detail="No puedes transferir dinero a tu propia cuenta"
        )

    if datos.monto > remitente["saldo"]:
        raise HTTPException(
            status_code=400,
            detail="Saldo insuficiente"
        )

    remitente["saldo"] -= datos.monto
    destinatario["saldo"] += datos.monto

    remitente["historico"].append(
        ("transferencia enviada", datos.monto, destinatario["nombre"])
    )

    destinatario["historico"].append(
        ("transferencia recibida", datos.monto, remitente["nombre"])
    )

    return {
        "mensaje": "Transferencia realizada exitosamente",
        "saldo": remitente["saldo"]
    }
    


@app.get("/historico/{correo}")
def consultar_historico(correo: str):
    for usuario in usuarios:
        if usuario["correo"] == correo:
            movimientos = []

            for movimiento in usuario["historico"]:
                tipo, monto, otra_persona = movimiento

                movimientos.append({
                    "tipo": tipo,
                    "monto": monto,
                    "otra_persona": otra_persona
                })

            return {
                "nombre": usuario["nombre"],
                "historico": movimientos
            }

    raise HTTPException(
        status_code=404,
        detail="Usuario no encontrado"
    )
