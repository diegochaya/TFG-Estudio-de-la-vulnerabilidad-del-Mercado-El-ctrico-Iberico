from mercado import ModeloMercado
import pandas as pd
import random


random.seed(42) 

    
n=3
df=pd.DataFrame(columns=["propietario", "periodo", "cantidad_mw", "precio_eur_mwh", "tipo_energia"])
for p in range(4):
    for periodo in range(1,n+1):
        df.loc[len(df)]={"propietario":p,"periodo":periodo, "cantidad_mw": random.uniform(3000,6000), "precio_eur_mwh":random.uniform(10,20), "tipo_energia": "solar"}
        df.loc[len(df)]={"propietario":p,"periodo":periodo, "cantidad_mw": random.uniform(2000,4000), "precio_eur_mwh":random.uniform(25,40), "tipo_energia": "hidraulica"}
        df.loc[len(df)]={"propietario":p,"periodo":periodo, "cantidad_mw": random.uniform(1000,1500), "precio_eur_mwh":random.uniform(35,45), "tipo_energia": "nuclear"}
        df.loc[len(df)]={"propietario":p,"periodo":periodo, "cantidad_mw": random.uniform(3000,4000), "precio_eur_mwh":random.uniform(60,80), "tipo_energia": "gas"}
demanda=[random.uniform(20000,40000) for _ in range(n)]

for n_esp in [[],[0],[0,1],[0,1,2]]:

    m = ModeloMercado(demanda)
    m.iniciar_mercado_df(df,n_esp)
    m.simular_df_simple()
    print(f"\nPrecio Marginal medio: {m.precio_marginal.mean()}")
    #print(m.df_of.groupby("tipo_energia")["cantidad_aceptada"].sum())
    m.resultados()
    #m.grafico_ventas_apiladas()
    m.grafico_precio()
