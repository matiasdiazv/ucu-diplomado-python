import streamlit as st           # construye la app web
import pandas as pd              # maneja los datos (la tabla)
import matplotlib.pyplot as plt  # dibuja los gráficos
import numpy as np               # cálculos numéricos (la línea de tendencia)

st.set_page_config(
    page_title="Inversión en marketing y su impacto en las Ventas",
    layout="centered"
)

COLOR_PRINCIPAL = "steelblue"

# Convierte un número en texto de dinero: 79110 -> "USD 79.110"
def formato_usd(valor):
    return f"USD {valor:,.0f}".replace(",", ".")

@st.cache_data
def cargar_datos():
    # La ruta NO lleva "../" porque app.py está en la raíz del proyecto
    df = pd.read_csv("data/processed/marketing_sales_limpio.csv")
    df["date"] = pd.to_datetime(df["date"])   # el CSV guarda la fecha como texto: la reconvertimos
    df["year"] = df["date"].dt.year           # columna de año, para el filtro
    return df


df = cargar_datos()

st.title("¿La inversión en marketing genera más ingresos?")
st.write(
    "Esta aplicación permite explorar la relación entre la inversión en "
    "marketing y los ingresos por venta. Utiliza los filtros de la izquierda para "
    "acotar los datos y observá cómo se actualizan las visualizaciones."
)

st.sidebar.markdown("## Filter")
st.sidebar.markdown(
    "Ajustá el rango de presupuesto y elegí los canales que querés analizar."
)

# Filtro 1: rango de presupuesto (slider con formato)
min_budget = int(df["marketing_budget_usd"].min())
max_budget = int(df["marketing_budget_usd"].max())

# Lista de valores posibles, en pasos de 500 USD (más el máximo exacto al final)
valores_presupuesto = list(range(min_budget, max_budget, 500)) + [max_budget]

rango = st.sidebar.select_slider(
    "Presupuesto de marketing",
    options=valores_presupuesto,
    value=(min_budget, max_budget),
    format_func=formato_usd      # muestra cada valor como "USD 79.109"
)

# Filtro 2: canal de venta (selector de una o varias categorías)
canales = st.sidebar.multiselect(
    "Canal de venta",
    options=df["sales_channel"].unique(),
    default=df["sales_channel"].unique()
)

# Filtro 3: año (selector de uno o varios años)
anios = st.sidebar.multiselect(
    "Año",
    options=sorted(df["year"].unique()),
    default=sorted(df["year"].unique())
)

df_filtrado = df[
    (df["marketing_budget_usd"] >= rango[0]) &
    (df["marketing_budget_usd"] <= rango[1]) &
    (df["sales_channel"].isin(canales)) &
    (df["year"].isin(anios))
]

# Si no quedó ningún dato (combinación de filtros sin ventas), avisamos y frenamos.
if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados. Ajustá los filtros para ver resultados.")
    st.stop()

# Mostramos en palabras qué se está viendo, bien formateado.
cantidad = f"{len(df_filtrado):,}".replace(",", ".")
st.write(
    f"Mostrando **{cantidad}** ventas con un presupuesto de marketing entre "
    f"**{formato_usd(rango[0])}** y **{formato_usd(rango[1])}**."
)

# Tres tarjetas visuales: Ventas, Ingreso Promedio e Inversión Promedio.
col1, col2, col3 = st.columns(3)

col1.metric("Ventas seleccionadas", f"{len(df_filtrado):,}".replace(",", "."))
col2.metric("Ingreso promedio", formato_usd(df_filtrado["sales_revenue_usd"].mean()))
col3.metric("Inversión promedio", formato_usd(df_filtrado["marketing_budget_usd"].mean()))

st.subheader("Resumen descriptivo")
st.markdown("Valores expresados en USD.")

# Columnas relevantes para el análisis (dejamos afuera 'id' y las que no aportan)
columnas_resumen = [
    "marketing_budget_usd",
    "ad_spend_online_usd",
    "ad_spend_offline_usd",
    "sales_revenue_usd"
]

# describe() de esas columnas, transpuesto
resumen = df_filtrado[columnas_resumen].describe().T

# Se cambia de nombre a las filas a los efectos de presentación.
resumen = resumen.rename(index={
    "marketing_budget_usd": "Marketing Budget",
    "ad_spend_online_usd": "Ad Spent Online",
    "ad_spend_offline_usd": "Ad Spent Offline",
    "sales_revenue_usd": "Sales Revenue"
})

# Formato de números al estilo local: "79.069,34" (punto miles, coma decimal)
def formato_tabla(x):
    return f"{x:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")

st.dataframe(resumen.style.format(formato_tabla))

rango_ingresos = df_filtrado["sales_revenue_usd"].max() - df_filtrado["sales_revenue_usd"].min()
st.write(f"Rango de ingresos (máximo − mínimo): **{formato_usd(rango_ingresos)}**")

# Histograma
st.subheader("Distribución de los ingresos")
st.write("La mayoría de las ventas generan ingresos bajos o medios, y unas pocas "
         "alcanzan montos muy altos. Por eso la distribución se concentra a la "
         "izquierda y se extiende con una cola hacia la derecha.")

fig1, ax1 = plt.subplots()
ax1.hist(
    df_filtrado["sales_revenue_usd"],
    bins=50,
    color=COLOR_PRINCIPAL,
    edgecolor="white"
)
ax1.set_xlabel("Ingresos (USD)")
ax1.set_ylabel("Cantidad de ventas")
ax1.set_xlim(0, 40000)
st.pyplot(fig1)

# Scatter Plot con Línea de Tendencia
st.subheader("Inversión en marketing vs. Ingresos")
st.write("Cada punto es una venta. La línea roja es la tendencia general: "
         "a mayor presupuesto de marketing, los ingresos tienden a ser mayores.")

fig2, ax2 = plt.subplots()
ax2.scatter(
    df_filtrado["marketing_budget_usd"],
    df_filtrado["sales_revenue_usd"],
    alpha=0.2,
    s=10,
    color=COLOR_PRINCIPAL
)

# Línea de tendencia (solo si hay suficientes puntos)
if len(df_filtrado) > 1:
    x = df_filtrado["marketing_budget_usd"]
    y = df_filtrado["sales_revenue_usd"]
    pendiente, ordenada = np.polyfit(x, y, 1)
    ax2.plot(x, pendiente * x + ordenada, color="red", linewidth=2)

ax2.set_xlabel("Presupuesto de marketing (USD)")
ax2.set_ylabel("Ingresos (USD)")
ax2.set_ylim(0, 40000)
st.pyplot(fig2)

# Bar Graph
st.subheader("Ingreso promedio por canal")
st.write("Comparamos cuánto genera en promedio cada canal de venta, según los "
         "filtros aplicados.")

# Ingreso promedio por canal, ordenado de menor a mayor
ventas_por_canal = df_filtrado.groupby("sales_channel")["sales_revenue_usd"].mean().sort_values()

fig3, ax3 = plt.subplots()
ax3.bar(ventas_por_canal.index, ventas_por_canal.values,
        color=COLOR_PRINCIPAL, edgecolor="white")
ax3.set_xlabel("Canal de venta")
ax3.set_ylabel("Ingreso promedio (USD)")
ax3.tick_params(axis="x", rotation=20)
st.pyplot(fig3)