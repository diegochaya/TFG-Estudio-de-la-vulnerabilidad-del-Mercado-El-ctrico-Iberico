from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING
import pandas as pd

if TYPE_CHECKING:
    from mercado import ModeloMercado
    from productor import Productor

class Estrategia(ABC):
   
    @abstractmethod
    def generar_ofertas_df(self,productor: "Productor", df: pd.DataFrame, demanda)-> pd.DataFrame:
        """Devuelve DataFrame con ofertas"""

class EstrategiaBasica(Estrategia):
    """Ofrece todo al coste marginal."""

    def generar_ofertas(self, productor: "Productor", h: int, mercado: "ModeloMercado"):
        ofertas = []
        for unidad in productor.unidades:
            if unidad.disponible(h) > 0:
                ofertas.append(unidad)
        return ofertas
    
    def generar_ofertas_df(self,productor: "Productor", df: pd.DataFrame, demanda:List)-> pd.DataFrame:
        df_p=productor.df.copy()
        df_p["precio_oferta"]=df_p["precio_eur_mwh"]
        df_p["cantidad_oferta"]=df_p["cantidad_mw"]
        return df_p



class EstrategiaEspeculador(Estrategia):
    
    def __init__(self, coef:int=10):
        self.coef=coef

    def generar_ofertas_df(self,productor: "Productor", df_ini: pd.DataFrame, demanda_lst: List)-> pd.DataFrame:
        print(productor.id)
        df_p=productor.df.copy()
        df=df_ini.copy().sort_values(["periodo","precio_eur_mwh"])[["periodo","precio_eur_mwh","cantidad_mw", "propietario"]]
        #Añadimos la demanda
        df=df.merge(pd.DataFrame(demanda_lst, columns=['demanda'], index=range(1, len(demanda_lst)+1)),left_on="periodo", right_index=True)
        df_p=df_p.merge(pd.DataFrame(demanda_lst, columns=['demanda'], index=range(1, len(demanda_lst)+1)),left_on="periodo", right_index=True)
        #Simulacion de ofertas
        df["acum"]=df.groupby("periodo")["cantidad_mw"].cumsum()
        df["cantidad_aceptada"]=(df["demanda"]-(df["acum"]-df["cantidad_mw"]))
        
        #Energia Casada
        casado_p=df[(df["propietario"]==productor.id) & (df["cantidad_aceptada"]>0)]
        casado_sum=casado_p.groupby("periodo")["cantidad_mw"].sum().rename("cantidad_precasada")


        df=df[~((df["cantidad_aceptada"]<=0) & (df["propietario"]==productor.id))]
        df["acum"]=df.groupby("periodo")["cantidad_mw"].cumsum()
        df["cantidad_aceptada"]=(df["demanda"]-(df["acum"]-df["cantidad_mw"]))
        df=df.merge(casado_sum, left_on="periodo", right_index=True)

        #Posibles cantidades de energía que pueden casar: desde cantidad_precasada hasta 0
        df["cantidades_posibles_casamientos"] = df["cantidad_precasada"]+df["cantidad_aceptada"].clip(-df["cantidad_precasada"],0)

        
        df["beneficio"]=df["cantidades_posibles_casamientos"]*df["precio_eur_mwh"].clip(lower=0)
        idxManipulacion=df.groupby("periodo")["beneficio"].idxmax()
        cantidad_manipulada=df.loc[idxManipulacion][["periodo","cantidades_posibles_casamientos"]]        
        
        #Manipular
        df_p=df_p.merge(cantidad_manipulada, on="periodo")
        idx_periodos_man=cantidad_manipulada["cantidades_posibles_casamientos"].values!=casado_sum.values
        mascara= pd.Series(idx_periodos_man,range(1, len(demanda_lst)+1))
        filas_a_cambiar=df_p["periodo"].map(mascara)
        df_p["acum"]=df_p.groupby("periodo")["cantidad_mw"].cumsum()
        df_p["cantidad_oferta"]=df_p["cantidad_mw"].copy()
        df_p.loc[filas_a_cambiar,"cantidad_oferta"]=(
            df_p.loc[filas_a_cambiar,"cantidades_posibles_casamientos"]-1e-5-
            (df_p.loc[filas_a_cambiar,"acum"]-df_p.loc[filas_a_cambiar,"cantidad_mw"])
            ).clip(0,df_p.loc[filas_a_cambiar,"cantidad_mw"])
        df_p=df_p[df_p["cantidad_oferta"]>0]
        df_p["precio_oferta"]=df_p["precio_eur_mwh"].copy()
        """
        rar=(df_p["cantidad_aceptada"] > 0)&(df_p["cantidad_aceptada"] <=df_p["cantidad_mw"])
        df_p.loc[df_p["cantidad_aceptada"] <= 0, "precio_oferta"] *= self.coef
        df_p.loc[rar,"cantidad_oferta"] = df_p.loc[rar,"cantidad_aceptada"].copy()
        df_p = pd.concat([df_p, df_p.loc[rar].assign(cantidad_oferta=lambda d:d["cantidad_mw"]-d["cantidad_oferta"],
                                                precio_oferta=lambda d: d["precio_oferta"]*self.coef,
                                                num_tramo=99)],ignore_index=True)
        """
        
        df_p=df_p.drop(columns=["acum", "demanda"])
        return df_p




    
    

