import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List


def Leer_demanda_REE(ruta_csv: str, n:int=24) -> List[float]:
        """
        Devuelve los 288 valores de 5 minutos comprendidos entre
        las filas 40 y 327 de la columna 'Prevista' (C-40 … C-327).

        • No se pasa fecha; nos fiamos de la posición fija.
        • Si la lectura UTF-8 falla probamos Latin-1.
        • Lanza ValueError si no encuentra exactamente 288 valores.
        """
        import pandas as pd

        df = pd.read_csv(ruta_csv, skiprows=1, engine="python", encoding="latin1")
        df.columns = [c.strip() for c in df.columns]
        
        if "Prevista" not in df.columns:
            raise ValueError("Columna 'Prevista' no encontrada en el CSV.")

        
        demandas = df["Prevista"].iloc[39:327].astype(float).to_numpy()       # 288 filas exactas

        if demandas.size != 288:
            raise ValueError(
                f"Se esperaban 288 valores entre C-40 y C-327; "
                f"se encontraron {len(demandas)}."
            )
        #Se pasa a intervalos de tamaño n
        x_src = np.arange(288)
        x_dst = np.linspace(0, 287, n)
        demandas_n = np.interp(x_dst, x_src, demandas)

        return demandas_n.astype(float).tolist()


def LeerofertasdeProductores(fecha: str, agentes):
    cab  = read_cab(fecha)
    det  = read_det(fecha)

    unid = cab[["cod_oferta", "version", "cod_uo", "cv", "max_pot"]].merge(agentes, on="cod_uo", how="left")

    #Ofertas
    ofertas = det.merge(unid, on="cod_oferta")
    if not (ofertas["version_x"] == ofertas["version_y"]).all():
        print("Warning: Una oferta tiene versiones distintas en DET y CAB")
    ofertas = ofertas.drop(columns=["version_x", "version_y"])
    ofertas["porcentaje"]= ofertas["porcentaje"].fillna(100)
    ofertas["cantidad_mw"]= ofertas["cantidad_mw"]*ofertas["porcentaje"]/100
    ofertasV=ofertas[(ofertas["cantidad_mw"]>0) & (ofertas["cv"]=="V")]
    return ofertas, ofertasV, cab, det, agentes

def LeerTodo(fecha: str):
 
    # ---------- lecturas -------------------------------------------
    cab  = read_cab(fecha)
    det  = read_det(fecha)
    pdb  = leer_pdb(fecha)
    agentes = read_xls()
    pcbtot = read_pdbtot(fecha)
    marg = read_marginalpdbc(fecha)

    # ---------- merges ---------------------------------------------

    #Agentes 
    unid = cab[["cod_oferta", "version", "cod_uo", "cv", "max_pot"]].merge(agentes, on="cod_uo", how="left")

    #Ofertas
    ofertas = det.merge(unid, on="cod_oferta")
    if not (ofertas["version_x"] == ofertas["version_y"]).all():
        print("Warning: Una oferta tiene versiones distintas en DET y CAB")
    ofertas = ofertas.drop(columns=["version_x", "version_y"])
    ofertasV=ofertas[(ofertas["cantidad_mw"]>0) & (ofertas["cv"]=="V")]

    #Transformación de pdb a 24 horas
    p96=True
    if p96:
      pdb["periodo"]=(pdb["periodo"]-1)//4+1
      pdb=(pdb.groupby(['year', 'month', 'day', "periodo", "cod_uo", "cod_oferta"],as_index=False).
        agg(cantidad_mw_casada=('cantidad_mw_casada', 'mean'),type_offer=('type_offer', 'first')))
    
    #Ofertas de Venta Casadas sin bilaterales
    pdb_sc=pdb[(pdb["type_offer"]!=4) & (pdb["cantidad_mw_casada"]>0)]
    ofertasCasadasV = ofertasV.merge(
        pdb_sc[["periodo", "cod_oferta","cod_uo", "cantidad_mw_casada","type_offer"]],
        on=["periodo", "cod_oferta", "cod_uo"], how="right")
    
    if sum(ofertasCasadasV["cv"]=="C")>0:
      print(f"Warning: En las ofertas positivas quedan compradores")
    

    #Eliminar las ofertas num_tramo no casadas

    ofertasCasadasV["porcentaje"]=ofertasCasadasV["porcentaje"].fillna(100)
    ofertasCasadasV = ofertasCasadasV.sort_values(
            ["cod_oferta", "cod_uo", "porcentaje", "periodo", "precio_eur_mwh"])

    ofertasCasadasV["acum_mw"] = (
            ofertasCasadasV.groupby(["cod_oferta", "cod_uo", "periodo", "porcentaje"])
                          ["cantidad_mw"].cumsum())
    
    ofertasCasadasV["aceptado_mw"] = (
            ofertasCasadasV["cantidad_mw_casada"]
            - (ofertasCasadasV["acum_mw"] - ofertasCasadasV["cantidad_mw"])
    ).clip(lower=0, upper=ofertasCasadasV["cantidad_mw"])
    ofertasCasadasV = ofertasCasadasV[ofertasCasadasV["aceptado_mw"] > 1e-7]
    ofertasCasadasV=ofertasCasadasV.drop(["cantidad_mw", "acum_mw", "cantidad_mw_casada"], axis=1)
    ofertasCasadasV=ofertasCasadasV.rename(columns={"aceptado_mw":"cantidad_mw"})

    #Aplicamos los porcentajes
    
    ofertasCasadasV["cantidad_mw"]= ofertasCasadasV["cantidad_mw"]*ofertasCasadasV["porcentaje"]/100
    
    #Separamos contratos bilaterales
    bilaterales=pdb[(pdb["type_offer"]==4) & (pdb["cantidad_mw_casada"]>0)]
    bilaterales = bilaterales.rename(columns={"cantidad_mw_casada": "cantidad_mw"})
    bilaterales = bilaterales[["periodo", "cod_oferta","cod_uo", "cantidad_mw","type_offer"]
        ].merge(unid.drop("cod_oferta",axis=1), on="cod_uo", how="left")
    bilaterales = bilaterales.assign(num_tramo=1, precio_eur_mwh=pd.NA, num_grupo_excl=0, num_block=0)
    bilaterales["porcentaje"] = bilaterales["porcentaje"].fillna(100)
    bilaterales["cantidad_mw"] = bilaterales["cantidad_mw"]*bilaterales["porcentaje"]/100
    return cab,det,pdb,agentes,unid, ofertasV, ofertasCasadasV, pcbtot, marg, bilaterales




def Validar(ofertas, ofertasCasadasV,pcbtot,marg, bilaterales):
    # --- 1 demanda total diaria ------------------------------
    contador_Pruebas:int=5
    energia_pdbce = ofertasCasadasV["cantidad_mw"].sum()
    e_tot = pcbtot["Total Ventas MI"]
    energia_tot   = sum(e_tot)
    if not np.isclose(energia_pdbce, energia_tot, atol=2):
        contador_Pruebas-=1
        print(
            f"Demanda diaria no coincide "
            f"(PDBCE={energia_pdbce:.3f} MWh  vs  PDBC_TOT={energia_tot:.3f} MWh)")

    # --- 2 energía por periodo ------------------------------
    ofertasTotales= ofertasCasadasV.groupby("periodo")["cantidad_mw"].sum()
    if not np.allclose(ofertasTotales.values, e_tot.values,
                        atol=2):
        contador_Pruebas-=1
        diff = max(abs(ofertasTotales.values - e_tot.values))
        print(f"Energía por periodo difiere hasta {diff:.3f} MWh")

    # --- 3 energía bilaterales por periodo ------------------------------
    bilateralesTotales= bilaterales.groupby("periodo")["cantidad_mw"].sum()
    bil_tot = pcbtot["Total Contratos Bilaterales MI"]
    if not np.allclose(bilateralesTotales.values, bil_tot.values,
                        atol=2):
        contador_Pruebas-=1
        diff = max(abs(bilateralesTotales.values - bil_tot.values))
        print(f"Energía bilaterales por periodo difiere hasta {diff:.3f} MWh")

    # --- 4 · precios marginales -------------------------------
    
    p_oferta = ofertasCasadasV.groupby("periodo")["precio_eur_mwh"].max()
    if not np.allclose(p_oferta.values,
                        marg["price_es"].values,
                        atol=3):
        contador_Pruebas-=1
        diff = max(abs(p_oferta.values-marg["price_es"].values))
        print(f"Energía bilaterales por periodo difiere hasta {diff:.3f} EUR/MWh")


    # --- 5 · capacidad ofertada vs declarada -------------------
    excedidas = ofertas[ofertas["cantidad_mw"] > ofertas["max_pot"]]
    if not excedidas.empty:
        contador_Pruebas-=1
        print(
            f"Capacidad ofertada excede el máximo en "
            f"{len(excedidas)} ofertas "
            f"(ejemplo: {excedidas.iloc[0,:]})")

    print(f"Pruebas pasadas {contador_Pruebas}/5")



def leer_pdb(fecha:str,doc:str="f", fname=None) -> pd.DataFrame:
    if not fname:
        fname=f"datos/pdb{doc}_{fecha[:-2]}/pdb{doc}_{fecha}.1"
    df = pd.read_csv(
        fname,
        sep=';', header=None, engine='python',
        names=[
            'year', 'month', 'day', 'periodo', 'cod_uo',
            'cantidad_mw_casada', 'company_acronym', "type_offer", 'cod_oferta',
             'dummy'
        ],
        decimal='.', dtype=str, skip_blank_lines=True
    )
    df = df.drop(columns=['dummy'])
    df = df[1:-1]        # quita línea cabecera y final
    num_cols = ['year', 'month', 'day', 'periodo',
                'cantidad_mw_casada', 'cod_oferta', 'type_offer']
    df[num_cols] = df[num_cols].apply(
        pd.to_numeric, errors='coerce')
    df['company_acronym'] = df['company_acronym'].replace('', None)
    df = df.sort_values(['year', 'month', 'day', 'periodo']).reset_index(drop=True)
    return df


def read_det(fecha: str, fname=None) -> pd.DataFrame:
    if not fname:
        fname=f"datos/det_{fecha[:-2]}/DET_{fecha}.1"
    DET_WIDTHS = [10, 5, 3, 2, 2, 2, 17, 7, 7, 5]
    DET_COLS = ["cod_oferta", "version", "periodo",
                "num_block", "num_tramo", "num_grupo_excl",
                "precio_eur_mwh", "cantidad_mw",
                "mav_mw", "mar_ratio"]
    df= pd.read_fwf(fname, widths=DET_WIDTHS, names=DET_COLS,
                       dtype=str, encoding='latin1', na_values=[""])
    df = df.apply(
        pd.to_numeric, errors='coerce')
    return df

def read_cab(fecha: str, fname=None) -> pd.DataFrame:
    if not fname:
        fname=f"datos/cab_{fecha[:-2]}/CAB_{fecha}.1"
    CAB_WIDTHS = [
        10, 5,          # cod_oferta, version
        7, 30,          # cod_uo, descripcion
        1, 1,        # cv, tipo_precio, ofer_plazo
        17, 7,          # fijo_eur, max_pot
        2,              # cod_int
        4, 2, 2, 2, 2, 2]   # anio_ins ... seg_ins
    CAB_COLS = [
        "cod_oferta", "version", "cod_uo", "descripcion",
        "cv", "ofer_plazo",
        "fijo_eur", "max_pot", "cod_int",
        "anio_ins", "mes_ins", "dia_ins",
        "hora_ins", "min_ins", "seg_ins"]

    df= pd.read_fwf(fname, widths=CAB_WIDTHS, names=CAB_COLS,
                       dtype=str, encoding='latin1', na_values=[""])
    num_cols = ["cod_oferta", "version", "fijo_eur", "max_pot"]
    df[num_cols] = df[num_cols].apply(
        pd.to_numeric, errors='coerce')

    return df

def read_xls(fname: str="datos/LISTA_UNIDADES.csv") -> pd.DataFrame:
  xls_cols=["cod_uo", "descripcion", "propietario",
        "porcentaje", "tipo_unidad", "pais","tipo_energia"
        ]
  return pd.read_csv(fname, sep=";", engine="python", encoding="latin1",thousands=".",
               decimal=",",skiprows=[0],names= xls_cols).dropna(how="all")



def read_pdbtot(fecha: str, doc:str= "f", fname=None) -> pd.DataFrame:
    if not fname:
        fname=f"datos/pdb{doc}_tot/pdb{doc}_tot_{fecha}.1"
    df  = pd.read_csv(fname, sep=";", engine="python", encoding="latin1",thousands=".",
               decimal=",",skiprows=[0,1,3,7,11,15])
    df= df.iloc[:, :-2]
    df['horas'] = df['Total'].astype(str) + ' ' + df['Pais'].astype(str)
    df = df.drop(['Total','Pais'], axis=1).set_index('horas')
    df= df.T
    df.iloc[:, 1:] = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
    df.index=pd.RangeIndex(start=1, stop=len(df)+1)
    return df


def read_marginalpdbc(fecha: str, fname=None) -> pd.DataFrame:
    if not fname:
        fname=f"datos/marginalpdbc/marginalpdbc_{fecha}.1"
    df = pd.read_csv(fname, sep=";", engine="python",
                     header=None,
                     skiprows=[0,25], encoding="latin1",
                     names=["year", "month", "day",
                            "periodo", "price_pt", "price_es", "dummy"])
    df=df[["periodo", "price_es"]].astype({"periodo": "int64",
                                              "price_es": "float64"})
    df.set_index("periodo", inplace=True)
    return df


