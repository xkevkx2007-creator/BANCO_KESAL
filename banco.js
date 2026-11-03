const API_URL = "https://banco-kesal.onrender.com";

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

        const campoContrasena =
            document.getElementById("contrasena-retiro");

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
                    monto: monto,
                    contraseña: campoContrasena.value
                })
            });

            const datos = await respuesta.json();

            if (!respuesta.ok) {
                mensaje.textContent =
                    typeof datos.detail === "string"
                        ? datos.detail
                        : "No se pudo realizar el retiro.";

                // Por seguridad, limpiar la contraseña tras un intento fallido
                campoContrasena.value = "";
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

                // PIX
                if (tipo.includes("pix")) {
                    if (tipo.includes("recib")) {
                        clase = "movimiento-deposito";
                        icono = "↓";
                        signo = "+";
                        descripcion = "PIX recibido";
                    } else {
                        clase = "movimiento-retiro";
                        icono = "↑";
                        signo = "−";
                        descripcion = "PIX enviado";
                    }

                // Depósito
                } else if (
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

// ========================================
// PIX (SIMULADO)
// ========================================

const ETIQUETAS_CHAVE = {
    cpf: "CPF",
    email: "Correo",
    aleatoria: "Aleatoria"
};

function mostrarMensaje(texto) {
    document.getElementById("mensaje").textContent = texto;
}

async function cargarChaves() {
    const lista = document.getElementById("lista-chaves");

    try {
        const respuesta = await fetch(
            `${API_URL}/pix/chaves/${encodeURIComponent(correoUsuario)}`
        );

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            mostrarMensaje(
                datos.detail || "No se pudieron cargar tus chaves PIX."
            );
            return;
        }

        lista.replaceChildren();

        if (datos.chaves.length === 0) {
            const vacio = document.createElement("li");
            vacio.className = "chave-vacia";
            vacio.textContent = "Todavía no tienes chaves PIX.";
            lista.appendChild(vacio);
            return;
        }

        datos.chaves.forEach((chave) => {
            const item = document.createElement("li");
            item.className = "chave-item";

            const tipo = document.createElement("span");
            tipo.className = "chave-tipo";
            tipo.textContent = ETIQUETAS_CHAVE[chave.tipo] || chave.tipo;

            const valor = document.createElement("span");
            valor.className = "chave-valor";
            valor.textContent = chave.valor;

            const eliminar = document.createElement("button");
            eliminar.type = "button";
            eliminar.textContent = "Eliminar";
            eliminar.addEventListener("click", () =>
                eliminarChave(chave.valor)
            );

            item.append(tipo, valor, eliminar);
            lista.appendChild(item);
        });

    } catch (error) {
        mostrarMensaje("No se pudo conectar con el servidor.");
    }
}

async function registrarChave(tipo) {
    try {
        const respuesta = await fetch(`${API_URL}/pix/chaves`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                correo: correoUsuario,
                tipo: tipo
            })
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            mostrarMensaje(
                typeof datos.detail === "string"
                    ? datos.detail
                    : "No se pudo registrar la chave."
            );
            return;
        }

        mostrarMensaje(datos.mensaje);
        await cargarChaves();

    } catch (error) {
        mostrarMensaje("No se pudo conectar con el servidor.");
    }
}

async function eliminarChave(valor) {
    if (!confirm(`¿Eliminar la chave ${valor}?`)) {
        return;
    }

    try {
        const respuesta = await fetch(`${API_URL}/pix/chaves/eliminar`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                correo: correoUsuario,
                chave: valor
            })
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            mostrarMensaje(
                typeof datos.detail === "string"
                    ? datos.detail
                    : "No se pudo eliminar la chave."
            );
            return;
        }

        mostrarMensaje(datos.mensaje);
        await cargarChaves();

    } catch (error) {
        mostrarMensaje("No se pudo conectar con el servidor.");
    }
}

document.getElementById("btn-chave-cpf").addEventListener(
    "click",
    () => registrarChave("cpf")
);

document.getElementById("btn-chave-email").addEventListener(
    "click",
    () => registrarChave("email")
);

document.getElementById("btn-chave-aleatoria").addEventListener(
    "click",
    () => registrarChave("aleatoria")
);

document.getElementById("form-pix").addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const chave = document.getElementById("chave-pix").value.trim();
        const campoContrasena = document.getElementById("contrasena-pix");

        const monto = Number(
            document.getElementById("monto-pix").value
        );

        if (!Number.isFinite(monto) || monto <= 0) {
            mostrarMensaje("El monto debe ser mayor que cero.");
            return;
        }

        try {
            // 1) Ver a quién pertenece la chave y pedir confirmación
            const consulta = await fetch(
                `${API_URL}/pix/consultar/${encodeURIComponent(chave)}`
            );

            const destino = await consulta.json();

            if (!consulta.ok) {
                mostrarMensaje(
                    typeof destino.detail === "string"
                        ? destino.detail
                        : "No se pudo consultar la chave PIX."
                );
                return;
            }

            const montoTexto = monto.toLocaleString("pt-BR", {
                style: "currency",
                currency: "BRL"
            });

            if (!confirm(`¿Enviar ${montoTexto} por PIX a ${destino.nombre}?`)) {
                mostrarMensaje("PIX cancelado.");
                return;
            }

            // 2) Enviar el PIX
            const respuesta = await fetch(`${API_URL}/pix/enviar`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    correo_origen: correoUsuario,
                    chave: chave,
                    monto: monto,
                    contraseña: campoContrasena.value
                })
            });

            const datos = await respuesta.json();

            if (!respuesta.ok) {
                mostrarMensaje(
                    typeof datos.detail === "string"
                        ? datos.detail
                        : "No se pudo enviar el PIX."
                );

                // Por seguridad, limpiar la contraseña tras un intento fallido
                campoContrasena.value = "";
                return;
            }

            mostrarMensaje(datos.mensaje);

            document.getElementById("form-pix").reset();

            await consultarSaldo();

            // consultarSaldo() borra el mensaje: volver a mostrarlo
            mostrarMensaje(datos.mensaje);

        } catch (error) {
            mostrarMensaje("No se pudo conectar con el servidor.");
        }
    }
);

// Cargar las chaves al entrar
if (nombreUsuario && correoUsuario) {
    cargarChaves();
}