import streamlit as st
import pandas as pd
import sqlite3
import json
import re
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Inventario Cíclico - Sulfatos", page_icon="🏭")

# Título principal
st.title("🏭 Sistema de Inventario Cíclico - Sulfatos")

st.write("Registro de inventario con base de datos permanente")

# --- CONFIGURACIÓN ARCHIVOS ---
DB_PATH = "inventario.db"
CATALOGO_PATH = "catalogo_productos.json"

# --- FUNCIONES DEL CATÁLOGO ---
def cargar_catalogo():
    """Carga el catálogo desde archivo JSON o crea uno por defecto"""
    try:
        with open(CATALOGO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Catálogo inicial con tus 5 productos
        catalogo_default = {
            "Sulfato de Magnesio Heptahidratado (PT)": {
                "codigo": "PT0000000093",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg"
            },
            "Nitrato de Magnesio Hexahidratado (MRC)": {
                "codigo": "MRC000000053",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg"
            },
            "Sulfato Ferroso Tetrahidratado (PT)": {
                "codigo": "PT0000000117",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg"
            },
            "Sulfato de Potasio (MRC)": {
                "codigo": "MRC000000019",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg"
            },
            "Sulfato Feroso Heptahidratado C/C (PT)": {
                "codigo": "PT000000130",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg"
            }
        }
        guardar_catalogo(catalogo_default)
        return catalogo_default

def guardar_catalogo(catalogo):
    """Guarda el catálogo en archivo JSON"""
    with open(CATALOGO_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalogo, f, ensure_ascii=False, indent=2)

# Cargar catálogo
CATALOGO_PRODUCTOS = cargar_catalogo()

# --- CONFIGURACIÓN SQLITE ---
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
            cantidad_unidades INTEGER,
            total_kg_lt REAL,
            unidad_medida TEXT,
            almacen TEXT,
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
        (fecha_hora, codigo, producto, clasificacion, presentacion, cantidad_unidades, 
         total_kg_lt, unidad_medida, almacen, responsable, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datos['fecha_hora'], datos['codigo'], datos['producto'], 
        datos['clasificacion'], datos['presentacion'], datos['cantidad_unidades'],
        datos['total_kg_lt'], datos['unidad_medida'], datos['almacen'], 
        datos['responsable'], datos['observaciones']
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

# Selectbox FUERA del formulario para que actualice visualmente
producto_desc = st.selectbox(
    "Selecciona el producto", 
    options=list(CATALOGO_PRODUCTOS.keys()),
    key="producto_selector"
)

# Obtener datos del producto seleccionado (esto actualiza automáticamente)
datos_producto = CATALOGO_PRODUCTOS[producto_desc]
es_kg = datos_producto["unidad"] == "kg"
unidad_label = "kg" if es_kg else "lt"

# Mostrar datos del producto seleccionado (actualización visual)
col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.text_input("Código", value=datos_producto["codigo"], disabled=True, key="display_codigo")
with col_info2:
    st.text_input("Presentación", value=datos_producto["presentacion"], disabled=True, key="display_presentacion")
with col_info3:
    st.text_input("Unidad", value=unidad_label.upper(), disabled=True, key="display_unidad")

st.divider()

# Formulario para el resto de datos
with st.form("formulario_inventario"):
    
    col3, col4 = st.columns(2)
    with col3:
        clasificacion = st.selectbox("Clasificación", CLASIFICACIONES)
    with col4:
        almacen = st.selectbox("Almacén", ALMACENES)
    
    # Cantidad de unidades y cálculo automático
    col5, col6 = st.columns(2)
    with col5:
        cantidad_unidades = st.number_input(
            f"Cantidad de unidades contadas", 
            min_value=0, 
            value=0,
            help="Número de sacos, bidones, etc."
        )
    with col6:
        total_calculado = cantidad_unidades * datos_producto["factor"]
        st.number_input(
            f"Total {unidad_label}", 
            value=float(total_calculado), 
            disabled=True,
            help=f"Cálculo: {cantidad_unidades} × {datos_producto['factor']} = {total_calculado} {unidad_label}"
        )
    
    responsable = st.text_input("Responsable del conteo")
    observaciones = st.text_input("Observaciones (opcional)")
    
    guardar = st.form_submit_button("💾 Guardar en base de datos")

# --- PROCESAR GUARDADO ---
if guardar:
    datos = {
        'fecha_hora': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'codigo': datos_producto["codigo"],
        'producto': producto_desc,
        'clasificacion': clasificacion,
        'presentacion': datos_producto["presentacion"],
        'cantidad_unidades': cantidad_unidades,
        'total_kg_lt': total_calculado,
        'unidad_medida': unidad_label,
        'almacen': almacen,
        'responsable': responsable,
        'observaciones': observaciones
    }
    guardar_registro(datos)
    st.success(f"✅ Guardado: {producto_desc} | {cantidad_unidades} unidades = {total_calculado} {unidad_label}")
    st.balloons()

# --- SECCIÓN 2: MOSTRAR INVENTARIO ---
st.header("📋 Historial de inventario")

df = obtener_inventario()

if not df.empty:
    st.subheader("🔍 Filtros")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_almacen = st.multiselect("Filtrar por Almacén", ALMACENES)
    with col_f2:
        filtro_clasificacion = st.multiselect("Filtrar por Clasificación", CLASIFICACIONES)
    
    df_filtrado = df.copy()
    if filtro_almacen:
        df_filtrado = df_filtrado[df_filtrado["almacen"].isin(filtro_almacen)]
    if filtro_clasificacion:
        df_filtrado = df_filtrado[df_filtrado["clasificacion"].isin(filtro_clasificacion)]
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    st.subheader("📊 Resumen")
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        st.metric("Total registros", len(df_filtrado))
    with col_r2:
        st.metric("Total unidades", int(df_filtrado["cantidad_unidades"].sum()))
    with col_r3:
        total_kg = df_filtrado[df_filtrado["unidad_medida"] == "kg"]["total_kg_lt"].sum()
        st.metric("Total KG", f"{total_kg:,.0f}")
    with col_r4:
        total_lt = df_filtrado[df_filtrado["unidad_medida"] == "lt"]["total_kg_lt"].sum()
        st.metric("Total LT", f"{total_lt:,.0f}")
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar Excel completo",
        csv,
        f"inventario_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )
else:
    st.info("Aún no hay registros. Agrega tu primer producto arriba.")

# --- ADMINISTRACIÓN: AGREGAR PRODUCTOS ---
with st.expander("➕ Administración: Agregar nuevos productos al catálogo"):
    st.write("Aquí puedes agregar productos nuevos sin editar el código:")
    
    with st.form("nuevo_producto"):
        st.subheader("Nuevo Producto")
        nuevo_nombre = st.text_input("Descripción del producto *")
        nuevo_codigo = st.text_input("Código *")
        
        col_np1, col_np2 = st.columns(2)
        with col_np1:
            nueva_presentacion = st.selectbox(
                "Presentación",
                ["Sacos x 25 kg", "Bidones x 20 lt", "Bigbag x 1000 kg", 
                 "Botella x 1 lt", "Bidón x 35 kg", "Balde x 25 kg", 
                 "Bigbag x 1250 kg", "Otra"]
            )
        with col_np2:
            nueva_unidad = st.selectbox("Unidad de medida", ["kg", "lt"])
        
        # Calcular factor automáticamente
        if nueva_presentacion == "Otra":
            factor = st.number_input("Cantidad por unidad", min_value=0.1, value=1.0)
        else:
            numeros = re.findall(r'(\d+)', nueva_presentacion)
            factor = float(numeros[0]) if numeros else 1.0
            st.number_input("Cantidad por unidad (automático)", value=factor, disabled=True)
        
        agregar = st.form_submit_button("Agregar al catálogo")
    
    if agregar:
        if nuevo_nombre and nuevo_codigo:
            CATALOGO_PRODUCTOS[nuevo_nombre] = {
                "codigo": nuevo_codigo,
                "presentacion": nueva_presentacion,
                "factor": factor,
                "unidad": nueva_unidad
            }
            guardar_catalogo(CATALOGO_PRODUCTOS)
            st.success(f"✅ Producto '{nuevo_nombre}' agregado. Recarga la página para verlo en el dropdown.")
        else:
            st.error("❌ Debes completar nombre y código")
    
    # Mostrar catálogo actual
    st.subheader("Catálogo actual")
    catalogo_df = pd.DataFrame.from_dict(CATALOGO_PRODUCTOS, orient='index')
    st.dataframe(catalogo_df, use_container_width=True)