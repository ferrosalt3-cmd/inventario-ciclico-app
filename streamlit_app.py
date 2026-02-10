import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Inventario Cíclico - Sulfatos", page_icon="🏭")

# Título principal
st.title("🏭 Sistema de Inventario Cíclico - Sulfatos")

# Descripción
st.write("Registro de inventario de sulfatos y productos químicos")

# --- DATOS PERSONALIZADOS ---
ALMACENES = ["Almacén A", "Almacén D", "Almacén E", "Almacén F", "Almacén G"]
PRESENTACIONES = [
    "Sacos x 25 kg",
    "Bidones x 20 Lt",
    "Bigbag x 1000 kg",
    "Botella x 1 Lt",
    "Bidón x 35 kg",
    "Balde x 25 kg",
    "Bigbag x 1250 kg"
]
CLASIFICACIONES = ["Producto Terminado", "Mercadería"]

# --- SECCIÓN 1: AGREGAR PRODUCTO ---
st.header("➕ Registrar nuevo conteo")

with st.form("formulario_inventario"):
    
    # Fila 1: Código y Producto
    col1, col2 = st.columns(2)
    with col1:
        codigo = st.text_input("Código de producto", placeholder="Ej: SUL-001")
    with col2:
        producto = st.text_input("Nombre del producto", placeholder="Ej: Sulfato de Cobre")
    
    # Fila 2: Clasificación y Presentación
    col3, col4 = st.columns(2)
    with col3:
        clasificacion = st.selectbox("Clasificación", CLASIFICACIONES)
    with col4:
        presentacion = st.selectbox("Presentación", PRESENTACIONES)
    
    # Fila 3: Almacén y Cantidad
    col5, col6 = st.columns(2)
    with col5:
        almacen = st.selectbox("Almacén", ALMACENES)
    with col6:
        cantidad = st.number_input("Cantidad contada", min_value=0, value=0)
    
    # Fila 4: Responsable y Observaciones
    col7, col8 = st.columns(2)
    with col7:
        responsable = st.text_input("Responsable del conteo")
    with col8:
        observaciones = st.text_input("Observaciones (opcional)")
    
    # Botón de guardar
    guardar = st.form_submit_button("💾 Guardar registro")

# --- SECCIÓN 2: MOSTRAR INVENTARIO ---
st.header("📋 Historial de inventario")

# Inicializar inventario en memoria
if 'inventario' not in st.session_state:
    st.session_state.inventario = []

# Guardar nuevo registro
if guardar:
    nuevo_registro = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Código": codigo,
        "Producto": producto,
        "Clasificación": clasificacion,
        "Presentación": presentacion,
        "Almacén": almacen,
        "Cantidad": cantidad,
        "Responsable": responsable,
        "Observaciones": observaciones
    }
    st.session_state.inventario.append(nuevo_registro)
    st.success(f"✅ Registrado: {codigo} - {producto} ({cantidad} unidades)")

# Mostrar tabla solo si hay datos
if st.session_state.inventario:
    df = pd.DataFrame(st.session_state.inventario)
    
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
        df_filtrado = df_filtrado[df_filtrado["Almacén"].isin(filtro_almacen)]
    if filtro_clasificacion:
        df_filtrado = df_filtrado[df_filtrado["Clasificación"].isin(filtro_clasificacion)]
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Estadísticas rápidas (solo si hay datos después de filtrar)
    if not df_filtrado.empty:
        st.subheader("📊 Resumen")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Total registros", len(df_filtrado))
        with col_r2:
            st.metric("Total unidades", int(df_filtrado["Cantidad"].sum()))
        with col_r3:
            st.metric("Productos únicos", df_filtrado["Código"].nunique())
    
    # Descargar
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar Excel/CSV",
        csv,
        f"inventario_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )
else:
    st.info("Aún no hay registros. Agrega tu primer producto arriba.")