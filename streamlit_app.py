import streamlit as st
import pandas as pd
import sqlite3
import json
import re
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Inventario Cíclico - Sulfatos", page_icon="🏭")

st.title("🏭 Sistema de Inventario Cíclico - Sulfatos")
st.write("Registro de inventario con base de datos permanente")

# --- CONFIGURACIÓN ARCHIVOS ---
DB_PATH = "inventario.db"
CATALOGO_PATH = "catalogo_productos.json"

# --- RESETEAR BASE DE DATOS (desarrollo) ---
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
if os.path.exists(CATALOGO_PATH):
    os.remove(CATALOGO_PATH)

# --- LÍNEAS DISPONIBLES ---
LINEAS = [
    "Magnesio", "Magnesio Suelo", "Fierro", "Nitrato de Magnesio", 
    "Zinc Hepta", "Zinc Mono", "Azufre", "Sulfato de Potasio", 
    "Nitrato de Calcio", "Manganeso", "Nitrato de Potasio", "Cobre", 
    "Fosfato Monoamónico", "Ácido Bórico", "Ácido Fosfórico", 
    "Quelatos", "Otras Mercaderías"
]

# --- FUNCIONES DEL CATÁLOGO ---
def cargar_catalogo():
    """Carga el catálogo desde archivo JSON o crea uno por defecto"""
    try:
        with open(CATALOGO_PATH, 'r', encoding='utf-8') as f:
            catalogo = json.load(f)
            # Agregar Sulcopenta si no existe
            if "Sulcopenta F-4" not in catalogo:
                catalogo["Sulcopenta F-4"] = {
                    "codigo": "PT000000263",
                    "presentacion": "Bidón x 20 lt",
                    "factor": 20,
                    "unidad": "lt",
                    "clasificacion": "Producto Terminado",
                    "linea": "Quelatos"
                }
                guardar_catalogo(catalogo)
            return catalogo
    except FileNotFoundError:
        # Catálogo inicial con tus 5 productos + Sulcopenta
        catalogo_default = {
            "Sulfato de Magnesio Heptahidratado (PT)": {
                "codigo": "PT0000000093",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Magnesio"
            },
            "Nitrato de Magnesio Hexahidratado (MRC)": {
                "codigo": "MRC000000053",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercadería",
                "linea": "Nitrato de Magnesio"
            },
            "Sulfato Ferroso Tetrahidratado (PT)": {
                "codigo": "PT0000000117",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulfato de Potasio (MRC)": {
                "codigo": "MRC000000019",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercadería",
                "linea": "Sulfato de Potasio"
            },
            "Sulfato Feroso Heptahidratado C/C (PT)": {
                "codigo": "PT000000130",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulcopenta F-4": {
                "codigo": "PT000000263",
                "presentacion": "Bidón x 20 lt",
                "factor": 20,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
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
            linea TEXT,
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
        (fecha_hora, codigo, producto, clasificacion, linea, presentacion, cantidad_unidades, 
         total_kg_lt, unidad_medida, almacen, responsable, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datos['fecha_hora'], datos['codigo'], datos['producto'], 
        datos['clasificacion'], datos['linea'], datos['presentacion'], 
        datos['cantidad_unidades'], datos['total_kg_lt'], datos['unidad_medida'], 
        datos['almacen'], datos['responsable'], datos['observaciones']
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
ALMACENES = [
    "Almacén A", "Almacén D", "Almacén E", "Almacén F", "Almacén G",
    "Almacén 13 (Sullana)", "Almacén 3 (Ica)", "Ferrofert (Paita)"
]

# --- SECCIÓN 1: AGREGAR PRODUCTO ---
st.header("➕ Registrar nuevo conteo")

# FILTRO POR LÍNEA PRIMERO
st.subheader("Paso 1: Selecciona la línea de producción")
linea_seleccionada = st.selectbox(
    "Línea",
    options=["Todas"] + LINEAS,
    key="filtro_linea"
)

# Filtrar productos por línea
if linea_seleccionada == "Todas":
    productos_filtrados = list(CATALOGO_PRODUCTOS.keys())
else:
    productos_filtrados = [
        nombre for nombre, datos in CATALOGO_PRODUCTOS.items() 
        if datos.get("linea") == linea_seleccionada
    ]

if not productos_filtrados:
    st.warning(f"No hay productos en la línea '{linea_seleccionada}'")
    st.stop()

# SELECCIONAR PRODUCTO FILTRADO
st.subheader("Paso 2: Selecciona el producto")
producto_desc = st.selectbox(
    "Producto", 
    options=productos_filtrados,
    key="producto_selector"
)

# Obtener datos actualizados
datos_producto = CATALOGO_PRODUCTOS[producto_desc]
unidad_label = datos_producto.get("unidad", "kg")
clasificacion_auto = datos_producto.get("clasificacion", "")
linea_auto = datos_producto.get("linea", "")

# Mostrar datos del producto seleccionado
st.subheader("📋 Información del producto:")
col_info1, col_info2 = st.columns(2)
with col_info1:
    st.text_input("Código", value=datos_producto["codigo"], disabled=True, key="disp_codigo")
    st.text_input("Clasificación", value=clasificacion_auto, disabled=True, key="disp_clasif")
with col_info2:
    st.text_input("Presentación", value=datos_producto["presentacion"], disabled=True, key="disp_pres")
    st.text_input("Línea", value=linea_auto, disabled=True, key="disp_linea")

st.text_input("Unidad de medida", value=unidad_label.upper(), disabled=True, key="disp_unidad")

st.divider()

with st.form("formulario_inventario"):
    
    col1, col2 = st.columns(2)
    with col1:
        almacen = st.selectbox("Almacén", ALMACENES, key="sel_almacen")
    with col2:
        responsable = st.text_input("Responsable del conteo *", key="inp_responsable")
    
    col3, col4 = st.columns(2)
    with col3:
        cantidad_unidades = st.number_input(
            "Cantidad de unidades contadas *", 
            min_value=0, 
            value=0,
            key="inp_cantidad",
            help="Número de sacos, bidones, etc."
        )
    with col4:
        factor = datos_producto.get("factor", 1)
        total_calculado = cantidad_unidades * factor
        st.number_input(
            f"Total {unidad_label} (automático)", 
            value=float(total_calculado), 
            disabled=True,
            key="disp_total",
            help=f"Cálculo: {cantidad_unidades} × {factor} = {total_calculado} {unidad_label}"
        )
    
    observaciones = st.text_input("Observaciones (opcional)", key="inp_obs")
    
    st.caption("Los campos con * son obligatorios")
    guardar = st.form_submit_button("💾 Guardar en base de datos")

if guardar:
    if not responsable:
        st.error("❌ Debes ingresar el responsable del conteo")
    elif cantidad_unidades <= 0:
        st.error("❌ La cantidad debe ser mayor a 0")
    else:
        datos = {
            'fecha_hora': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'codigo': datos_producto["codigo"],
            'producto': producto_desc,
            'clasificacion': clasificacion_auto,
            'linea': linea_auto,
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

# --- SECCIÓN 2: MOSTRAR INVENTARIO ---
st.header("📋 Historial de inventario")

df = obtener_inventario()

if not df.empty:
    st.subheader("🔍 Filtros")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_almacen = st.multiselect("Filtrar por Almacén", ALMACENES, key="filtro_alm_hist")
    with col_f2:
        filtro_clasificacion = st.multiselect("Filtrar por Clasificación", ["Producto Terminado", "Mercadería"], key="filtro_clas_hist")
    with col_f3:
        filtro_linea_hist = st.multiselect("Filtrar por Línea", LINEAS, key="filtro_linea_hist")
    
    df_filtrado = df.copy()
    if filtro_almacen:
        df_filtrado = df_filtrado[df_filtrado["almacen"].isin(filtro_almacen)]
    if filtro_clasificacion:
        df_filtrado = df_filtrado[df_filtrado["clasificacion"].isin(filtro_clasificacion)]
    if filtro_linea_hist:
        df_filtrado = df_filtrado[df_filtrado["linea"].isin(filtro_linea_hist)]
    
    # Seleccionar columnas para mostrar
    columnas_mostrar = ['fecha_hora', 'codigo', 'producto', 'linea', 'clasificacion', 
                       'presentacion', 'cantidad_unidades', 'total_kg_lt', 'unidad_medida', 
                       'almacen', 'responsable', 'observaciones']
    df_display = df_filtrado[columnas_mostrar] if all(col in df_filtrado.columns for col in columnas_mostrar) else df_filtrado
    
    st.dataframe(df_display, use_container_width=True)
    
    st.subheader("📊 Resumen")
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
        st.metric("Total registros", len(df_filtrado))
    with col_r2:
        total_unidades = df_filtrado["cantidad_unidades"].sum() if "cantidad_unidades" in df_filtrado.columns else 0
        st.metric("Total unidades", int(total_unidades))
    with col_r3:
        total_kg = df_filtrado[df_filtrado["unidad_medida"] == "kg"]["total_kg_lt"].sum() if "unidad_medida" in df_filtrado.columns else 0
        st.metric("Total KG", f"{total_kg:,.0f}")
    with col_r4:
        total_lt = df_filtrado[df_filtrado["unidad_medida"] == "lt"]["total_kg_lt"].sum() if "unidad_medida" in df_filtrado.columns else 0
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
        nuevo_nombre = st.text_input("Descripción del producto *", key="new_nombre")
        nuevo_codigo = st.text_input("Código *", key="new_codigo")
        
        col_np1, col_np2 = st.columns(2)
        with col_np1:
            nueva_clasificacion = st.selectbox("Clasificación *", ["Producto Terminado", "Mercadería"], key="new_clasif")
        with col_np2:
            nueva_linea = st.selectbox("Línea *", LINEAS, key="new_linea")
        
        col_np3, col_np4 = st.columns(2)
        with col_np3:
            nueva_presentacion = st.selectbox(
                "Presentación *",
                ["Sacos x 25 kg", "Bidones x 20 lt", "Bidón x 20 lt", "Bidón x 35 lt", 
                 "Botella x 1 lt", "Bigbag x 1000 kg", "Bigbag x 1250 kg", 
                 "Balde x 25 kg", "Otra"],
                key="new_presentacion"
            )
        with col_np4:
            nueva_unidad = st.selectbox("Unidad de medida *", ["kg", "lt"], key="new_unidad")
        
        # Calcular factor automáticamente basado en la presentación Y unidad
        if nueva_presentacion == "Otra":
            factor = st.number_input("Cantidad por unidad *", min_value=0.1, value=1.0, key="new_factor_manual")
        else:
            # Extraer número de la presentación
            numeros = re.findall(r'(\d+)', nueva_presentacion)
            if numeros:
                factor = float(numeros[0])
                # Verificar consistencia con unidad seleccionada
                tiene_lt = "lt" in nueva_presentacion.lower()
                if tiene_lt and nueva_unidad != "lt":
                    st.warning("⚠️ La presentación indica 'lt' pero seleccionaste unidad 'kg'")
                elif not tiene_lt and nueva_unidad == "lt" and "kg" in nueva_presentacion.lower():
                    st.warning("⚠️ La presentación indica 'kg' pero seleccionaste unidad 'lt'")
            else:
                factor = 1.0
            
            st.number_input("Cantidad por unidad (automático)", value=factor, disabled=True, key="new_factor_auto")
        
        agregar = st.form_submit_button("Agregar al catálogo")
    
    if agregar:
        if nuevo_nombre and nuevo_codigo:
            # Determinar factor final
            if nueva_presentacion == "Otra":
                factor_final = factor
            else:
                numeros = re.findall(r'(\d+)', nueva_presentacion)
                factor_final = float(numeros[0]) if numeros else 1.0
            
            CATALOGO_PRODUCTOS[nuevo_nombre] = {
                "codigo": nuevo_codigo,
                "presentacion": nueva_presentacion,
                "factor": factor_final,
                "unidad": nueva_unidad,
                "clasificacion": nueva_clasificacion,
                "linea": nueva_linea
            }
            guardar_catalogo(CATALOGO_PRODUCTOS)
            st.success(f"✅ Producto '{nuevo_nombre}' agregado correctamente")
            st.balloons()
        else:
            st.error("❌ Debes completar todos los campos obligatorios (*)")
    
    # Mostrar catálogo actual
    st.subheader("Catálogo actual")
    catalogo_df = pd.DataFrame.from_dict(CATALOGO_PRODUCTOS, orient='index')
    st.dataframe(catalogo_df, use_container_width=True)
    
    # Opción para eliminar producto (nueva)
    st.subheader("🗑️ Eliminar producto del catálogo")
    producto_a_eliminar = st.selectbox(
        "Selecciona producto a eliminar",
        options=list(CATALOGO_PRODUCTOS.keys()),
        key="del_producto"
    )
    if st.button("Eliminar producto seleccionado", type="secondary"):
        if producto_a_eliminar in CATALOGO_PRODUCTOS:
            del CATALOGO_PRODUCTOS[producto_a_eliminar]
            guardar_catalogo(CATALOGO_PRODUCTOS)
            st.success(f"✅ Producto '{producto_a_eliminar}' eliminado. Recarga la página.")