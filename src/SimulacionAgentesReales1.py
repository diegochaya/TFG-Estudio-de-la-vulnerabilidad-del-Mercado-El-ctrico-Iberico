from lectura import LeerofertasdeProductores, read_marginalpdbc, read_pdbtot, read_xls
from mercado import ModeloMercado
import matplotlib.pyplot as plt

"""
En este documento se cargan todas las ofertas de Venta de los productores.
Se introducen en la simulación
Se muestran los resultados
"""
agentes=read_xls()

fecha=f"20250402"
[_,ofertas, _, _, _]=LeerofertasdeProductores(fecha, agentes)
demanda=read_pdbtot(fecha)[f"Total Ventas MI"].to_list()

print("0")
m = ModeloMercado(demanda,fecha)
m.iniciar_mercado_df(ofertas,[])
m.simular_df_pulp()
m.resultados()

print("1")
m1 = ModeloMercado(demanda,fecha)
m1.iniciar_mercado_df(ofertas,[0])
m1.simular_df_pulp()
m1.resultados()

print("2")
m2 = ModeloMercado(demanda,fecha)
m2.iniciar_mercado_df(ofertas,[1])
m2.simular_df_pulp()
m2.resultados()

print("3")
m3 = ModeloMercado(demanda,fecha)
m3.iniciar_mercado_df(ofertas,[2])
m3.simular_df_pulp()
m3.resultados()
"""
print("2")
m4 = ModeloMercado(demanda,fecha)
m4.iniciar_mercado_df(ofertas,[0,1,2,3,4])
m4.simular_df_pulp()
"""
print("4")
m5 = ModeloMercado(demanda,fecha)
m5.iniciar_mercado_df(ofertas,[3])
m5.simular_df_pulp()
m5.resultados()

print("6")
m6 = ModeloMercado(demanda,fecha)
m6.iniciar_mercado_df(ofertas,[5])
m6.simular_df_pulp()
m6.resultados()

"""
print("2")
m7 = ModeloMercado(demanda,fecha)
m7.iniciar_mercado_df(ofertas,[0,1,2,3,4,5,6,7])
m7.simular_df_pulp()

print("2")
m8 = ModeloMercado(demanda,fecha)
m8.iniciar_mercado_df(ofertas,[0,1,2,3,4,5,6,7,8])
m8.simular_df_pulp()
"""

plt.figure()
plt.plot(m.precio_marginal.values, label="precio sin especuladores")
plt.plot(m1.precio_marginal.values, label="precio con especulador 1")
plt.plot(m2.precio_marginal.values, label="precio con especulador 2")
plt.plot(m3.precio_marginal.values, label="precio con especulador 3")
#plt.plot(m4.precio_marginal.values, label="precio con 4 especuladores")
plt.plot(m5.precio_marginal.values, label="precio con especulador 5")
plt.plot(m6.precio_marginal.values, label="precio con especulador 6")
#plt.plot(m7.precio_marginal.values, label="precio con 7 especuladores")
# vendedplt.plot(m8.precio_marginal.values, label="precio con 8 especuladores")
plt.title("PreciosMarginales")
plt.xlabel("Horas del día")
plt.ylabel("Euros")
plt.legend()
plt.savefig(f"outputs/Espec/Especuladores1_{fecha}.png", dpi=150)