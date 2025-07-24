from lectura import LeerofertasdeProductores, read_pdbtot, read_marginalpdbc, read_xls
import matplotlib.pyplot as plt

FECHA   = "20250402"     # formato aaaammdd   

agentes=read_xls()
[_,ofertas, _, _, _]=LeerofertasdeProductores(FECHA,agentes)
pdbtot=read_pdbtot(FECHA)
marg=read_marginalpdbc(FECHA)


of_Merc=ofertas[(ofertas["num_block"]==0) & (ofertas["mav_mw"]==0)]
of_Merc=of_Merc.sort_values(["periodo","precio_eur_mwh"])


of_Merc=of_Merc.merge(pdbtot["Total Ventas MI"],left_on="periodo", right_index=True)
of_Merc["acum"]=of_Merc.groupby("periodo")["cantidad_mw"].cumsum()
of_Merc["cantidad_aceptada"]=(of_Merc["Total Ventas MI"]-(of_Merc["acum"]-of_Merc["cantidad_mw"])).clip(0,of_Merc["cantidad_mw"])


#Calcular la Casada


of_cas=of_Merc[of_Merc["cantidad_aceptada"]>1e-7]
of_cas=of_cas.drop(["cantidad_mw", "acum", "Total Ventas MI"], axis=1)
of_cas=of_cas.rename(columns={"cantidad_aceptada":"cantidad_mw"})
precio_marginal=of_cas.groupby("periodo")["precio_eur_mwh"].max()
precio_marginal.name="precio_marginal"

xmax=100000
# Indice de manipulabilidad
mandad=of_Merc[(of_Merc["cantidad_aceptada"]<=1e-7) & (of_Merc["cantidad_aceptada"]>-xmax)]
mandad=mandad.merge(precio_marginal,left_on="periodo", right_index=True)
mandad["area"]=(mandad["precio_eur_mwh"]-mandad["precio_marginal"])*mandad["cantidad_mw"]
manipulabilidad= mandad.groupby("periodo")["area"].sum()


#Indice de manipulacion
mancon=of_Merc[(of_Merc["cantidad_aceptada"]>1e-7) & (of_Merc["cantidad_aceptada"]<xmax)]
mancon=mancon.merge(precio_marginal,left_on="periodo", right_index=True)
mancon["area"]=(mancon["precio_marginal"]-mancon["precio_eur_mwh"])*mancon["cantidad_mw"]
manipulacion= mancon.groupby("periodo")["area"].sum()

per=1
plt.figure()
plt.plot(mandad[mandad["periodo"]==per]["area"], label="manipulabilidad")
plt.plot(mancon[mancon["periodo"]==per]["area"], label="manipulacion")
plt.title(f"Rango de Energía = {xmax}")
plt.legend()
plt.savefig(f"outputs/Manipulabilidad_cion_per_{per}.png", dpi=150)

plt.figure()
plt.plot(manipulabilidad.values, label="manipulabilidad")
plt.plot(manipulacion.values, label="manipulacion")
plt.title(f"Rango de Energía = {xmax}")
plt.legend()
plt.savefig("outputs/Manipulabilidad_cion.png", dpi=150)

plt.figure()
plt.plot(of_cas.groupby("periodo")["cantidad_mw"].sum().values, label="ofertas_det")
plt.plot(pdbtot["Total Ventas MI"].values, label="PDBC_TOT_MI")
plt.legend()
plt.savefig("outputs/Energias_det_tot.png", dpi=150)

plt.figure()
plt.plot(marg.values, label="preciomargtot")
plt.plot(precio_marginal.values, label="preciodet")
plt.legend()
plt.savefig("outputs/Precios_det_tot.png", dpi=150)

