from lectura import LeerofertasdeProductores, read_marginalpdbc, read_pdbtot, read_xls
from mercado import ModeloMercado
import matplotlib.pyplot as plt

"""
En este documento se cargan todas las ofertas de Venta de los productores.
Se introducen en la simulación
Se muestran los resultados
"""
agentes=read_xls()

err={}
for i in [320,321,322,323,324,325,326,327,328,329,331,401,402,403,404,405,406,407]:
    fecha=f"20250{i}"
    [_,ofertas, _, _, _]=LeerofertasdeProductores(fecha,agentes)
    demanda=read_pdbtot(fecha)[f"Total Ventas MI"].to_list()
    m = ModeloMercado(demanda,fecha)
    m.iniciar_mercado_df(ofertas[(ofertas["mav_mw"]==0) & (ofertas["num_block"]==0)],[])
    m.simular_df_simple()
    marg=read_marginalpdbc(fecha)
    m.grafico_precio(f"outputs/Valid/marzo/{fecha}.png",marg["price_es"].to_list())
    print((marg["price_es"].reset_index(drop=True)-m.precio_marginal.reset_index(drop=True)).abs().mean())
    err[fecha]=((marg["price_es"].reset_index(drop=True)-m.precio_marginal.reset_index(drop=True)).abs().mean())



plt.figure()
plt.plot(list(err.keys()),list(err.values()), label="error medio por día")
plt.title("Marzo: Error Simulación vs OMIE")
plt.xlabel("Días del mes")
plt.ylabel("Energía mwh")
plt.legend()
plt.savefig("outputs/Valid/marzo_abrilerror.png", dpi=150)

