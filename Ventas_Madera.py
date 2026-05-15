import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Sistema de Ventas Madera", layout="wide")

# Inventario (Igual al original)
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

def get_file_name():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    return f"ventas_{fecha_hoy}.csv"

def cargar_datos():
    nombre_archivo = get_file_name()
    if os.path.exists(nombre_archivo):
        df = pd.read_csv(nombre_archivo, sep=";")
        return df[df['Categoria'] != "--- TOTAL GENERAL ---"]
    return pd.DataFrame(columns=["Categoria", "Medida", "Precio_Unit", "Cantidad_Total", "Venta_Total"])

def guardar_venta(categoria, medida, cant, precio):
    nombre_archivo = get_file_name()
    df = cargar_datos()
    
    monto_actual = cant * precio
    
    filtro = (df['Categoria'] == categoria) & (df['Medida'] == medida)
    if not df[filtro].empty:
        df.loc[filtro, 'Cantidad_Total'] += cant
        df.loc[filtro, 'Venta_Total'] = df.loc[filtro, 'Cantidad_Total'] * precio
    else:
        nueva = pd.DataFrame([{"Categoria": categoria, "Medida": medida, "Precio_Unit": precio, 
                               "Cantidad_Total": cant, "Venta_Total": monto_actual}])
        df = pd.concat([df, nueva], ignore_index=True)
    
    # Recalcular Gran Total
    gran_total_dia = df['Venta_Total'].sum()
    fila_total = pd.DataFrame([{"Categoria": "--- TOTAL GENERAL ---", "Medida": "---", 
                                "Precio_Unit": 0, "Cantidad_Total": 0, "Venta_Total": gran_total_dia}])
    
    df_final = pd.concat([df, fila_total], ignore_index=True)
    df_final.to_csv(nombre_archivo, index=False, sep=";", encoding='utf-8-sig')

# --- INTERFAZ STREAMLIT ---
st.title("🌲 Sistema de Ventas - Control Diario")

# Cargar datos actuales
df_ventas = cargar_datos()
total_dia = df_ventas['Venta_Total'].sum()

# Label de ventas del día (Métrica destacada)
st.metric(label="VENTAS TOTALES DEL DÍA", value=f"${total_dia:,.0f}".replace(",", "."))

st.divider()

# Formulario de entrada
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    grupo = st.selectbox("Categoría", list(INVENTARIO.keys()))
with col2:
    medida = st.selectbox("Medida", list(INVENTARIO[grupo].keys()))
with col3:
    cantidad = st.number_input("Cantidad", min_value=1, step=1, value=1)

if st.button("REGISTRAR VENTA", use_container_width=True, type="primary"):
    precio_unit = INVENTARIO[grupo][medida]
    monto_operacion = cantidad * precio_unit
    
    # Guardar en el CSV
    guardar_venta(grupo, medida, cantidad, precio_unit)
    
    # 1. Mensaje flotante en la esquina (Toast)
    st.toast(f'✅ Venta registrada: ${monto_operacion:,.0f}', icon='💰')
    
    # 2. Mensaje de confirmación en el cuerpo de la página
    st.success(f"Operación exitosa: Se han vendido {cantidad} unidades de {medida} por un total de ${monto_operacion:,.0f}")
    
    # Esperar un momento antes de recargar para que el usuario vea el mensaje
    import time
    time.sleep(4)
    st.rerun()

# Mostrar Tabla de ventas
st.subheader("Resumen de ventas de hoy")
if not df_ventas.empty:
    # Formatear para visualización
    df_mostrar = df_ventas.copy()
    df_mostrar['Precio_Unit'] = df_mostrar['Precio_Unit'].map('${:,.0f}'.format)
    df_mostrar['Venta_Total'] = df_mostrar['Venta_Total'].map('${:,.0f}'.format)
    st.table(df_mostrar)
else:
    st.info("Aún no hay ventas registradas hoy.")
