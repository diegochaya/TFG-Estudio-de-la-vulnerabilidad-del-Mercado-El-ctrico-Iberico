from __future__ import annotations
from typing import List, TYPE_CHECKING
from tecnologia import Technology
from estrategia import Estrategia, EstrategiaBasica
import pandas as pd

if TYPE_CHECKING:                          
    from mercado import ModeloMercado

class Productor:
    """Empaqueta ofertas y delega la lógica a una *Estrategia*."""

    def __init__(self, id_: int | str, unidades: List[Technology]=[], estrategia: Estrategia=EstrategiaBasica()):
        self.id = id_
        self.unidades = unidades
        self.estrategia = estrategia
        self.beneficio = 0.0
        self.df=pd.DataFrame()

    # ------------------------------------------------------------------
    def ofertas_hora(self, h: int, mercado: "ModeloMercado"):
        return self.estrategia.generar_ofertas(self, h, mercado)

    # ------------------------------------------------------------------
    def escribir_ofertas(self, df_ini:pd.DataFrame, df_of: pd.DataFrame, demanda=List):
        return pd.concat([df_of,self.estrategia.generar_ofertas_df(self,df_ini, demanda)],ignore_index=True).copy()
    
    # ------------------------------------------------------------------
    def __str__(self):
        return f"Productor {self.id}"
