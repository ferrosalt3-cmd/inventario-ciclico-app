import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# Configuración de la página
st.set_page_config(page_title="Inventario Cíclico - Sulfatos", page_icon="🏭")

# Título principal
st.title("🏭 Sistema de Inventario Cíclico - Sulfatos")

st.write("Registro de inventario con base de datos permanente")

# --- CATÁLOGO DE PRODUCTOS MAESTRO ---
CATALOGO_PRODUCTOS = {
    "Sulfato de Magnesio Heptahidratado (PT)": {
        "codigo": "PT0000000093",
        "presentacion": "Sacos x 25 kg"
    },
    "Nitrato de Magnesio Hexahidratado (MRC)": {
        "codigo": "MRC000000053",
        "presentacion": "Sacos x 25 kg"
    },
    "Sulfato Ferroso Tetrahidratado (PT)": {
        "codigo": "PT0000000117",
        "presentacion": "Sacos x 25 kg"
    },
    "Sulfato de Potasio (MRC)": {
        "codigo": "MRC000000019",
        "presentacion": "Sacos x 25 kg"
    },
    "Sulfato Feroso Heptahidratado C/C (PT)": {
        "codigo": "PT000000130",
        "presentacion": "Sacos x 25 kg"
    }
}

# --- CONFIGURACIÓN SQLITE ---
DB_PATH = "inventario.db"

def init_db():
    """Crea la base de datos si no existe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT,
            codigo TEXT,
            producto TEXT,
            clasificacion TEXT,
            presentacion TEXT,
            almacen TEXT,
            cantidad INTEGER,
            responsable TEXT,
            observaciones TEXT,
            estado TEXT DEFAULT 'Pendiente'
        )
    ''')
    conn.commit()
    conn.close()

def guardar_registro(datos):
    """Guarda un registro en la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inventario 
        (fecha_hora, codigo, producto, clasificacion, presentacion, almacen, cantidad, responsable, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datos['fecha_hora'], datos['codigo'], datos['producto'], 
        datos['clasificacion'], datos['presentacion'], datos['almacen'],
        datos['cantidad'], datos['responsable'], datos['observaciones']
    ))
    conn.commit()
    conn.close()

def obtener_inventario():
    """Obtiene todos los registros"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM inventario ORDER BY fecha_hora DESC", conn)
    conn.close()
    return df

# Inicializar base de datos
init_db()

# --- DATOS PERSONALIZADOS ---
ALMACENES = ["Almacén A", "Almacén D", "Almacén E", "Almacén F", "Almacén G"]
CLASIFICACIONES = ["Producto Terminado", "Mercadería"]

# --- SECCIÓN 1: AGREGAR PRODUCTO ---
st.header("➕ Registrar nuevo conteo")

with st.form("formulario_inventario"):
    
    # Selección de producto (descripción)
    producto_desc = st.selectbox(
        "Selecciona el producto", 
        options=list(CATALOGO_PRODUCTOS.keys()),
        help="El código y presentación se llenarán automáticamente"
    )
    
    # Datos que se autocompletan
    col1, col2 = st.columns(2)
    with col1:
        codigo_auto = CATALOGO_PRODUCTOS[producto_desc]["codigo"]
        st.text_input("Código", value=codigo_auto, disabled=True, key="codigo_display")
    with col2:
        presentacion_auto = CATALOGO_PRODUCTOS[producto_desc]["presentacion"]
        st.text_input("Presentación", value=presentacion_auto, disabled=True, key="presentacion_display")
    
    # Resto del formulario
    col3, col4 = st.columns(2)
    with col3:
        clasificacion = st.selectbox("Clasificación", CLASIFICACIONES)
    with col4:
        almacen = st.selectbox("Almacén", ALMACENES)
    
    col5, col6 = st.columns(2)
    with col5:
        cantidad = st.number_input("Cantidad contada", min_value=0, value=0)
    with col6:
        responsable = st.text_input("Responsable del conteo")
    
    observaciones = st.text_input("Observaciones (opcional)")
    
    guardar = st.form_submit_button("💾 Guardar en base de datos")

# --- PROCESAR GUARDADO ---
if guardar:
    datos = {
        'fecha_hora': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'codigo': codigo_auto,
        'producto': producto_desc,
        'clasificacion': clasificacion,
        'presentacion': presentacion_auto,
        'almacen': almacen,
        'cantidad': cantidad,
        'responsable': responsable,
        'observaciones': observaciones
    }
    guardar_registro(datos)
    st.success(f"✅ Guardado en base de datos: {producto_desc} ({cantidad} unidades)")

# --- SECCIÓN 2: MOSTRAR INVENTARIO ---
st.header("📋 Historial de inventario (Base de datos)")

# Recargar datos
df = obtener_inventario()

if not df.empty:
    # Filtros
    st.subheader("🔍 Filtros")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_almacen = st.multiselect("Filtrar por Almacén", ALMACENES)
    with col_f2:
        filtro_clasificacion = st.multiselect("Filtrar por Clasificación", CLASIFICACIONES)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if filtro_almacen:
        df_filtrado = df_filtrado[df_filtrado["almacen"].isin(filtro_almacen)]
    if filtro_clasificacion:
        df_filtrado = df_filtrado[df_filtrado["clasificacion"].isin(filtro_clasificacion)]
    
    # Mostrar tabla
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Estadísticas
    st.subheader("📊 Resumen")
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric("Total registros", len(df_filtrado))
    with col_r2:
        st.metric("Total unidades", int(df_filtrado["cantidad"].sum()))
    with col_r3:
        st.metric("Productos únicos", df_filtrado["producto"].nunique())
    
    # Descargar
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar Excel completo",
        csv,
        f"inventario_completo_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )
else:
    st.info("Aún no hay registros en la base de datos. Agrega tu primer producto arriba.")

# --- ADMINISTRACIÓN ---
with st.expander("⚙️ Administración (Agregar más productos al catálogo)"):
    st.write("Para agregar más productos al catálogo, edita la variable CATALOGO_PRODUCTOS en el código.")
    st.code("""
CATALOGO_PRODUCTOS = {
    "Nuevo Producto": {
        "codigo": "CODIGO-001",
        "presentacion": "Presentación X"
    }
}
    """)