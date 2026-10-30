
const API_URL = "http://127.0.0.1:8000";

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

// CREAR CUENTA
document.getElementById("form-registro").addEventListener("submit", async (event) => {
    event.preventDefault();

    const datos = {
        nombre: document.getElementById("registro-nombre").value,
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

        mensaje.textContent =
            resultado.mensaje || resultado.error || "No se pudo crear la cuenta.";

        if (respuesta.ok && resultado.mensaje === "Cuenta creada exitosamente") {
            document.getElementById("form-registro").reset();
        }
    } catch (error) {
        mensaje.textContent = "No se pudo conectar con el servidor.";
    }
});
