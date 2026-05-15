import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time

# --- CONFIGURACIÓN Y SESIÓN ---
st.set_page_config(page_title="Sistema Ventas Madera", layout="wide")

# Inicializar el carrito en la memoria de la sesión si no existe
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# (Mantenemos el DICCIONARIO INVENTARIO igual al anterior)
INVENTARIO = {
    "MADERA PINO BRUTA": {
        '1 X 2" X 3,2 MTS': 1575, '1 X 3" X 3,2 MTS': 1800, '1 X 4" X 3,2 MTS': 2888,
        '1 X 5" X 3,2 MTS': 3623, '1 X 6" X 3,2 MTS': 4620, '1 X 8" X 3,2 MTS': 5775,
        '2 X 2" X 3,2 MTS': 2000, '2 X 3" X 3,2 MTS': 4043, '2 X 4" X 3,2 MTS': 5408,
        '2 X 5" X 3,2 MTS': 6930, '2 X 6" X 3,2 MTS': 8190, '2 X 8" X 3,2 MTS': 11340,
        '2 X 10" X 3,2 MTS': 14175, '3 X 3" X 3,2 MTS': 6038, '4 X 4" X 3,2 MTS': 10500,
        '5 X 5" X 3,2 MTS': 16800, '6 X 6" X 3,2 MTS': 23625, '8 X 8" X 3,2 MTS': 45150
    },
    "MADERA PINO TERRAZA": {
        '1 X 4" X 3,2 MTS': 3255, '1 X 5" X 3,2 MTS': 3465,
        '1.5 X 4" X 3,2 MTS': 4935, '1.5 X 5" X 3,2 MTS': 6195
    },
    "TINGLADO": {
        '1 X 4" X 3,2 MTS': 3255, '1 X 5" X 3,2 MTS': 4200
    },
    "POLINES": {
        'AGRICOLA 3 A 4" X 2,4 MTS': 4095, '4" X 2,4 MTS': 5565, '5" X 2,4 MTS': 9345,
        '3 A 4" X 3 MTS': 7298, '4" X 3,5 MTS': 11550, '5 A 6" X 3 MTS': 12075,
        '4 A 5" X 3 MTS': 9345, '6" X 3 MTS': 14385
    },
    "POSTES": {
        '4" X 4 MTS': 13125, '5" X 4 MTS': 19425, '5 A 6" X 5 MTS': 26250,
        '5 A 6" X 6 MTS': 40000, 'X 8 MTS': 73500
    },
    "OTROS / TAPAS": {
        'MADERA PINO 1 X 2" X 3,2 MTS': 1000,
        'MADERA TAPA 1 X 4 X 3,2 MTS': 2100,
        'TAPA 1 X 4 X 3,2 MTS': 2150
    }
}

# --- FUNCIONES DE ARCHIVO ---
def get_file_name():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    return f"ventas_{fecha_hoy}.csv"

def cargar_ventas_dia():
    nombre_archivo = get_file_name()
    if os.path.exists(nombre_archivo):
        df = pd.read_csv(nombre_archivo, sep=";")
        return df[df['Categoria'] != "--- TOTAL GENERAL ---"]
    return pd.DataFrame(columns=["Categoria", "Medida", "Precio_Unit", "Cantidad_Total", "Venta_Total"])

def procesar_finalizar_venta():
    nombre_archivo = get_file_name()
    df_historial = cargar_ventas_dia()
    
    # Crear DF del carrito actual
    df_carrito = pd.DataFrame(st.session_state.carrito)
    
    # Unir carrito con historial
    for _, item in df_carrito.iterrows():
        filtro = (df_historial['Categoria'] == item['Categoria']) & (df_historial['Medida'] == item['Medida'])
        if not df_historial[filtro].empty:
            df_historial.loc[filtro, 'Cantidad_Total'] += item['Cantidad_Total']
            df_historial.loc[filtro, 'Venta_Total'] = df_historial.loc[filtro, 'Cantidad_Total'] * item['Precio_Unit']
        else:
            df_historial = pd.concat([df_historial, pd.DataFrame([item])], ignore_index=True)
    
    # Calcular gran total y guardar
    gran_total = df_historial['Venta_Total'].sum()
    fila_total = pd.DataFrame([{"Categoria": "--- TOTAL GENERAL ---", "Medida": "---", 
                                "Precio_Unit": 0, "Cantidad_Total": 0, "Venta_Total": gran_total}])
    
    df_final = pd.concat([df_historial, fila_total], ignore_index=True)
    df_final.to_csv(nombre_archivo, index=False, sep=";", encoding='utf-8-sig')
    
    # Limpiar carrito
    st.session_state.carrito = []

# --- INTERFAZ ---
st.title("🌲 Venta de Maderas - Punto de Venta")

# Métrica de ventas acumuladas en el día
df_dia = cargar_ventas_dia()
st.metric("TOTAL VENTAS DEL DÍA (CAJA)", f"${df_dia['Venta_Total'].sum():,.0f}".replace(",", "."))

st.divider()

# Columna Izquierda: Selección / Columna Derecha: Carrito Actual
col_input, col_cart = st.columns([1, 1.2])

with col_input:
    st.subheader("Agregar Producto")
    cat = st.selectbox("Categoría", list(INVENTARIO.keys()))
    med = st.selectbox("Medida", list(INVENTARIO[cat].keys()))
    can = st.number_input("Cantidad", min_value=1, value=1)
    precio = INVENTARIO[cat][med]
    
    if st.button("Añadir al Carrito 🛒", use_container_width=True):
        nuevo_item = {
            "Categoria": cat,
            "Medida": med,
            "Precio_Unit": precio,
            "Cantidad_Total": can,
            "Venta_Total": precio * can
        }
        st.session_state.carrito.append(nuevo_item)
        st.toast(f"Agregado: {med}", icon="➕")

with col_cart:
    st.subheader("Carrito Actual")
    if st.session_state.carrito:
        df_temp = pd.DataFrame(st.session_state.carrito)
        st.table(df_temp[['Medida', 'Cantidad_Total', 'Venta_Total']])
        
        total_carrito = df_temp['Venta_Total'].sum()
        st.markdown(f"### Total Carrito: **${total_carrito:,.0f}**")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("CANCELAR", color="red", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        with col_btn2:
            if st.button("TERMINAR VENTA ✅", type="primary", use_container_width=True):
                procesar_finalizar_venta()
                st.success("Venta guardada en caja correctamente")
                time.sleep(1)
                st.rerun()
    else:
        st.info("El carrito está vacío")

st.divider()
st.subheader("Historial de Ventas del Día (CSV)")
st.dataframe(df_dia, use_container_width=True)
