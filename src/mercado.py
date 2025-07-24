import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pulp
from typing import List, Tuple, Dict, Sequence
from productor import Productor
from tecnologia import Technology, Solar, Eolica, Hidraulica, Gas, Nuclear 
from estrategia  import EstrategiaBasica, EstrategiaEspeculador




class ModeloMercado:

    def __init__(self, demandas_horarias: List[float]=[], fecha:str=""):
        self.demandas_horarias = demandas_horarias
        self.productores: List[Productor] = []
        self.precio_marginal = []
        self.fecha=fecha
        self.df_of=pd.DataFrame()
        self.df_ini=pd.DataFrame()
        self.of_cas=pd.DataFrame()

    # ------------------------------------------------------------------
    def iniciar_mercado_df(self,ofertas: pd.DataFrame, lst_especulador:List) -> None:   
        self.df_ini=ofertas.copy()
        self.lst_especulador=lst_especulador
        totales = (self.df_ini
           .groupby("propietario", sort=False)["cantidad_mw"]
           .sum().sort_values(ascending=False)) 
        for i,id_p in enumerate(totales.index):
            if i in lst_especulador:
                p=Productor(id_p,estrategia=EstrategiaEspeculador())
            else:
                p=Productor(id_p,estrategia=EstrategiaBasica())
            p.df = self.df_ini[self.df_ini["propietario"] == id_p].copy()
            self.productores.append(p)


        
    def recoger_ofertas_productores(self):
        for p in self.productores:
            self.df_of=p.escribir_ofertas(self.df_ini,self.df_of, self.demandas_horarias)
    
    def simular_df_simple(self):
        self.recoger_ofertas_productores()
        self.df_of=self.df_of.sort_values(["periodo","precio_oferta"])
        self.df_of=self.df_of.merge(pd.DataFrame(self.demandas_horarias, columns=['demanda'], index=range(1, len(self.demandas_horarias)+1)),left_on="periodo", right_index=True)
        self.df_of["acum"]=self.df_of.groupby("periodo")["cantidad_oferta"].cumsum()
        self.df_of["cantidad_aceptada"]=(self.df_of["demanda"]-(self.df_of["acum"]-self.df_of["cantidad_oferta"])).clip(0,self.df_of["cantidad_oferta"])
        

        #Calcular la Casada
        self.df_of=self.df_of.drop(["acum", "demanda"], axis=1)
        self.of_cas=self.df_of[self.df_of["cantidad_aceptada"]>0].copy()
        self.precio_marginal=self.of_cas.groupby("periodo")["precio_oferta"].max()
        self.of_cas["precio_marginal"] = self.of_cas["periodo"].map(self.precio_marginal)
        
       


    # ──────────────────────────────────────────────────────────

    def grafico_ventas_apiladas(self, figsize=(12, 6), **kwargs):
        mapa = {
            "RE Mercado Solar Fotovoltáica": "Solar",
            "RE Mercado Solar Térmica": "Solar",
            "RE Tar. CUR Solar Fotovoltáica": "Solar",
            "RE Mercado Eólica": "Eólica",
            "Nuclear": "Nuclear",
            "Hidráulica Generación": "Hidráulica",
            "RE Mercado Hidráulica": "Hidráulica",
            "Hidráulica de Bombeo Puro": "Hidráulica",
            "Ciclo Combinado": "Ciclo combinado",
            "Import. de agentes externos": "Importaciones"
        }
        self.of_cas["fuente"] = self.of_cas["tipo_energia"].map(mapa).fillna("Otros")
        orden = ["Eólica", "Solar", "Hidráulica", "Nuclear", 
         "Ciclo combinado", "Importaciones", "Otros"]
        df_plot = (self.of_cas.groupby(["periodo", "fuente"])["cantidad_aceptada"]
                        .sum()
                        .unstack(fill_value=0)
                        .sort_index())
        df_plot = df_plot.reindex(columns=orden)
        ax=df_plot.plot(kind="bar", stacked=True, figsize=(14, 6))
        ax.plot(ax.get_xticks(), self.demandas_horarias, marker="o", linewidth=2, label="Demanda OMIE")
        ax.set_xlabel("Hora")
        ax.set_ylabel("MW ofertados")
        ax.set_title("Oferta horaria por tecnología")
        plt.tight_layout()
        plt.savefig(f"outputs/Valid/Energias_Simu_mix_{self.fecha}.png", dpi=150, bbox_inches="tight")

        return df_plot

    def resultados(self):
        print("\n=== RESULTADOS ===")
        self.of_cas["beneficio"]=self.of_cas["cantidad_aceptada"]*self.of_cas["precio_marginal"]
        print(f"beneficio total = {self.of_cas['beneficio'].sum()} €")
        for p_id, p_df in (self.of_cas.groupby("propietario")["beneficio"].sum().sort_values(ascending=False)).head(7).items():
            print(f"{p_id}: beneficio total = {p_df:.2f} €")
        
    # ---------------------------------------------------------------
    
    def grafico_precio(self, fname="outputs/Simu/Precio_Simu_Marginal.png", marg=None):
        plt.figure()
        plt.plot(self.precio_marginal.values, label="Precio Marginal")
        if marg: plt.plot(marg, label="Precio Marginal OMIE")
        plt.legend()
        plt.savefig(fname, dpi=150)


    def simular_df_pulp(self,big_M: float = 1e6):
        """Resolve la casación de un día completo (24 h) con restricciones de bloques
        y ratio MAR usando PuLP.

        ofertas_df : pd.DataFrame
            DataFrame con la estructura:
            ['cod_oferta', 'periodo', 'num_block', 'num_tramo', 'num_grupo_excl',
            'precio_eur_mwh', 'cantidad_mw', 'mav_mw', 'mar_ratio', 'cod_uo', 'cv',
            'max_pot', 'descripcion', 'propietario', 'porcentaje', 'tipo_unidad',
            'pais', 'tipo_energia']"""
        self.recoger_ofertas_productores()
        ofertas_df = self.df_of.copy()

        # --- Validaciones básicas -------------------------------------------------
        required_cols = {
            'cod_oferta', 'periodo', 'precio_eur_mwh', 'cantidad_mw',
            'num_block', 'mar_ratio', 'num_grupo_excl'
        }

        # --- Pre-procesado de ofertas ---------------------------------------------
        missing = required_cols - set(ofertas_df.columns)
        if missing:
            raise ValueError(f"Faltan columnas en ofertas_df: {missing}")
        
        ofertas_df['mar_ratio'] = ofertas_df['mar_ratio'].fillna(0)
        ofertas_df['num_block'] = ofertas_df['num_block'].fillna(0).astype(int)
        ofertas_df['num_grupo_excl'] = ofertas_df['num_grupo_excl'].fillna(0).astype(int)
        ofertas_df = ofertas_df.dropna(subset=['precio_eur_mwh', 'cantidad_mw'])
        ofertas_df = ofertas_df[ofertas_df['cantidad_mw'] > 0]
        #ofertas_df = ofertas_df[ofertas_df['mav_mw'] < ofertas_df['cantidad_mw']]


        # Convertir periodo → int 0‑23 para indexar demanda

        #ofertas_df=ofertas_df[(ofertas_df["num_block"]==0) & (ofertas_df["mav_mw"]==0)]
        ofertas_df['periodo'] = ofertas_df['periodo'].astype(int) - 1 

        # --- Crear problema MILP --------------------------------------------------
        prob = pulp.LpProblem("CasacionMercado", pulp.LpMinimize)

        # VARIABLES ---------------------------------------------------------------
        # Fracción aceptada por tramo (0‑1). Continua por defecto.
        frac: Dict[int, pulp.LpVariable] = {
            idx: pulp.LpVariable(f"x_{idx}", lowBound=0, upBound=1, cat="Continuous")
            for idx in ofertas_df.index
        }

        # Variables binarias de bloque (para ofertas con num_block > 0 o mar_ratio >= 1)
        # Clave: id_block (cod_oferta o num_block? -> agrupamos por cod_oferta)
        blocks: Dict[int, Dict[int,pulp.LpVariable]] = {}

        for cod, sub in ofertas_df.groupby('cod_oferta'):
            if (sub['num_block'] > 0).any():
                blocks[cod]={}
                excl={}
                for cod2, sub2 in ofertas_df.groupby('num_block'):
                    if cod2!=0:
                        y = pulp.LpVariable(f"b_{cod}_{cod2}", cat="Binary")
                        blocks[cod][cod2]=y
                        for idx in sub2.index: 
                            mar=sub2.loc[idx,"mar_ratio"]
                            if mar==1 or mar==0:                      
                                prob+= frac[idx]==y
                            else:
                                prob+=frac[idx]<=y
                                prob+=frac[idx]>=y*mar
                        num_excl=sub2["num_grupo_excl"].mode().iloc[0]
                        if num_excl>0:
                            excl.setdefault(num_excl, []).append(y)
                for lst in excl.values():
                    prob+=pulp.lpSum(lst)<=1


        deficit = {
            h: pulp.LpVariable(f"deficit_{h}", lowBound=0, cat="Continuous")
            for h in range(24)
        }

        #Ofertas MAV
        for idx in ofertas_df.index:
            if ofertas_df.loc[idx,"mav_mw"]>0:
                y=pulp.LpVariable(f"b_{idx}", cat="Binary")
                prob+=frac[idx]*ofertas_df.loc[idx,"cantidad_mw"]>=ofertas_df.loc[idx,"mav_mw"]*y
                prob+=frac[idx]<=y

        # OBJETIVO ---------------------------------------------------------------
        cost = pulp.lpSum(
            ofertas_df.loc[idx, 'precio_eur_mwh'] * ofertas_df.loc[idx, 'cantidad_mw'] * frac[idx]
            for idx in ofertas_df.index
        ) + big_M * pulp.lpSum(deficit[h] for h in range(24))
        prob += cost

        # RESTRICCIONES DE BALANCE ------------------------------------------------
        for h in range(24):
            ofertas_h = ofertas_df[ofertas_df['periodo'] == h]
            prob += (
                pulp.lpSum(ofertas_h.loc[idx, 'cantidad_mw'] * frac[idx] for idx in ofertas_h.index)
                + deficit[h] == self.demandas_horarias[h]
            ), f"Balance_h_{h}"


        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        status = pulp.LpStatus[prob.status]

        # --- Post‑procesado -------------------------------------------------------
        self.df_of['frac_aceptada'] = [frac[idx].value() if prob.status == 1 else 0 for idx in ofertas_df.index]
        self.df_of['cantidad_aceptada'] = self.df_of['frac_aceptada'] * ofertas_df['cantidad_mw']
        self.df_of.drop(columns="frac_aceptada")

        self.of_cas=self.df_of[self.df_of["cantidad_aceptada"]>0]
        self.precio_marginal=self.of_cas.groupby("periodo")["precio_oferta"].max()
        self.of_cas["precio_marginal"] = self.of_cas["periodo"].map(self.precio_marginal)
        return self.df_of, pulp.value(prob.objective), status















    #Modelo sin DataFrame
    # ───────────────────────────────────────────────────────────────
    # ───────────────────────────────────────────────────────────────
    # ───────────────────────────────────────────────────────────────

    def get_productor(self, id_: int) -> Productor:
        for p in self.productores:
            if p.id == id_:
                return p
        raise ValueError(f"No existe el productor {id_}")
    
    def simular(self, verbose:bool=False):
        print("\n=== SIMULACIÓN MERCADO ===")
        for h, demanda in enumerate(self.demandas_horarias):
            print(f"\nHora {h:02d} – Demanda = {demanda} MW")
            demanda_restante = demanda

            # 1) Recopilar ofertas
            ofertas = []
            for p in self.productores:
                ofertas.extend(p.ofertas_hora(h, self))
            ofertas.sort(key=lambda x: x.precio)  # ordenar por precio

            # 2) Casar demanda – listado de (prod, unidad, vendido, precio)
            ventas: List[Tuple[Technology, float]] = []
            for unidad in ofertas:
                if demanda_restante <= 0:
                    break
                vendido = unidad.ofertar(h, demanda_restante)
                if vendido > 0:
                    ventas.append((unidad, vendido))
                    demanda_restante -= vendido

            self.ventas_por_hora.append(ventas)

            if demanda_restante > 0:
                print(f"Demanda no cubierta: {demanda_restante} MW")

            # 3) Liquidar: precio = más caro casado + colchón
            if ventas:
                precio_clear = ventas[-1][0].precio
                self.precio_marg_lst.append(precio_clear)
                print(f"Precio de casación: {precio_clear:.2f} €/MWh")
                for unidad, q in ventas:
                    beneficio_venta = q * precio_clear
                    self.get_productor(unidad.id_Productor).beneficio += beneficio_venta
                    if verbose:
                        print(f"  • Productor {unidad.id_Productor} vende {q:.1f} MW de {unidad} a {unidad.precio} ⇒ Benef. {beneficio_venta:.1f}")

    def iniciar_mercado_simple_df(
            self,
            ofertas: pd.DataFrame,
            sample_n: int | None = None,      # nº máx. de productores 
            verbose: bool = False
    ) -> None:
        
        

        # -------------------------------------------------- 1) mapeo tipo_energia → clase
        def _clase_para(tipo: str):
            t = tipo.lower()
            if "solar" in t:
                return Solar
            if "eólic" in t or "eolic" in t:
                return Eolica
            if "hidrául" in t or "hidraul" in t:
                return Hidraulica
            if "nuclear" in t:
                return Nuclear
            if "ciclo combinado" in t or "ccgt" in t or "gas" in t:
                return Gas
            # resto (carbón, genéricas, híbridas, geotérmica, import…) → Gas
            return Gas

        
        ofertas=ofertas[(ofertas["num_block"]==0) & (ofertas["mav_mw"]==0)& (ofertas["num_grupo_excl"]==0) & (ofertas["mar_ratio"]==0)]
        # -------------------------------------------------- 2) ordenar productores por energía ↓
        
        ranking = (
            ofertas.groupby("propietario")["cantidad_mw"]
            .sum()
            .sort_values(ascending=False)
        )

        propietarios = ranking.index.tolist()
        if sample_n:
            propietarios = propietarios[:sample_n]

        # -------------------------------------------------- 3) crear productores y unidades
        for id_prod, propietario in enumerate(propietarios, start=1):
            df_p = ofertas[ofertas["propietario"] == propietario]
            unidades: List[Technology] = []
            group_cols = ["cod_oferta", "cod_uo", "num_tramo",
                          "tipo_energia", "precio_eur_mwh"]

            for key, grp in df_p.groupby(group_cols):
                cod_oferta, cod_uo, num_tramo, tipo_en, precio = key
                capacidad = [0.0] * 24
                for _, fila in grp.iterrows():
                    h = int(fila["periodo"]) - 1                   # 0-based
                    if 0 <= h < 24:
                        capacidad[h] += float(fila["cantidad_mw"])

                cls = _clase_para(tipo_en)
                nombre = f"{cod_oferta}_{num_tramo}"
                unidades.append(cls(nombre, id_prod, capacidad, float(precio)))
            P=Productor(id_prod, unidades, EstrategiaBasica())
            self.agregar_productor(P)
            P.df=df_p

            if verbose:
                print(f"✔ Productor {id_prod:>3}  {propietario[:40]:40s} "
                      f"→ {len(unidades):>2} unidades  "
                      f"(energía={ranking[propietario]:.0f} MW)")


    def graficos_por_productor(self, figsize=(12, 6),
                               orden_tec=("Eolica", "Solar", "Nuclear", "Hidraulica", "Gas"),
                               **kwargs):
        """
        Recorre todos los productores y pinta, para cada uno:
          – barras apiladas por tecnología (orden fijo)
          – línea de energía acumulada (eje secundario)
        Parámetros extra (**kwargs) se pasan a DataFrame.plot().
        Devuelve un dict {id_prod: DataFrame} con los datos de cada productor.
        """
        if not self.ventas_por_hora:
            raise RuntimeError("¡Primero ejecuta simular()!")

        resultados = {}
        n_horas = len(self.ventas_por_hora)

        for prod in self.productores:
            # ---------- 1) Matriz hora × tecnología ----------
            datos = {}
            for h, ventas in enumerate(self.ventas_por_hora):
                for unidad, q in ventas:
                    if unidad.id_Productor is prod.id:                     # este productor
                        tech = unidad.__class__.__name__
                        datos.setdefault(tech, [0] * n_horas)
                        datos[tech][h] += q
            df = pd.DataFrame(datos)

            # si el productor no vendió nada, saltamos
            if df.empty:
                continue

            # ---------- 2) Ordenar columnas ----------
            cols = [t for t in orden_tec if t in df.columns] + \
                   [t for t in df.columns if t not in orden_tec]
            df = df[cols]

            # ---------- 3) Graficar ----------
            ax = df.plot(kind="bar", stacked=True, figsize=figsize, **kwargs)
            ax.set_xlabel("Hora")
            ax.set_ylabel("Energía vendida (MW)")
            ax.set_title(f"Productor {prod.id}: mix horario")
            ax.legend(title="Tecnología", bbox_to_anchor=(1.02, 1), loc="upper left")

            # Línea de energía acumulada en eje secundario
            acumulada = df.sum(axis=1).cumsum()
            ax2 = ax.twinx()
            ax2.plot(acumulada.index, acumulada.values, marker="o",
                     label="Acumulada", linestyle="--")
            ax2.set_ylabel("Energía acumulada (MWh)")
            ax2.legend(loc="upper right")

            plt.tight_layout()
            plt.savefig(f"outputs/Simu/Energias_Simu_prod_{prod.id}.png", dpi=150, bbox_inches="tight")

            resultados[prod.id] = df

        return resultados
    


    # ──────────────────────────────────────────────────────────────
    

