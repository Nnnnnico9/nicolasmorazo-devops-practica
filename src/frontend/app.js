// Frontend de la tienda online.
// Toda la comunicación con la API se hace en la función `api()` usando fetch.
// Endpoints utilizados:
//   GET  /productos                    -> cargarProductos()
//   GET  /productos?nombre=...         -> formulario "Buscar por nombre"
//   POST /productos                    -> formulario "Nuevo producto"
//   GET  /usuarios                     -> cargarUsuarios()
//   POST /pedidos                      -> formulario "Nuevo pedido"
//   GET  /usuarios/{id}/pedidos        -> formulario "Pedidos de un usuario"

// Si la página la sirve la propia API (http://localhost:8000), se usa ese mismo
// origen; si se abre el index.html directamente (file://), el valor del campo.
if (location.protocol.startsWith("http")) {
  document.getElementById("api-url").value = location.origin;
}
let BASE_URL = document.getElementById("api-url").value;
let productos = [];

// ---------------------------------------------------------------------------
// Petición HTTP genérica: envía JSON, comprueba el código de estado y
// devuelve el JSON de la respuesta. Si la API responde con error, lanza una
// excepción con el mensaje `detail` que devuelve FastAPI.
// ---------------------------------------------------------------------------
async function api(metodo, ruta, cuerpo) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }

  const respuesta = await fetch(BASE_URL + ruta, opciones);
  const datos = respuesta.status === 204 ? null : await respuesta.json();

  if (!respuesta.ok) {
    throw new Error(`${respuesta.status}: ${textoError(datos)}`);
  }
  return datos;
}

// FastAPI devuelve `detail` como texto (errores de negocio) o como lista (422).
function textoError(datos) {
  if (!datos || !datos.detail) return "Error desconocido";
  if (Array.isArray(datos.detail)) {
    return datos.detail.map((e) => e.msg).join("; ");
  }
  return datos.detail;
}

// ---------------------------------------------------------------------------
// Utilidades de interfaz
// ---------------------------------------------------------------------------
function mostrarMensaje(texto, tipo) {
  const caja = document.getElementById("mensaje");
  caja.textContent = texto;
  caja.className = `mensaje ${tipo}`;
  clearTimeout(mostrarMensaje.timer);
  mostrarMensaje.timer = setTimeout(() => caja.classList.add("oculto"), 5000);
}

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = texto ?? "";
  return div.innerHTML;
}

function euros(n) {
  return n.toFixed(2) + " €";
}

// ---------------------------------------------------------------------------
// Productos
// ---------------------------------------------------------------------------
async function cargarProductos() {
  productos = await api("GET", "/productos");
  pintarProductos(productos);

  // Actualiza los desplegables de producto del formulario de pedido
  document.querySelectorAll(".linea select").forEach(rellenarSelectProductos);
}

function pintarProductos(lista) {
  document.getElementById("tabla-productos").innerHTML = lista
    .map((p) => {
      let detalles = "";
      if (p.tipo === "electronico") detalles = `Garantía: ${p.meses_garantia} meses`;
      if (p.tipo === "ropa") detalles = `Talla ${escapar(p.talla)}, ${escapar(p.color)}`;
      return `<tr>
        <td>${escapar(p.nombre)}</td><td>${p.tipo}</td><td>${euros(p.precio)}</td>
        <td>${p.stock}</td><td>${detalles}</td></tr>`;
    })
    .join("");
}

// Búsqueda con parámetro de consulta: GET /productos?nombre=...
document.getElementById("form-buscar").addEventListener("submit", async (e) => {
  e.preventDefault();
  const nombre = document.getElementById("buscar-nombre").value.trim();
  if (!nombre) return cargarProductos();
  try {
    const encontrados = await api("GET", `/productos?nombre=${encodeURIComponent(nombre)}`);
    pintarProductos(encontrados);
    if (encontrados.length === 0) mostrarMensaje(`No hay productos llamados "${nombre}"`, "error");
  } catch (err) {
    mostrarMensaje(`No se pudo buscar. ${err.message}`, "error");
  }
});

document.getElementById("btn-ver-todos").addEventListener("click", () => {
  document.getElementById("buscar-nombre").value = "";
  cargarProductos();
});

function rellenarSelectProductos(select) {
  const actual = select.value;
  select.innerHTML = productos
    .map((p) => `<option value="${p.id}">${escapar(p.nombre)} (${euros(p.precio)}, stock ${p.stock})</option>`)
    .join("");
  if (actual) select.value = actual;
}

// Muestra solo los campos que corresponden al tipo de producto elegido
document.getElementById("prod-tipo").addEventListener("change", (e) => {
  const tipo = e.target.value;
  document.querySelectorAll(".campo-electronico").forEach((el) => el.classList.toggle("oculto", tipo !== "electronico"));
  document.querySelectorAll(".campo-ropa").forEach((el) => el.classList.toggle("oculto", tipo !== "ropa"));
});

document.getElementById("form-producto").addEventListener("submit", async (e) => {
  e.preventDefault();
  const tipo = document.getElementById("prod-tipo").value;
  const cuerpo = {
    tipo,
    nombre: document.getElementById("prod-nombre").value,
    precio: parseFloat(document.getElementById("prod-precio").value),
    stock: parseInt(document.getElementById("prod-stock").value, 10),
  };
  if (tipo === "electronico") {
    cuerpo.meses_garantia = parseInt(document.getElementById("prod-garantia").value, 10);
  }
  if (tipo === "ropa") {
    cuerpo.talla = document.getElementById("prod-talla").value;
    cuerpo.color = document.getElementById("prod-color").value;
  }

  try {
    const producto = await api("POST", "/productos", cuerpo);
    mostrarMensaje(`Producto "${producto.nombre}" creado`, "ok");
    e.target.reset();
    document.getElementById("prod-tipo").dispatchEvent(new Event("change"));
    await cargarProductos();
  } catch (err) {
    mostrarMensaje(`No se pudo crear el producto. ${err.message}`, "error");
  }
});

// ---------------------------------------------------------------------------
// Usuarios
// ---------------------------------------------------------------------------
async function cargarUsuarios() {
  const usuarios = await api("GET", "/usuarios");

  document.getElementById("tabla-usuarios").innerHTML = usuarios
    .map((u) => `<tr><td>${escapar(u.nombre)}</td><td>${escapar(u.email)}</td>
      <td>${u.es_admin ? "Administrador" : "Cliente"}</td></tr>`)
    .join("");

  // Solo los clientes pueden hacer pedidos
  const opciones = usuarios
    .filter((u) => !u.es_admin)
    .map((u) => `<option value="${u.id}">${escapar(u.nombre)} (${escapar(u.email)})</option>`)
    .join("");
  document.getElementById("pedido-cliente").innerHTML = opciones;
  document.getElementById("consulta-cliente").innerHTML = opciones;
}

// ---------------------------------------------------------------------------
// Pedidos
// ---------------------------------------------------------------------------
function anadirLinea() {
  const linea = document.createElement("div");
  linea.className = "linea";
  linea.innerHTML = `
    <label>Producto <select required></select></label>
    <label>Cantidad <input type="number" min="1" value="1" required></label>
    <button type="button" class="quitar">Quitar</button>`;
  rellenarSelectProductos(linea.querySelector("select"));
  linea.querySelector(".quitar").addEventListener("click", () => linea.remove());
  document.getElementById("lineas-pedido").appendChild(linea);
}

document.getElementById("btn-linea").addEventListener("click", anadirLinea);

document.getElementById("form-pedido").addEventListener("submit", async (e) => {
  e.preventDefault();
  const items = [...document.querySelectorAll(".linea")].map((linea) => ({
    producto_id: linea.querySelector("select").value,
    cantidad: parseInt(linea.querySelector("input").value, 10),
  }));
  if (items.length === 0) {
    mostrarMensaje("Añade al menos un producto al pedido", "error");
    return;
  }

  const cuerpo = { cliente_id: document.getElementById("pedido-cliente").value, items };
  try {
    const pedido = await api("POST", "/pedidos", cuerpo);
    mostrarMensaje(`Pedido creado para ${pedido.cliente_nombre}. Total: ${euros(pedido.total)}`, "ok");
    document.getElementById("lineas-pedido").innerHTML = "";
    anadirLinea();
    await cargarProductos(); // el stock ha cambiado
  } catch (err) {
    mostrarMensaje(`No se pudo crear el pedido. ${err.message}`, "error");
  }
});

document.getElementById("form-consulta").addEventListener("submit", async (e) => {
  e.preventDefault();
  const clienteId = document.getElementById("consulta-cliente").value;
  const contenedor = document.getElementById("lista-pedidos");

  try {
    const pedidos = await api("GET", `/usuarios/${clienteId}/pedidos`);
    if (pedidos.length === 0) {
      contenedor.innerHTML = "<p>Este usuario no tiene pedidos.</p>";
      return;
    }
    contenedor.innerHTML = pedidos
      .map((p) => `<div class="pedido">
        <strong>${new Date(p.fecha).toLocaleString("es-ES")}</strong> · Total: ${euros(p.total)}
        <ul>${p.items
          .map((i) => `<li>${i.cantidad} × ${escapar(i.nombre)} (${euros(i.precio_unitario)}) = ${euros(i.subtotal)}</li>`)
          .join("")}</ul></div>`)
      .join("");
  } catch (err) {
    mostrarMensaje(`No se pudieron cargar los pedidos. ${err.message}`, "error");
  }
});

// ---------------------------------------------------------------------------
// Conexión con la API (la URL se puede cambiar para usar la IP de otro equipo)
// ---------------------------------------------------------------------------
async function conectar() {
  BASE_URL = document.getElementById("api-url").value.trim().replace(/\/+$/, "");
  const estado = document.getElementById("estado-api");
  try {
    await Promise.all([cargarProductos(), cargarUsuarios()]);
    estado.textContent = "✔ Conectado";
    if (document.querySelectorAll(".linea").length === 0) anadirLinea();
  } catch (err) {
    estado.textContent = "✖ Sin conexión";
    mostrarMensaje(`No se pudo conectar con ${BASE_URL}. ${err.message}`, "error");
  }
}

document.getElementById("form-api").addEventListener("submit", (e) => {
  e.preventDefault();
  conectar();
});

conectar();
