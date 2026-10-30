
const API_URL = "http://127.0.0.1:8000";

// Recuperar el usuario que inició sesión
const nombreUsuario = sessionStorage.getItem("nombre");
const correoUsuario = sessionStorage.getItem("correo");

if (!nombreUsuario || !correoUsuario) {
    window.location.href = "index.html";
} else {
    document.getElementById("nombre-usuario").textContent = nombreUsuario;
}

// ========================================
// CONSULTAR SALDO
// ========================================

async function consultarSaldo() {
    const mensaje = document.getElementById("mensaje");

    try {
        const respuesta = await fetch(
            `${API_URL}/saldo/${encodeURIComponent(correoUsuario)}`
        );

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            mensaje.textContent =
                datos.detail || "No se pudo consultar el saldo.";
            return;
        }

        document.getElementById("saldo").textContent =
            Number(datos.saldo).toLocaleString("pt-BR", {
                style: "currency",
                currency: "BRL"
            });

        mensaje.textContent = "";
    } catch (error) {
        mensaje.textContent = "No se pudo conectar con el servidor.";
    }
}

document.getElementById("btn-actualizar").addEventListener(
    "click",
    consultarSaldo
);

// Cerrar sesión y regresar al inicio
const botonSalir = document.getElementById("btn-salir");

if (botonSalir) {
    botonSalir.addEventListener("click", () => {
        sessionStorage.clear();
        window.location.href = "index.html";
    });
}

// Consultar el saldo al entrar
if (nombreUsuario && correoUsuario) {
    consultarSaldo();
}

// ========================================
// DEPOSITAR DINERO
// ========================================

document.getElementById("form-deposito").addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const monto = Number(
            document.getElementById("monto-deposito").value
        );

        const mensaje = document.getElementById("mensaje");

        if (!Number.isFinite(monto) || monto <= 0) {
            mensaje.textContent = "El monto debe ser mayor que cero.";
            return;
        }

        try {
            const respuesta = await fetch(`${API_URL}/depositar`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    correo: correoUsuario,
                    monto: monto
                })
            });

            const datos = await respuesta.json();

            if (!respuesta.ok) {
                mensaje.textContent =
                    datos.detail || "No se pudo realizar el depósito.";
                return;
            }

            mensaje.textContent = datos.mensaje;

            document.getElementById("form-deposito").reset();

            await consultarSaldo();

        } catch (error) {
            mensaje.textContent = "No se pudo conectar con el servidor.";
        }
    }
);

// ========================================
// RETIRAR DINERO
// ========================================

document.getElementById("form-retiro").addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const monto = Number(
            document.getElementById("monto-retiro").value
        );

        const mensaje = document.getElementById("mensaje");

        if (!Number.isFinite(monto) || monto <= 0) {
            mensaje.textContent = "El monto debe ser mayor que cero.";
            return;
        }

        try {
            const respuesta = await fetch(`${API_URL}/retirar`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    correo: correoUsuario,
                    monto: monto
                })
            });

            const datos = await respuesta.json();

            if (!respuesta.ok) {
                mensaje.textContent =
                    datos.detail || "No se pudo realizar el retiro.";
                return;
            }

            mensaje.textContent = datos.mensaje;

            document.getElementById("form-retiro").reset();

            await consultarSaldo();

        } catch (error) {
            mensaje.textContent = "No se pudo conectar con el servidor.";
        }
    }
);

// ========================================
// TRANSFERIR DINERO
// ========================================

document.getElementById("form-transferencia").addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const correoDestino =
            document.getElementById("correo-destino").value.trim();

        const monto = Number(
            document.getElementById("monto-transferencia").value
        );

        const mensaje = document.getElementById("mensaje");

        if (!Number.isFinite(monto) || monto <= 0) {
            mensaje.textContent = "El monto debe ser mayor que cero.";
            return;
        }

        if (correoDestino === correoUsuario) {
            mensaje.textContent =
                "No puedes transferir dinero a tu propia cuenta.";
            return;
        }

        try {
            const respuesta = await fetch(`${API_URL}/transferir`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    correo_origen: correoUsuario,
                    correo_destino: correoDestino,
                    monto: monto
                })
            });

            const datos = await respuesta.json();

            if (!respuesta.ok) {
                mensaje.textContent =
                    datos.detail || "No se pudo realizar la transferencia.";
                return;
            }

            mensaje.textContent = datos.mensaje;

            document.getElementById("form-transferencia").reset();

            await consultarSaldo();

        } catch (error) {
            mensaje.textContent =
                "No se pudo conectar con el servidor.";
        }
    }
);

// ========================================
// HISTORIAL DE MOVIMIENTOS
// ========================================

document.getElementById("btn-historico").addEventListener(
    "click",
    async () => {
        const lista = document.getElementById("lista-historico");
        const mensaje = document.getElementById("mensaje");

        lista.replaceChildren();

        try {
            const respuesta = await fetch(
                `${API_URL}/historico/${encodeURIComponent(correoUsuario)}`
            );

            const datos = await respuesta.json();

            if (!respuesta.ok) {
                mensaje.textContent =
                    datos.detail || "No se pudo consultar el historial.";
                return;
            }

            if (!Array.isArray(datos.historico) ||
                datos.historico.length === 0) {

                const item = document.createElement("li");
                item.textContent = "Todavía no hay movimientos.";
                lista.appendChild(item);

                mensaje.textContent = "";
                return;
            }

            datos.historico.forEach((movimiento) => {
                const item = document.createElement("li");

                const tipoOriginal = String(
                    movimiento.tipo || ""
                ).trim();

                const tipo = tipoOriginal.toLowerCase();

                const monto = Number(movimiento.monto).toLocaleString(
                    "pt-BR",
                    {
                        style: "currency",
                        currency: "BRL"
                    }
                );

                let clase = "movimiento-transferencia";
                let icono = "↗";
                let signo = "";
                let descripcion = tipoOriginal || "Movimiento";

                // Depósito
                if (
                    tipo.includes("deposit") ||
                    tipo.includes("depósito") ||
                    tipo.includes("deposito")
                ) {
                    clase = "movimiento-deposito";
                    icono = "↓";
                    signo = "+";
                    descripcion = "Depósito";

                // Retiro
                } else if (
                    tipo.includes("retir") ||
                    tipo.includes("saque") ||
                    tipo.includes("retiro")
                ) {
                    clase = "movimiento-retiro";
                    icono = "↑";
                    signo = "−";
                    descripcion = "Retiro";

                // Transferencia
                } else if (tipo.includes("transfer")) {
                    clase = "movimiento-transferencia";
                    icono = "↗";
                    descripcion = "Transferencia";
                }

                if (movimiento.otra_persona) {
                    descripcion += ` · ${movimiento.otra_persona}`;
                }

                // Icono del movimiento
                const iconoElemento = document.createElement("span");
                iconoElemento.className = "movimiento-icono";
                iconoElemento.textContent = icono;
                iconoElemento.setAttribute("aria-hidden", "true");

                // Detalles del movimiento
                const detalles = document.createElement("div");
                detalles.className = "movimiento-detalles";

                const titulo = document.createElement("span");
                titulo.className = "movimiento-titulo";
                titulo.textContent = descripcion;

                const subtitulo = document.createElement("span");
                subtitulo.className = "movimiento-subtitulo";
                subtitulo.textContent = "Movimiento bancario";

                // Valor del movimiento
                const valor = document.createElement("span");
                valor.className = "movimiento-valor";
                valor.textContent = `${signo}${monto}`;

                // Construir la tarjeta
                detalles.append(titulo, subtitulo);

                item.className = `movimiento-item ${clase}`;
                item.append(iconoElemento, detalles, valor);

                lista.appendChild(item);
            });

            mensaje.textContent = "Historial cargado correctamente.";

        } catch (error) {
            mensaje.textContent =
                "No se pudo conectar con el servidor.";
        }
    }
);
