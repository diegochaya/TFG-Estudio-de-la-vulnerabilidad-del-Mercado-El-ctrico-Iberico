from lectura import LeerofertasdeProductores, read_marginalpdbc, read_pdbtot, read_xls
from mercado import ModeloMercado
import matplotlib.pyplot as plt


agentes=read_xls()

fecha=f"20250402"
[_,ofertas, _, _, _]=LeerofertasdeProductores(fecha, agentes)
demanda=read_pdbtot(fecha)[f"Total Ventas MI"].to_list()

print("0")
m = ModeloMercado(demanda,fecha)
m.iniciar_mercado_df(ofertas,[])
m.simular_df_pulp()

print("1")
m1 = ModeloMercado(demanda,fecha)
m1.iniciar_mercado_df(ofertas,[0])
m1.simular_df_pulp()

print("2")
m2 = ModeloMercado(demanda,fecha)
m2.iniciar_mercado_df(ofertas,[0,1,2])
m2.simular_df_pulp()

print("3")
m3 = ModeloMercado(demanda,fecha)
m3.iniciar_mercado_df(ofertas,[0,1,2,3])
m3.simular_df_pulp()

print("5")
m5 = ModeloMercado(demanda,fecha)
m5.iniciar_mercado_df(ofertas,[0,1,2,3,5])
m5.simular_df_pulp()

print("6")
m6 = ModeloMercado(demanda,fecha)
m6.iniciar_mercado_df(ofertas,[0,1,2,3,5,6])
m6.simular_df_pulp()



plt.figure()
plt.plot(m.precio_marginal.values, label="precio sin especuladores")
plt.plot(m1.precio_marginal.values, label="precio con 1 especulador")
plt.plot(m2.precio_marginal.values, label="precio con 2 especuladores")
plt.plot(m3.precio_marginal.values, label="precio con 3 especuladores")
plt.plot(m5.precio_marginal.values, label="precio con 5 especuladores")
plt.plot(m6.precio_marginal.values, label="precio con 6 especuladores")

plt.title("PreciosMarginales")
plt.xlabel("Horas del día")
plt.ylabel("Euros")
plt.legend()
plt.savefig(f"outputs/Espec/EspeculadoresV_{fecha}.png", dpi=150)
