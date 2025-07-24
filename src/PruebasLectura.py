from lectura import LeerTodo, Validar, Leer_demanda_REE
import matplotlib.pyplot as plt


FECHA   = "20250405"     # formato aaaammdd



[cab,det,pdb,agentes,unid, ofertasV, ofertasCasadasV, pcbtot, marg, bilaterales] = LeerTodo(FECHA)
Validar(ofertasV, ofertasCasadasV,pcbtot, marg, bilaterales)



DemandaREE=Leer_demanda_REE(
    "datos/Custom-Report-2025-04-02-Seguimiento de la demanda de energía eléctrica (MW).csv")

e_tot_bil   = pcbtot["Total Ventas ES"] + pcbtot["Total Contratos Bilaterales ES"]
e_tot_MI   = pcbtot["Total Ventas ES"]
ofertasTotales= ofertasCasadasV[ofertasCasadasV["pais"]=="ZONA ESPAÑOLA"].groupby("periodo")["cantidad_mw"].sum()
bilateralesTotales=bilaterales[bilaterales["pais"]=="ZONA ESPAÑOLA"].groupby("periodo")["cantidad_mw"].sum()

plt.figure()
plt.plot(e_tot_bil.values, label="PDBC_TOT_BIL_ES")
plt.plot(e_tot_MI.values, label="PDBC_TOT_ES")
plt.plot(ofertasTotales.values, label="OfertasV totales mercado MI")
plt.plot(DemandaREE, label="Demanda REE ES")
plt.plot(pcbtot["Total Contratos Bilaterales ES"].values, label="bilateralesTot ES")
plt.plot(bilateralesTotales.values, label="bilaterales mercado ES")
plt.ylim(0,40000)
plt.legend()
plt.savefig("outputs/Energias.png", dpi=150)


p_oferta = ofertasCasadasV.groupby("periodo")["precio_eur_mwh"].max()
plt.figure()
plt.plot(marg["price_es"], label="MARGINALPDBC")
plt.plot(p_oferta, label="PDBCE")
plt.legend()
plt.savefig("outputs/Precios.png", dpi=150)





