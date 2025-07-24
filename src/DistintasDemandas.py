from lectura import LeerofertasdeProductores, read_pdbtot, read_marginalpdbc, read_xls
import numpy as np
import matplotlib.pyplot as plt
from mercado import ModeloMercado

FECHA   = "20250402"     # formato aaaammdd   

agentes=read_xls()
[_,ofertas, _, _, _]=LeerofertasdeProductores(FECHA, agentes)
pdbtot=read_pdbtot(FECHA)
marg=read_marginalpdbc(FECHA)

demanda=pdbtot["Total Ventas MI"]
of_Merc=ofertas.copy()
of_Merc=of_Merc.sort_values(["periodo","precio_eur_mwh"])
x0=0.8
xn=1
d_incr=np.linspace(x0,xn,10)
norm = plt.Normalize(x0, xn)
cmap = plt.cm.viridis_r
fig,ax=plt.subplots()

for d in d_incr:
    print(d)
    m = ModeloMercado((demanda*d).tolist())
    m.iniciar_mercado_df(ofertas,[])
    m.simular_df_simple()
    print(m.precio_marginal.values)
    ax.plot(m.precio_marginal.values, color=cmap(norm(d)), alpha=0.8)


sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array(d_incr)
cbar = fig.colorbar(sm,ax=ax, label='Parámetro p')


ax.set_title('Familia de curvas según parámetro')

plt.tight_layout()
plt.savefig(f"outputs/EnergiasDemandasMenosSimple_{FECHA}.png")


x0=1
xn=1.2
d_incr=np.linspace(x0,xn,10)
norm = plt.Normalize(x0, xn)
cmap = plt.cm.viridis
fig,ax=plt.subplots()

for d in d_incr:
    print(d)
    m = ModeloMercado((demanda*d).tolist())
    m.iniciar_mercado_df(ofertas,[])
    m.simular_df_simple()
    print(m.precio_marginal.values)
    ax.plot(m.precio_marginal.values, color=cmap(norm(d)), alpha=0.8)


sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array(d_incr)
cbar = fig.colorbar(sm,ax=ax, label='Parámetro p')


ax.set_title('Familia de curvas según parámetro')

plt.tight_layout()
plt.savefig(f"outputs/EnergiasDemandasMasSimple_{FECHA}.png")