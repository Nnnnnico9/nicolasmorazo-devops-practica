"""Punto de entrada de la API REST de la tienda online (capa de exposición).

Aquí solo se definen los endpoints: reciben los datos validados por los
esquemas Pydantic, llaman a TiendaService (que contiene la lógica de negocio)
y traducen el resultado o los errores a respuestas HTTP.

Ejecutar desde la carpeta Tienda_online:
    uvicorn main:app --reload
y abrir http://127.0.0.1:8000 (frontend) o http://127.0.0.1:8000/docs (Swagger)

Para aceptar conexiones de otros equipos de la red:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.producto import Producto, ProductoElectronico, ProductoRopa
from schemas import (
    PedidoCreate,
    PedidoRead,
    ProductoCreate,
    ProductoRead,
    UsuarioCreate,
    UsuarioRead,
)
from services.tienda_service import (
    EmailDuplicado,
    ProductoNoEncontrado,
    StockInsuficiente,
    TiendaService,
    UsuarioNoEncontrado,
    UsuarioNoEsCliente,
)

app = FastAPI(
    title="Tienda Online API",
    description="API REST de la tienda online construida sobre TiendaService (Práctica 2).",
    version="1.0.0",
)

# CORS: permite que el frontend (abierto en el navegador desde otro origen,
# p. ej. file:// o http://localhost:5500) pueda hacer peticiones a la API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Una única instancia del servicio para toda la aplicación (datos en memoria).
tienda = TiendaService()


def cargar_datos_ejemplo(servicio: TiendaService) -> None:
    """Carga los mismos datos de ejemplo que la Práctica 1 para poder probar la API."""
    servicio.registrar_usuario(
        "cliente", nombre="alejandro", email="alejandro@tiendaonline.com", direccion="Avenida Sol 12"
    )
    servicio.registrar_usuario(
        "cliente", nombre="sofia", email="sofia@tiendaonline.com", direccion="Calle Luna 45"
    )
    servicio.registrar_usuario("administrador", nombre="marta", email="marta@tiendaonline.com")

    servicio.agregar_producto(ProductoElectronico("Portátil Pro", 899.99, 10, meses_garantia=24))
    servicio.agregar_producto(ProductoElectronico("Smartphone X", 499.99, 15, meses_garantia=12))
    servicio.agregar_producto(ProductoRopa("Sudadera", 29.99, 35, talla="M", color="Negro"))
    servicio.agregar_producto(ProductoRopa("Vaquero", 44.99, 22, talla="L", color="Azul"))
    servicio.agregar_producto(Producto("Cuaderno", 12.50, 18))


cargar_datos_ejemplo(tienda)


# ============================================================================
# Usuarios
# ============================================================================


@app.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
    responses={409: {"description": "Ya existe un usuario con ese email"}},
)
def crear_usuario(datos: UsuarioCreate) -> UsuarioRead:
    """Crea un nuevo usuario (cliente o administrador)."""
    try:
        usuario = tienda.registrar_usuario(
            datos.tipo, nombre=datos.nombre, email=datos.email, direccion=datos.direccion
        )
    except EmailDuplicado as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return UsuarioRead.desde_modelo(usuario)


@app.get("/usuarios", response_model=List[UsuarioRead], tags=["Usuarios"])
def listar_usuarios(nombre: Optional[str] = None) -> List[UsuarioRead]:
    """Devuelve la lista de usuarios. Con `?nombre=...` filtra por nombre exacto."""
    return [UsuarioRead.desde_modelo(u) for u in tienda.listar_usuarios(nombre)]


@app.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioRead,
    tags=["Usuarios"],
    responses={404: {"description": "Usuario no encontrado"}},
)
def obtener_usuario(usuario_id: str) -> UsuarioRead:
    """Devuelve un usuario concreto."""
    try:
        usuario = tienda.obtener_usuario(usuario_id)
    except UsuarioNoEncontrado as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return UsuarioRead.desde_modelo(usuario)


@app.get(
    "/usuarios/{cliente_id}/pedidos",
    response_model=List[PedidoRead],
    tags=["Pedidos"],
    responses={
        404: {"description": "Cliente no encontrado"},
        400: {"description": "El usuario no es un cliente"},
    },
)
def listar_pedidos_cliente(cliente_id: str) -> List[PedidoRead]:
    """Devuelve el historial de pedidos de un cliente, ordenado por fecha."""
    try:
        pedidos = tienda.listar_pedidos_usuario(cliente_id)
    except UsuarioNoEncontrado as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UsuarioNoEsCliente as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return [PedidoRead.desde_modelo(p) for p in pedidos]


# ============================================================================
# Productos
# ============================================================================


@app.post(
    "/productos",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
)
def crear_producto(datos: ProductoCreate) -> ProductoRead:
    """Crea un producto genérico, electrónico o de ropa según el campo `tipo`."""
    producto = tienda.agregar_producto(datos.a_modelo())
    return ProductoRead.desde_modelo(producto)


@app.get("/productos", response_model=List[ProductoRead], tags=["Productos"])
def listar_productos(nombre: Optional[str] = None) -> List[ProductoRead]:
    """Devuelve los productos del catálogo. Con `?nombre=...` filtra por nombre exacto."""
    return [ProductoRead.desde_modelo(p) for p in tienda.listar_productos(nombre)]


@app.get(
    "/productos/{producto_id}",
    response_model=ProductoRead,
    tags=["Productos"],
    responses={404: {"description": "Producto no encontrado"}},
)
def obtener_producto(producto_id: str) -> ProductoRead:
    """Devuelve un producto concreto."""
    try:
        producto = tienda.obtener_producto(producto_id)
    except ProductoNoEncontrado as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return ProductoRead.desde_modelo(producto)


@app.delete(
    "/productos/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Productos"],
    responses={404: {"description": "Producto no encontrado"}},
)
def eliminar_producto(producto_id: str) -> Response:
    """Elimina un producto del catálogo."""
    if not tienda.eliminar_producto(producto_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el producto {producto_id}",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================================
# Pedidos
# ============================================================================


@app.post(
    "/pedidos",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Pedidos"],
    responses={
        404: {"description": "Cliente o producto no encontrado"},
        400: {"description": "El usuario no es un cliente"},
        409: {"description": "Stock insuficiente"},
    },
)
def crear_pedido(datos: PedidoCreate) -> PedidoRead:
    """Crea un pedido comprobando el cliente, los productos y el stock disponible."""
    # Si el mismo producto aparece en varias líneas, se suman las cantidades.
    cantidades: Dict[str, int] = {}
    for item in datos.items:
        cantidades[item.producto_id] = cantidades.get(item.producto_id, 0) + item.cantidad

    try:
        pedido = tienda.realizar_pedido(datos.cliente_id, cantidades)
    except (UsuarioNoEncontrado, ProductoNoEncontrado) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UsuarioNoEsCliente as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockInsuficiente as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return PedidoRead.desde_modelo(pedido)


# ============================================================================
# Frontend
# ============================================================================

# Si existe la carpeta frontend (al mismo nivel que Tienda_online), se sirve en
# la raíz (http://localhost:8000). Se monta al final para que las rutas de la
# API definidas arriba tengan prioridad. Sin ella, la API funciona igual.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
