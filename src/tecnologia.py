from __future__ import annotations
from abc import ABC
from typing import List

class Technology(ABC):
    """Unidad de generación con sus propias restricciones físicas."""

    def __init__(self, nombre: str, id_P: int, capacidad_horaria: List[float], precio_marginal: float, **restricciones):
        self.nombre = nombre
        self.id_Productor = id_P
        self._capacidad_inicial = capacidad_horaria[:]  # kWh o MW según uses
        self._oferta = capacidad_horaria[:].copy()
        self.precio = precio_marginal
        self.restricciones = restricciones

    def disponible(self, h: int) -> float:
        """Energía máxima que la unidad *podría* vender en la hora *h* (antes de estrategia)."""
        return self._capacidad_inicial[h]

    def __str__(self):
        return f"{self.nombre}({self.__class__.__name__})"

    def ofertar(self, h: int, cantidad: float) -> float:
        """Reduce la capacidad disponible y devuelve la cantidad efectivamente vendida."""
        vendible = min(cantidad, self._oferta[h])
        self._oferta[h] -= vendible
        return vendible


class Solar(Technology):
    pass  


class Eolica(Technology):
    pass


class Hidraulica(Technology):
    def disponible(self, h: int) -> float:
        return super().disponible(h)


class Gas(Technology):
    def disponible(self, h: int) -> float:
        return super().disponible(h)


class Nuclear(Technology):
    def disponible(self, h: int) -> float:
        bloque = self.restricciones.get("bloque", 24)
        inicio = (h // bloque) * bloque
        return self._capacidad_inicial[inicio]