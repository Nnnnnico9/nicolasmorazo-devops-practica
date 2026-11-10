"""Servicio principal que gestiona usuarios, stock y pedidos de la tienda."""

from typing import Dict, List, Optional

from models.pedido import Pedido
from models.producto import Producto
from models.usuario import Administrador, Cliente, Usuario


# --- Excepciones de negocio -------------------------------------------------
# El servicio no sabe nada de HTTP: solo indica qué ha fallado. Es main.py
# quien traduce cada error al código HTTP adecuado (404, 409, 400...).


class TiendaError(Exception):
    """Error base de la lógica de la tienda."""


class UsuarioNoEncontrado(TiendaError):
    """No existe ningún usuario con el identificador indicado."""


class UsuarioNoEsCliente(TiendaError):
    """El usuario existe pero no es un cliente (por ejemplo, es administrador)."""


class EmailDuplicado(TiendaError):
    """Ya hay un usuario registrado con ese email."""


class ProductoNoEncontrado(TiendaError):
    """No existe ningún producto con el identificador indicado."""


class StockInsuficiente(TiendaError):
    """No hay unidades suficientes de un producto para servir el pedido."""


# --- Servicio ---------------------------------------------------------------


class TiendaService:
    """Se encarga de conectar la lógica de la tienda con los modelos de datos."""

    def __init__(self) -> None:
        """Inicializa los registros internos de clientes, productos y compras."""
        self.usuarios: Dict[str, Usuario] = {}
        self.productos: Dict[str, Producto] = {}
        self.pedidos: List[Pedido] = []

    # ---------- Usuarios ----------

    def registrar_usuario(self, tipo: str, **atributos: str) -> Usuario:
        """Crea un nuevo usuario según el tipo indicado: cliente o administrador."""
        email = atributos.get("email", "").lower()
        if any(u.email.lower() == email for u in self.usuarios.values()):
            raise EmailDuplicado(f"Ya existe un usuario con el email {email}")

        if tipo == "cliente":
            usuario: Usuario = Cliente(**atributos)
        elif tipo == "administrador":
            atributos.pop("direccion", None)  # un administrador no tiene dirección
            usuario = Administrador(**atributos)
        else:
            raise ValueError(f"Tipo de usuario no válido: {tipo}")

        self.usuarios[usuario.id] = usuario
        return usuario

    def obtener_usuario(self, usuario_id: str) -> Usuario:
        """Devuelve un usuario por su id o lanza UsuarioNoEncontrado."""
        usuario = self.usuarios.get(usuario_id)
        if usuario is None:
            raise UsuarioNoEncontrado(f"No existe el usuario {usuario_id}")
        return usuario

    def listar_usuarios(self, nombre: Optional[str] = None) -> List[Usuario]:
        """Devuelve los usuarios registrados; si se indica `nombre`, solo los que se llaman así."""
        usuarios = list(self.usuarios.values())
        if nombre is not None:
            usuarios = [u for u in usuarios if u.nombre == nombre]
        return usuarios

    # ---------- Productos ----------

    def agregar_producto(self, producto: Producto) -> Producto:
        """Añade un producto al inventario si ya está construido."""
        self.productos[producto.id] = producto
        return producto

    def obtener_producto(self, producto_id: str) -> Producto:
        """Devuelve un producto por su id o lanza ProductoNoEncontrado."""
        producto = self.productos.get(producto_id)
        if producto is None:
            raise ProductoNoEncontrado(f"No existe el producto {producto_id}")
        return producto

    def eliminar_producto(self, producto_id: str) -> bool:
        """Elimina un artículo del catálogo a partir de su identificador."""
        return self.productos.pop(producto_id, None) is not None

    def listar_productos(self, nombre: Optional[str] = None) -> List[Producto]:
        """Devuelve los productos del catálogo; si se indica `nombre`, solo los que se llaman así."""
        productos = list(self.productos.values())
        if nombre is not None:
            productos = [p for p in productos if p.nombre == nombre]
        return productos

    # ---------- Pedidos ----------

    def _obtener_cliente(self, usuario_id: str) -> Cliente:
        """Devuelve el usuario si existe y es cliente; si no, lanza el error que toque."""
        usuario = self.obtener_usuario(usuario_id)
        if not isinstance(usuario, Cliente):
            raise UsuarioNoEsCliente(f"El usuario {usuario_id} no es un cliente")
        return usuario

    def realizar_pedido(self, usuario_id: str, cantidades: Dict[str, int]) -> Pedido:
        """Comprueba la existencia del cliente, de los productos y el stock antes de registrar la compra.

        Primero se valida todo el pedido y solo después se descuenta el stock,
        de forma que si una línea falla no se modifica ningún producto.
        """
        cliente = self._obtener_cliente(usuario_id)

        productos_pedido: Dict[Producto, int] = {}
        for producto_id, cantidad in cantidades.items():
            producto = self.obtener_producto(producto_id)
            if not producto.hay_stock(cantidad):
                raise StockInsuficiente(
                    f"Stock insuficiente de '{producto.nombre}': "
                    f"pedidas {cantidad}, disponibles {producto.stock}"
                )
            productos_pedido[producto] = cantidad

        for producto, cantidad in productos_pedido.items():
            producto.actualizar_stock(-cantidad)

        pedido = Pedido(cliente, productos_pedido)
        self.pedidos.append(pedido)
        return pedido

    def listar_pedidos_usuario(self, usuario_id: str) -> List[Pedido]:
        """Muestra los pedidos realizados por un cliente, ordenados por fecha."""
        self._obtener_cliente(usuario_id)
        pedidos_usuario = [pedido for pedido in self.pedidos if pedido.cliente.id == usuario_id]
        return sorted(pedidos_usuario, key=lambda pedido: pedido.fecha)
