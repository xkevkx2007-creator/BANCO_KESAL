usuarios = [
    {
        "nombre": "Juan Pérez",
        "correo": "juan.perez@example.com",
        "contraseña": "password123",
        "saldo": 0.0,
        "historico": []
    },
    {
        "nombre": "María López",
        "correo": "maria.lopez@example.com",
        "contraseña": "password456",
        "saldo": 0.0,
        "historico": []
    },
    {
        "nombre": "Kevin Martínez",
        "correo": "kevin.martinez@example.com",
        "contraseña": "password789",
        "saldo": 0.0,
        "historico": []
    }
]


# ---------------- MENU PRINCIPAL ----------------

def menu():

    print("\n----- Bienvenido al sistema bancario -----")
    print("1. Iniciar sesión")
    print("2. Crear cuenta")
    print("3. Salir")


# ---------------- INICIAR SESIÓN ----------------

def iniciar_sesion():

    user_name = input("Ingrese su Usuario: ")
    user_password = input("Ingrese su contraseña: ")

    usuario_encontrado = None

    for usuario in usuarios:

        if usuario["nombre"] == user_name and usuario["contraseña"] == user_password:

            usuario_encontrado = usuario
            break

    if usuario_encontrado:

        print("****************************************************")
        print("Inicio de sesión exitoso.")
        print(f"Bienvenido, {usuario_encontrado['nombre']}!")

        return usuario_encontrado

    else:

        print("****************************************************")
        print("Nombre de usuario o contraseña incorrectos.")

        opcion1 = input("¿Desea crear una nueva cuenta? (s/n): ")

        if opcion1.lower() == "s":

            return crear_cuenta()

        elif opcion1.lower() == "n":

            print("****************************************************")
            print("Volviendo al menú principal...")

            return None

        else:

            print("****************************************************")
            print("Opción inválida.")

            return None


# ---------------- CREAR CUENTA ----------------

def crear_cuenta():

    nombre = input("Ingrese su nombre: ")
    correo = input("Ingrese su correo electrónico: ")
    contraseña = input("Ingrese su contraseña: ")

    # Verificar si el correo ya existe

    for usuario in usuarios:

        if usuario["correo"] == correo:

            print("****************************************************")
            print("Ya existe una cuenta con ese correo electrónico.")

            return None

    nuevo_usuario = {
        "nombre": nombre,
        "correo": correo,
        "contraseña": contraseña,
        "saldo": 0.0,
        "historico": []
    }

    usuarios.append(nuevo_usuario)

    print("****************************************************")
    print("Cuenta creada exitosamente.")
    print(f"Bienvenido, {nombre}!")

    return nuevo_usuario


# ---------------- CONSULTAR SALDO ----------------

def consultar_saldo(usuario):

    print("****************************************************")
    print(f"Su saldo disponible es: R$ {usuario['saldo']:.2f}")


# ---------------- REALIZAR RETIRO ----------------

def realizar_retiro(usuario):

    try:

        monto_retiro = float(
            input("Ingrese el monto a retirar: ")
        )

    except ValueError:

        print("****************************************************")
        print("Ingrese un valor numérico válido.")
        return

    if monto_retiro <= 0:

        print("****************************************************")
        print("El monto debe ser mayor que cero.")

    elif monto_retiro <= usuario["saldo"]:

        usuario["saldo"] -= monto_retiro

        # Registrar solamente retiros exitosos
        usuario["historico"].append(
            ("retiro", monto_retiro, None)
        )

        print("****************************************************")
        print("Retiro realizado exitosamente.")
        print(f"Su nuevo saldo es: R$ {usuario['saldo']:.2f}")

    else:

        print("****************************************************")
        print("Saldo insuficiente para realizar el retiro.")


# ---------------- REALIZAR DEPÓSITO ----------------

def realizar_deposito(usuario):

    try:

        monto_deposito = float(
            input("Ingrese el monto a depositar: ")
        )

    except ValueError:

        print("****************************************************")
        print("Ingrese un valor numérico válido.")
        return

    if monto_deposito <= 0:

        print("****************************************************")
        print("El monto debe ser mayor que cero.")

    else:

        usuario["saldo"] += monto_deposito

        usuario["historico"].append(
            ("depósito", monto_deposito, None)
        )

        print("****************************************************")
        print("Depósito realizado exitosamente.")
        print(f"Su nuevo saldo es: R$ {usuario['saldo']:.2f}")


# ---------------- REALIZAR TRANSFERENCIA ----------------

def realizar_transferencia(usuario):

    correo_destino = input(
        "Ingrese el correo electrónico del destinatario: "
    )

    try:

        monto_transferencia = float(
            input("Ingrese el monto a transferir: ")
        )

    except ValueError:

        print("****************************************************")
        print("Ingrese un valor numérico válido.")
        return

    usuario_destino = None

    for user in usuarios:

        if user["correo"] == correo_destino:

            usuario_destino = user
            break

    if usuario_destino is None:

        print("****************************************************")
        print("No se encontró un usuario con ese correo electrónico.")

    elif usuario_destino == usuario:

        print("****************************************************")
        print("No puede transferir dinero a su propia cuenta.")

    elif monto_transferencia <= 0:

        print("****************************************************")
        print("El monto debe ser mayor que cero.")

    elif monto_transferencia > usuario["saldo"]:

        print("****************************************************")
        print("Saldo insuficiente para realizar la transferencia.")

    else:

        # Quitar dinero del remitente
        usuario["saldo"] -= monto_transferencia

        # Agregar dinero al destinatario
        usuario_destino["saldo"] += monto_transferencia

        # Registrar transferencia del remitente
        usuario["historico"].append(
            (
                "transferencia enviada",
                monto_transferencia,
                usuario_destino["nombre"]
            )
        )

        # Registrar transferencia del destinatario
        usuario_destino["historico"].append(
            (
                "transferencia recibida",
                monto_transferencia,
                usuario["nombre"]
            )
        )

        print("****************************************************")
        print("Transferencia realizada exitosamente.")
        print(
            f"Su nuevo saldo es: R$ {usuario['saldo']:.2f}"
        )


# ---------------- CERRAR SESIÓN ----------------

def cerrar_sesion():

    print("****************************************************")
    print("Sesión cerrada correctamente.")
    print("Volviendo al menú principal...")


# ---------------- SALIR ----------------

def salir():

    print("****************************************************")
    print("Gracias por usar nuestro sistema bancario. ¡Hasta luego!")


# ---------------- MENÚ BANCARIO ----------------

def menu_entrada():

    print("\n----- Menú de operaciones bancarias -----")
    print("1. Consultar saldo")
    print("2. Realizar retiro")
    print("3. Realizar depósito")
    print("4. Transferir dinero")
    print("5. Cerrar sesión")
    print("6. Ver historial de transacciones")


# ---------------- VER HISTORIAL DE TRANSACCIONES ----------------

def ver_historial(usuario):

    if not usuario["historico"]:

        print("****************************************************")
        print("No hay transacciones registradas.")

    else:

        print("****************************************************")
        print("Historial de transacciones:")

        for transaccion in usuario["historico"]:

            tipo, monto, otra_persona = transaccion

            if tipo == "transferencia enviada":

                print(
                    f"Transferencia de R$ {monto:.2f} "
                    f"a {otra_persona}"
                )

            elif tipo == "transferencia recibida":

                print(
                    f"Transferencia de R$ {monto:.2f} "
                    f"recibida de {otra_persona}"
                )

            else:

                print(
                    f"{tipo.capitalize()} de R$ {monto:.2f}"
                )


# ---------------- PROGRAMA PRINCIPAL ----------------

while True:

    menu()

    opcion = input(
        "Ingrese el número de la opción deseada: "
    )

    # INICIAR SESIÓN

    if opcion == "1":

        usuario_actual = iniciar_sesion()

        if usuario_actual:

            # MENÚ BANCARIO

            while True:

                menu_entrada()

                opcion_entrada = input(
                    "Ingrese el número de la opción deseada: "
                )

                if opcion_entrada == "1":

                    consultar_saldo(usuario_actual)

                elif opcion_entrada == "2":

                    realizar_retiro(usuario_actual)

                elif opcion_entrada == "3":

                    realizar_deposito(usuario_actual)

                elif opcion_entrada == "4":

                    realizar_transferencia(usuario_actual)

                elif opcion_entrada == "5":

                    cerrar_sesion()
                    break

                elif opcion_entrada == "6":

                    ver_historial(usuario_actual)

                else:

                    print("****************************************************")
                    print("Opción inválida. Intente nuevamente.")

    # CREAR CUENTA

    elif opcion == "2":

        crear_cuenta()

    # SALIR

    elif opcion == "3":

        salir()
        break

    # OPCIÓN INVÁLIDA

    else:

        print("****************************************************")
        print("Opción inválida. Intente nuevamente.")