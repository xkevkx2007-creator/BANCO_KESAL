const API_URL = "https://banco-kesal.onrender.com";

const mensaje = document.getElementById("mensaje");

// INICIAR SESIÓN
document.getElementById("form-login").addEventListener("submit", async (event) => {
    event.preventDefault();

    const datos = {
        nombre: document.getElementById("login-nombre").value,
        contraseña: document.getElementById("login-contrasena").value
    };

    try {
        const respuesta = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json();

        mensaje.textContent =
            resultado.mensaje || resultado.error || "No se pudo iniciar sesión.";
            if (respuesta.ok && resultado.correo && resultado.nombre) {
    sessionStorage.setItem("nombre", resultado.nombre);
    sessionStorage.setItem("correo", resultado.correo);

    window.location.href = "banco.html";
}
    } catch (error) {
        mensaje.textContent = "No se pudo conectar con el servidor.";
    }
});

// CPF: permitir solo números (máximo 11)
const campoCpf = document.getElementById("registro-cpf");

campoCpf.addEventListener("input", () => {
    campoCpf.value = campoCpf.value.replace(/\D/g, "").slice(0, 11);
});

// CREAR CUENTA
document.getElementById("form-registro").addEventListener("submit", async (event) => {
    event.preventDefault();

    const cpf = campoCpf.value.trim();

    if (!/^[0-9]{11}$/.test(cpf)) {
        mensaje.textContent = "El CPF debe tener exactamente 11 números.";
        return;
    }

    const datos = {
        nombre: document.getElementById("registro-nombre").value,
        cpf: cpf,
        correo: document.getElementById("registro-correo").value,
        contraseña: document.getElementById("registro-contrasena").value
    };

    try {
        const respuesta = await fetch(`${API_URL}/usuarios`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json();

        let detalle = "";

        if (typeof resultado.detail === "string") {
            detalle = resultado.detail;
        } else if (Array.isArray(resultado.detail) && resultado.detail.length > 0) {
            // Error de validación del servidor (422): indicar qué campo falló
            const fallo = resultado.detail[0];
            const campo = Array.isArray(fallo.loc) ? fallo.loc[fallo.loc.length - 1] : "";
            detalle = `Error en el campo "${campo}": ${fallo.msg}`;
        }

        mensaje.textContent =
            resultado.mensaje || resultado.error || detalle || "No se pudo crear la cuenta.";

        if (respuesta.ok && resultado.mensaje === "Cuenta creada exitosamente") {
            document.getElementById("form-registro").reset();
        }
    } catch (error) {
        mensaje.textContent = "No se pudo conectar con el servidor.";
    }
});