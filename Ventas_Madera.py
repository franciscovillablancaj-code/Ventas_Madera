import streamlit as st
import pandas as pd
from datetime import datetime
import time
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Ventas Madera", layout="wide")

# Estilo para botones (Opcional: mejora visual)
st.markdown("""
    <style>
    .stButton>button { border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
# Esta conexión busca las credenciales en los "Secrets" de Streamlit
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZACIÓN DE MEMORIA TEMPORAL ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- INVENTARIO (Igual al original) ---
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

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_ventas_totales():
    try:
        # Lee la hoja de Google Sheets
        return conn.read(ttl=0)
    except:
        return pd.DataFrame(columns=["Fecha", "Categoria", "Medida", "Precio_Unit", "Cantidad", "Total"])

def finalizar_venta_gsheets(carrito_items):
    df_historial = cargar_ventas_totales()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    # Preparar datos del carrito para anexar
    nuevos_datos = []
    for item in carrito_items:
        nuevos_datos.append({
            "Fecha": fecha_hoy,
            "Categoria": item["Categoria"],
            "Medida": item["Medida"],
            "Precio_Unit": item["Precio_Unit"],
            "Cantidad": item["Cantidad"],
            "Total": item["Total"]
        })
    
    df_nuevos = pd.DataFrame(nuevos_datos)
    df_actualizado = pd.concat([df_historial, df_nuevos], ignore_index=True)
    
    # Guardar de vuelta en Google Sheets
    conn.update(data=df_actualizado)
    st.session_state.carrito = []

# --- INTERFAZ DE USUARIO ---
st.title("🌲 Punto de Venta Madera (Cloud Sync)")

# 1. Mostrar Ventas del Día
df_todo = cargar_ventas_totales()
fecha_hoy = datetime.now().strftime("%Y-%m-%d")
df_hoy = df_todo[df_todo['Fecha'] == fecha_hoy] if not df_todo.empty else pd.DataFrame()

total_dia = df_hoy['Total'].sum() if not df_hoy.empty else 0
st.metric("VENTAS TOTALES DEL DÍA (EN NUBE)", f"${total_dia:,.0f}".replace(",", "."))

st.divider()

# 2. Área de Trabajo (Carrito y Selección)
col_input, col_cart = st.columns([1, 1.2])

with col_input:
    st.subheader("Agregar Producto")
    cat = st.selectbox("Categoría", list(INVENTARIO.keys()))
    med = st.selectbox("Medida", list(INVENTARIO[cat].keys()))
    can = st.number_input("Cantidad", min_value=1, value=1)
    
    if st.button("Añadir al Carrito 🛒", use_container_width=True):
        precio = INVENTARIO[cat][med]
        st.session_state.carrito.append({
            "Categoria": cat,
            "Medida": med,
            "Precio_Unit": precio,
            "Cantidad": can,
            "Total": precio * can
        })
        st.toast(f"Añadido: {med}", icon="➕")

with col_cart:
    st.subheader("Carrito Actual")
    if st.session_state.carrito:
        df_temp = pd.DataFrame(st.session_state.carrito)
        st.table(df_temp[['Medida', 'Cantidad', 'Total']])
        
        monto_carrito = df_temp['Total'].sum()
        st.markdown(f"### Total Carrito: **${monto_carrito:,.0f}**")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("CANCELAR", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        with c2:
            if st.button("TERMINAR VENTA ✅", type="primary", use_container_width=True):
                finalizar_venta_gsheets(st.session_state.carrito)
                st.success("Venta sincronizada con Google Sheets")
                time.sleep(1)
                st.rerun()
    else:
        st.info("El carrito está vacío")
