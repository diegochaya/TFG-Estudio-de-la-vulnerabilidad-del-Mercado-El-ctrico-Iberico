from lectura import LeerTodo, Validar, leer_pdb, read_pdbtot,read_xls
import pandas as pd
import matplotlib.pyplot as plt
from mercado import ModeloMercado

dict={"mav_mw":[],"num_block":[],"num_grupo_excl":[],"mar_ratio":[]}
for i in [320,321,322,323,324,325,326,327,328,329,331,401,402,403,404,405,406,407]:
    
    FECHA   = f"20250{i}"     # formato aaaammdd
    print(FECHA)

    [cab,det,pdb,agentes,unid, ofertasV, ofertasCasadasV, pdbtot, marg, bilaterales] = LeerTodo(FECHA)
    Validar(ofertasV, ofertasCasadasV, pdbtot, marg, bilaterales)
    print(ofertasCasadasV["mav_mw"].value_counts())
    print(ofertasCasadasV["num_block"].value_counts())
    print(ofertasCasadasV["num_grupo_excl"].value_counts())
    print(ofertasCasadasV["mar_ratio"].value_counts())
    dict["mav_mw"].append(ofertasCasadasV["mav_mw"].value_counts())
    dict["num_block"].append(ofertasCasadasV["num_block"].value_counts())
    dict["num_grupo_excl"].append(ofertasCasadasV["num_grupo_excl"].value_counts())
    dict["mar_ratio"].append(ofertasCasadasV["mar_ratio"].value_counts())

    plt.figure()
    plt.plot(ofertasCasadasV.groupby("periodo")["cantidad_mw"].sum().values, label=f"pdbf_ofertas_{FECHA}",alpha=0.5)
    plt.plot(pdbtot["Total Ventas MI"].values, label=f"PDBC_TOT_{FECHA}_MI", alpha=0.5)
    plt.legend()
    plt.savefig(f"outputs/PruebasOmie/Energias_{FECHA}.png", dpi=150)

    plt.figure()
    plt.plot(ofertasCasadasV.groupby("periodo")["precio_eur_mwh"].max().values, label=f"pdbf_precios_{FECHA}",alpha=0.5)
    plt.plot(marg["price_es"].values, label=f"maginalpdbc_{FECHA}", alpha=0.5)
    plt.legend()
    plt.savefig(f"outputs/PruebasOmie/Energias_Precio{FECHA}.png", dpi=150)

print(dict)