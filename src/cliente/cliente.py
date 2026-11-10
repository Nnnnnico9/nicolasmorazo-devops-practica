"""Cliente de la API REST de la tienda online (Práctica 2 - Parte 2).

Este script es independiente del servidor: no importa TiendaService ni los
modelos. Toda la comunicación se hace con peticiones HTTP usando `requests`.

Uso:
    python cliente.py                              # usa BASE_URL
    python cliente.py http://192.168.1.34:8000     # API en otro equipo
"""

import sys
import uuid

import requests

# Dirección base de la API. Cambiarla por la IP del equipo servidor para
# probar entre dos equipos, p. ej. "http://192.168.1.34:8000".
BASE_URL = "http://localhost:8000"

TIMEOUT = 5  # segundos


def peticion(metodo, ruta, esperado, json=None, params=None):
    """Hace una petición HTTP, comprueba el código de estado y devuelve el JSON.

    Si el código no es el esperado, muestra el error devuelto por la API y
    termina el programa.
    """
    url = f"{BASE_URL}{ruta}"
    try:
        respuesta = requests.request(metodo, url, json=json, params=params, timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] No se pudo conectar con {url}: {e}")
        sys.exit(1)

    print(f"{metodo} {respuesta.url.replace(BASE_URL, '')} -> {respuesta.status_code}")
    if respuesta.status_code != esperado:
        try:
            detalle = respuesta.json().get("detail")
        except ValueError:
            detalle = respuesta.text
        print(f"[ERROR] Se esperaba {esperado}. Detalle: {detalle}")
        sys.exit(1)

    return respuesta.json()


def titulo(texto):
    print(f"\n=== {texto} ===")


def main():
    print(f"Usando la API en {BASE_URL}")

    # 1. Crear un usuario (email aleatorio para poder ejecutar el script varias veces)
    titulo("1. Crear usuario")
    sufijo = uuid.uuid4().hex[:6]
    usuario = peticion(
        "POST",
        "/usuarios",
        201,
        json={
            "nombre": f"cliente_{sufijo}",
            "email": f"cliente_{sufijo}@tiendaonline.com",
            "tipo": "cliente",
            "direccion": "Calle Prueba 1",
        },
    )
    print(f"Usuario creado: {usuario['nombre']} ({usuario['email']}) id={usuario['id']}")

    # 2. Consultar la lista de usuarios
    titulo("2. Listar usuarios")
    usuarios = peticion("GET", "/usuarios", 200)
    for u in usuarios:
        rol = "admin" if u["es_admin"] else "cliente"
        print(f"- {u['nombre']:<20} {u['email']:<35} {rol}")

    # 3. Crear varios productos
    titulo("3. Crear productos")
    nuevos = [
        {"tipo": "electronico", "nombre": "Tablet", "precio": 299.9, "stock": 5, "meses_garantia": 24},
        {"tipo": "ropa", "nombre": "Gorra", "precio": 15, "stock": 10, "talla": "U", "color": "Rojo"},
        {"tipo": "generico", "nombre": "Boli", "precio": 1.2, "stock": 100},
    ]
    creados = []
    for datos in nuevos:
        producto = peticion("POST", "/productos", 201, json=datos)
        creados.append(producto)
        print(f"Producto creado: {producto['nombre']} ({producto['tipo']}) id={producto['id']}")

    # 4. Consultar la lista de productos
    titulo("4. Listar productos")
    productos = peticion("GET", "/productos", 200)
    for p in productos:
        print(f"- {p['nombre']:<15} {p['tipo']:<12} {p['precio']:>8.2f} EUR  stock={p['stock']}")

    # 4b. Buscar productos por nombre con un parámetro de consulta (?nombre=...)
    titulo("4b. Buscar producto por nombre")
    encontrados = peticion("GET", "/productos", 200, params={"nombre": "Tablet"})
    print(f"Productos llamados 'Tablet': {len(encontrados)}")
    for p in encontrados:
        print(f"- {p['nombre']} id={p['id']} stock={p['stock']}")

    # 5. Crear un pedido para el usuario creado
    titulo("5. Crear pedido")
    pedido = peticion(
        "POST",
        "/pedidos",
        201,
        json={
            "cliente_id": usuario["id"],
            "items": [
                {"producto_id": creados[0]["id"], "cantidad": 1},
                {"producto_id": creados[1]["id"], "cantidad": 2},
            ],
        },
    )
    print(f"Pedido {pedido['id']} creado para {pedido['cliente_nombre']}. Total: {pedido['total']:.2f} EUR")

    # 6. Consultar los pedidos de ese usuario
    titulo("6. Pedidos del usuario")
    pedidos = peticion("GET", f"/usuarios/{usuario['id']}/pedidos", 200)
    for p in pedidos:
        print(f"Pedido {p['id']} ({p['fecha']}) - total {p['total']:.2f} EUR")
        for item in p["items"]:
            print(f"    {item['cantidad']} x {item['nombre']} = {item['subtotal']:.2f} EUR")

    print("\nFlujo completado correctamente.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1].rstrip("/")
    main()
