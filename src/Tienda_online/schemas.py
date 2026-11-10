"""Esquemas Pydantic de la API: qué datos recibe y qué datos devuelve.

Los *Create* describen el cuerpo de las peticiones (lo que envía el cliente).
Los *Read* describen las respuestas (lo que devuelve la API).
FastAPI los usa para validar los datos automáticamente y para generar /docs.
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.pedido import Pedido
from models.producto import Producto, ProductoElectronico, ProductoRopa
from models.usuario import Usuario


# ============================================================================
# 1.1 Usuarios
# ============================================================================


class UsuarioCreate(BaseModel):
    """Datos necesarios para registrar un usuario."""

    nombre: str = Field(min_length=1, max_length=100, examples=["alejandro"])
    email: str = Field(
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", examples=["alejandro@tiendaonline.com"]
    )
    tipo: Literal["cliente", "administrador"] = Field(examples=["cliente"])
    direccion: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Dirección postal. Obligatoria para clientes.",
        examples=["Avenida Sol 12"],
    )

    @model_validator(mode="after")
    def cliente_necesita_direccion(self) -> "UsuarioCreate":
        """Un cliente debe tener dirección postal para poder recibir pedidos."""
        if self.tipo == "cliente" and not self.direccion:
            raise ValueError("La dirección postal es obligatoria para los clientes")
        return self


class UsuarioRead(BaseModel):
    """Información de un usuario devuelta por la API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    email: str
    es_admin: bool

    @classmethod
    def desde_modelo(cls, usuario: Usuario) -> "UsuarioRead":
        """Convierte un objeto Usuario del dominio en el esquema de respuesta."""
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            es_admin=usuario.is_admin(),
        )


# ============================================================================
# 1.2 Productos
# ============================================================================

TipoProducto = Literal["generico", "electronico", "ropa"]


class ProductoCreate(BaseModel):
    """Datos para dar de alta un producto. Los campos extra dependen del tipo."""

    tipo: TipoProducto = Field(examples=["electronico"])
    nombre: str = Field(min_length=1, max_length=100, examples=["Portátil Pro"])
    precio: float = Field(gt=0, examples=[899.99])
    stock: int = Field(ge=0, examples=[10])
    meses_garantia: Optional[int] = Field(
        default=None, gt=0, description="Solo para electrónicos.", examples=[24]
    )
    talla: Optional[str] = Field(default=None, min_length=1, description="Solo para ropa.")
    color: Optional[str] = Field(default=None, min_length=1, description="Solo para ropa.")

    @model_validator(mode="after")
    def validar_atributos_por_tipo(self) -> "ProductoCreate":
        """Comprueba que cada tipo lleve sus atributos y no los de otro tipo."""
        if self.tipo == "electronico":
            if self.meses_garantia is None:
                raise ValueError("Un producto electrónico necesita 'meses_garantia'")
            if self.talla is not None or self.color is not None:
                raise ValueError("Un producto electrónico no admite 'talla' ni 'color'")
        elif self.tipo == "ropa":
            if self.talla is None or self.color is None:
                raise ValueError("Un producto de ropa necesita 'talla' y 'color'")
            if self.meses_garantia is not None:
                raise ValueError("Un producto de ropa no admite 'meses_garantia'")
        else:  # generico
            if any(v is not None for v in (self.meses_garantia, self.talla, self.color)):
                raise ValueError(
                    "Un producto genérico no admite 'meses_garantia', 'talla' ni 'color'"
                )
        return self

    def a_modelo(self) -> Producto:
        """Construye el objeto de dominio (Producto, ProductoElectronico o ProductoRopa)."""
        if self.tipo == "electronico":
            return ProductoElectronico(self.nombre, self.precio, self.stock, self.meses_garantia)
        if self.tipo == "ropa":
            return ProductoRopa(self.nombre, self.precio, self.stock, self.talla, self.color)
        return Producto(self.nombre, self.precio, self.stock)


class ProductoRead(BaseModel):
    """Información de un producto devuelta por la API."""

    id: str
    tipo: TipoProducto
    nombre: str
    precio: float
    stock: int
    meses_garantia: Optional[int] = None
    talla: Optional[str] = None
    color: Optional[str] = None

    @classmethod
    def desde_modelo(cls, producto: Producto) -> "ProductoRead":
        """Convierte un objeto Producto (o subclase) en el esquema de respuesta."""
        datos = dict(
            id=producto.id,
            nombre=producto.nombre,
            precio=producto.precio,
            stock=producto.stock,
        )
        if isinstance(producto, ProductoElectronico):
            return cls(tipo="electronico", meses_garantia=producto.meses_garantia, **datos)
        if isinstance(producto, ProductoRopa):
            return cls(tipo="ropa", talla=producto.talla, color=producto.color, **datos)
        return cls(tipo="generico", **datos)


# ============================================================================
# 1.3 Pedidos
# ============================================================================


class PedidoItemCreate(BaseModel):
    """Una línea del pedido: qué producto y cuántas unidades."""

    producto_id: str
    cantidad: int = Field(gt=0, examples=[1])


class PedidoCreate(BaseModel):
    """Datos para crear un pedido."""

    cliente_id: str
    items: List[PedidoItemCreate] = Field(min_length=1)


class PedidoItemRead(BaseModel):
    """Una línea de un pedido ya creado."""

    producto_id: str
    nombre: str
    precio_unitario: float
    cantidad: int
    subtotal: float


class PedidoRead(BaseModel):
    """Pedido completo devuelto por la API."""

    id: str
    fecha: datetime
    cliente_id: str
    cliente_nombre: str
    total: float
    items: List[PedidoItemRead]

    @classmethod
    def desde_modelo(cls, pedido: Pedido) -> "PedidoRead":
        """Convierte un objeto Pedido del dominio en el esquema de respuesta."""
        items = [
            PedidoItemRead(
                producto_id=producto.id,
                nombre=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=cantidad,
                subtotal=round(producto.precio * cantidad, 2),
            )
            for producto, cantidad in pedido.productos.items()
        ]
        return cls(
            id=pedido.id,
            fecha=pedido.fecha,
            cliente_id=pedido.cliente.id,
            cliente_nombre=pedido.cliente.nombre,
            total=round(pedido.calcular_total(), 2),
            items=items,
        )
