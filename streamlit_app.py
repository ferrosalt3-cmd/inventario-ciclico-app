import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Inventario Cíclico", page_icon="📦")

# Título principal
st.title("📦 Sistema de Inventario Cíclico")

# Descripción
st.write("Registra y consulta tu inventario de forma periódica")

# --- SECCIÓN 1: AGREGAR PRODUCTO ---
st.header("➕ Registrar nuevo conteo")

# Creamos el formulario
with st.form("formulario_inventario"):
    
    # Campos del formulario
    producto = st.text_input("Nombre del producto")
    ubicacion = st.selectbox(
        "Ubicación", 
        ["Almacén Principal", "Almacén Secundario", "Tienda", "Otro"]
    )
    cantidad = st.number_input("Cantidad contada", min_value=0, value=0)
    responsable = st.text_input("Responsable del conteo")
    
    # Botón de guardar
    guardar = st.form_submit_button("💾 Guardar registro")

# --- SECCIÓN 2: MOSTRAR INVENTARIO ---
st.header("📋 Historial de inventario")

# Creamos datos de ejemplo (después conectaremos base de datos real)
if 'inventario' not in st.session_state:
    st.session_state.inventario = []

# Si presionaron guardar, agregamos el dato
if guardar:
    nuevo_registro = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Producto": producto,
        "Ubicación": ubicacion,
        "Cantidad": cantidad,
        "Responsable": responsable
    }
    st.session_state.inventario.append(nuevo_registro)
    st.success(f"✅ Registrado: {producto} - {cantidad} unidades")

# Mostramos la tabla
if st.session_state.inventario:
    df = pd.DataFrame(st.session_state.inventario)
    st.dataframe(df, use_container_width=True)
    
    # Botón para descargar
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar Excel/CSV",
        csv,
        "inventario.csv",
        "text/csv"
    )
else:
    st.info("Aún no hay registros. Agrega tu primer producto arriba.")