"""Modelo de pedido para la tienda online."""

import uuid
from datetime import datetime
from typing import Dict

from models.producto import Producto
from models.usuario import Cliente


class Pedido:
    """Compra realizada por un cliente con uno o varios artículos."""

    def __init__(self, cliente: Cliente, productos: Dict[Producto, int]) -> None:
        """Genera un pedido con referencia única y fecha de registro."""
        self.id: str = str(uuid.uuid4())
        self.cliente: Cliente = cliente
        self.productos: Dict[Producto, int] = productos
        self.fecha: datetime = datetime.now()

    def calcular_total(self) -> float:
        """Suma el precio de cada línea según la cantidad pedida."""
        return sum(producto.precio * cantidad for producto, cantidad in self.productos.items())

    def __str__(self) -> str:
        """Devuelve un resumen legible con cliente, fecha e importe total."""
        return (
            f"Pedido [{self.id}] para {self.cliente.nombre} - "
            f"{self.fecha:%Y-%m-%d %H:%M} - Importe total: {self.calcular_total():.2f} EUR"
        )
