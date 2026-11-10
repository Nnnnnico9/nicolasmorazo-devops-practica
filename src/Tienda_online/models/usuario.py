"""Modelos de usuarios para la tienda online."""

import uuid


class Usuario:
    """Persona que participa en la operativa de la tienda."""

    def __init__(self, nombre: str, email: str) -> None:
        """Genera un usuario con un código único y sus datos básicos."""
        self.id: str = str(uuid.uuid4())
        self.nombre: str = nombre
        self.email: str = email

    def is_admin(self) -> bool:
        """Indica si el perfil tiene permisos de administración."""
        return False

    def __str__(self) -> str:
        """Devuelve la descripción principal del usuario."""
        return f"[{self.id}] {self.nombre} ({self.email})"


class Cliente(Usuario):
    """Usuario con capacidad para comprar en la plataforma."""

    def __init__(self, nombre: str, email: str, direccion: str) -> None:
        """Añade la dirección de envío del cliente."""
        super().__init__(nombre, email)
        self.direccion: str = direccion

    def __str__(self) -> str:
        """Devuelve también la dirección del cliente."""
        return f"{super().__str__()} - Dirección: {self.direccion}"


class Administrador(Usuario):
    """Perfil encargado del control del catálogo y la gestión."""

    def is_admin(self) -> bool:
        """Los administradores tienen permisos especiales por defecto."""
        return True
