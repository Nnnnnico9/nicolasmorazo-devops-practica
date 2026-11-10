"""Modelos de productos para la tienda online."""

import uuid


class Producto:
    """Artículo básico disponible en el catálogo."""

    def __init__(self, nombre: str, precio: float, stock: int) -> None:
        """Genera un producto con un identificador único y datos principales."""
        self.id: str = str(uuid.uuid4())
        self.nombre: str = nombre
        self.precio: float = precio
        self.stock: int = stock

    def hay_stock(self, cantidad: int) -> bool:
        """Comprueba si existe suficiente inventario para la cantidad indicada."""
        return self.stock >= cantidad

    def actualizar_stock(self, cantidad: int) -> None:
        """Modifica el stock: valores positivos añaden unidades y negativos las quitan."""
        self.stock += cantidad

    def __str__(self) -> str:
        """Devuelve una representación clara del producto."""
        return f"[{self.id}] {self.nombre} - {self.precio:.2f} EUR (stock: {self.stock})"


class ProductoElectronico(Producto):
    """Producto tecnológico con periodo de garantía."""

    def __init__(self, nombre: str, precio: float, stock: int, meses_garantia: int) -> None:
        """Añade la garantía de un producto electrónico a la base del artículo."""
        super().__init__(nombre, precio, stock)
        self.meses_garantia: int = meses_garantia

    def __str__(self) -> str:
        """Incluye la información de garantía en la vista del producto."""
        return f"{super().__str__()} - Garantía: {self.meses_garantia} meses"


class ProductoRopa(Producto):
    """Artículo de ropa con datos de talla y color."""

    def __init__(self, nombre: str, precio: float, stock: int, talla: str, color: str) -> None:
        """Extiende el producto con características específicas de la prenda."""
        super().__init__(nombre, precio, stock)
        self.talla: str = talla
        self.color: str = color

    def __str__(self) -> str:
        """Muestra la información básica junto a talla y color."""
        return f"{super().__str__()} - Talla: {self.talla}, Color: {self.color}"
