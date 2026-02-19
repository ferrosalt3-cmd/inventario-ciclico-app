import streamlit as st
import pandas as pd
import json
import re
import io
from datetime import datetime
import os
from sqlalchemy import create_engine, text
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

config = {
    'credentials': {
        'usernames': {
            'admin': {
                'name': 'Administrador',
                'password': '$2b$12$KIXQ4QX8rFzKQFvL3WzHKuTn5q1e1QZ9E9Q7J8e9z0xYyXyXyXyXy',  # admin123
                'role': 'Administrador'
            },
            'invent1': {
                'name': 'Juan Perez',
                'password': '$2b$12$KIXQ4QX8rFzKQFvL3WzHKuTn5q1e1QZ9E9Q7J8e9z0xYyXyXyXyXy',  # invent123
                'role': 'Inventariador'
            }
        }
    },
    'cookie': {
        'name': 'inventario_app',
        'key': 'super_secret_key',
        'expiry_days': 1
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status is False:
    st.error("Usuario o contraseña incorrectos")
    st.stop()

if authentication_status is None:
    st.warning("Por favor ingresa tus credenciales")
    st.stop()

if authentication_status:
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido {name}")
    rol = config['credentials']['usernames'][username]['role']

DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

# Configuración de la página
st.set_page_config(page_title="Inventario Cíclico - Sulfatos", page_icon="🏭")

st.title("🏭 Sistema de Inventario Cíclico - Sulfatos")
st.write("Registro de inventario con base de datos permanente")

# --- CONFIGURACIÓN ARCHIVOS ---
DB_PATH = "inventario.db"
CATALOGO_PATH = "catalogo_productos.json"

# --- LÍNEAS DISPONIBLES ---
LINEAS = [
    "Magnesio", "Magnesio Suelo", "Fierro", "Nitrato de Magnesio", 
    "Zinc Hepta", "Zinc Mono", "Azufre", "Sulfato de Potasio", 
    "Nitrato de Calcio", "Manganeso", "Nitrato de Potasio", "Cobre", 
    "Fosfato Monoamonico", "Acido Borico", "Acido Fosforico", 
    "Quelatos", "Otras"
]

# --- FUNCIONES DEL CATÁLOGO ---
def cargar_catalogo():
    """Carga el catálogo desde archivo JSON o crea uno por defecto"""
    try:
        with open(CATALOGO_PATH, 'r', encoding='utf-8') as f:
            catalogo = json.load(f)
            return catalogo
    except FileNotFoundError:
        catalogo_default = {
            "Sulfato de Magnesio Heptahidratado (PT)": {
                "codigo": "PT0000000093",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Magnesio"
            },
            "Oxido de Magnesio (PT)": {
                "codigo": "PT000000174",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Magnesio"
            },
            "Sulfato de Magnesio Heptahidratado SQM (PT)": {
                "codigo": "PT000000153",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Magnesio"
            },
            "Sulfato de Magnesio Heptahidratado - Quiagral (PT)": {
                "codigo": "PT000000156",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Magnesio"
            },
            "Sulfato de Magnesio Heptahidratado - Industrial (PT)": {
                "codigo": "PT000000191",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Magnesio"
            },
            # Magnesio Suelo
            "Sulfato de Magnesio Suelo (PT)": {
                "codigo": "PT000000245",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Magnesio Suelo"
            },
            "Sulfato de Magnesio Suelo (MRC)": {
                "codigo": "MRC000000015",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Magnesio Suelo"
            },
            # Nitrato de Magnesio
            "Nitrato de Magnesio Hexahidratado (PT)": {
                "codigo": "PT000000230",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Nitrato de Magnesio"
            },
            "Nitrato de Magnesio Hexahidratado (MRC)": {
                "codigo": "MRC000000053",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Nitrato de Magnesio"
            },
            # Fierro
            "Sulfato Ferroso Heptahidratado C/C (PT)": {
                "codigo": "PT000000130",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulfato Ferroso Tetrahidratado (PT)": {
                "codigo": "PT0000000117",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulfato Ferroso Heptahidratado S/C (PT)": {
                "codigo": "PT0000000111",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulfato Ferroso Heptahidratado - Fermagri (PT)": {
                "codigo": "PT0000000114",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulfato Ferroso Heptahidratado - Quiagral (PT)": {
                "codigo": "PT000000138",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulfato Ferroso Heptahidratado S/C USP (PT)": {
                "codigo": "PT0000000113",
                "presentacion": "Tambor x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulfato Ferroso Monohidratado USP (PT)": {
                "codigo": "PT0000000116",
                "presentacion": "Tambor x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            "Sulfato Ferroso Monohidratado (MRC)": {
                "codigo": "MRC000000048",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Fierro"
            },
            "Sulfato Ferroso Heptahidratado Paletizado (PT)": {
                "codigo": "PT000000189",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fierro"
            },
            # Zinc Hepta
            "Sulfato de Zinc Heptahidratado (MRC)": {
                "codigo": "MRC000000021",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Zinc Hepta"
            },
            "Sulfato de Zinc Heptahidratado - Nexa el Porvenir (PT)": {
                "codigo": "PT0000000104",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Hepta"
            },
            "Sulfato de Zinc Heptahidratado (PT)": {
                "codigo": "PT0000000173",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Hepta"
            },
            "Sulfato de Zinc Heptahidratado PT Bigbag x 1 TM (PT)": {
                "codigo": "PT0000000145",
                "presentacion": "Bigbag x 1000 kg",
                "factor": 1000,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Hepta"
            },
            "Sulfato de Zinc Heptahidratado PT Bigbag x 1.5 TM (PT)": {
                "codigo": "PT0000000174",
                "presentacion": "Bigbag x 1500 kg",
                "factor": 1500,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Hepta"
            },
            "Sulfato de Zinc Heptahidratado - Diamond (PT)": {
                "codigo": "PT0000000163",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Hepta"
            },
            "Sulfato de Zinc Heptahidratado - Quiagral (PT)": {
                "codigo": "PT0000000140",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Hepta"
            },
            # Zinc Mono
            "Sulfato de Zinc Monohidratado 1 TM - Exportacion (PT)": {
                "codigo": "PT0000000126",
                "presentacion": "Bigbag x 1000 kg",
                "factor": 1000,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Mono"
            },
            "Sulfato de Zinc Monohidratado - Antamina (PT)": {
                "codigo": "PT000000182",
                "presentacion": "Bigbag x 1000 kg",
                "factor": 1000,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Mono"
            },
            "Sulfato de Zinc Monohidratado AFG (MRC)": {
                "codigo": "MRC000000024",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Zinc Mono"
            },
            "Sulfato de Zinc Monohidratado (PT)": {
                "codigo": "PT000000181",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Zinc Mono"
            },
            # Azufre
            "Azufre Puro Granulado (PT)": {
                "codigo": "PT000000209",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Azufre"
            },
            "Fungisulf WP (PT)": {
                "codigo": "PT000000188",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Azufre"
            },
            "Fungisulf DP-400 (PT)": {
                "codigo": "PT000000187",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Azufre"
            },
            "Azufre Puro Micronizado (PT)": {
                "codigo": "PT000000216",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Azufre"
            },
            # Sulfato de Potasio
            "Sulfato de potasio (MRC)": {
                "codigo": "MRC000000019",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Sulfato de Potasio"
            },
            "Sulfato de potasio (PT)": {
                "codigo": "PT000000134",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Sulfato de Potasio"
            },
            # Nitrato de Calcio
            "Nitrato de Calcio/Granular (PT)": {
                "codigo": "PT000000173",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Nitrato de Calcio"
            },
            "Nitrato de Calcio Tetrahidratado Cristalizado (PT)": {
                "codigo": "PT000000171",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Nitrato de Calcio"
            },
            "Nitrato de Calcio/Amonio (MRC)": {
                "codigo": "MRC000000029",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Nitrato de Calcio"
            },
            # Manganeso
            "Sulfato de Manganeso Monohidratado (PT)": {
                "codigo": "PT0000000094",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Manganeso"
            },
            "Sulfato de Manganeso Monohidratado al 31% (MRC)": {
                "codigo": "MRC000000018",
                "presentacion": "Bigbag x 1000 kg",
                "factor": 1000,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Manganeso"
            },
            # Nitrato de Potasio
            "Nitrato de Potasio (MRC)": {
                "codigo": "MRC000000030",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Nitrato de Potasio"
            },
            "Nitrato de Potasio (PT)": {
                "codigo": "PT000000195",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Nitrato de Potasio"
            },
            # Cobre
            "Oxicloruro de Cobre (MRC)": {
                "codigo": "MRC000000009",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Cobre"
            },
            "Sulfato de Cobre Pentahidratado - Marcobre (MRC)": {
                "codigo": "MRC000000010",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Cobre"
            },
            "Sulfato de Cobre Pentahidratado (PT)": {
                "codigo": "PT000000231",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Cobre"
            },
            "Sulfato de Cobre Pentahidratado - Nacol (MRC)": {
                "codigo": "MRC000000011",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Cobre"
            },
            # Fosfato Monoamonico
            "Fosfato Monoamonico (PT)": {
                "codigo": "PT000000229",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Fosfato Monoamonico"
            },
            "Fosfato Monoamonico (MRC)": {
                "codigo": "MRC000000036",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Fosfato Monoamonico"
            },
            # Acido Borico
            "Acido Borico Granulado (MRC)": {
                "codigo": "MRC000000043",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Acido Borico"
            },
            "Acido Borico (PT)": {
                "codigo": "PT000000244",
                "presentacion": "Sacos x 25 kg",
                "factor": 25,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Acido Borico"
            },
            # Acido Fosforico
            "Acido Fosforico al 85 % - Grado Tecnico (MRC)": {
                "codigo": "MRC000000040",
                "presentacion": "Bidon x 35 kg",
                "factor": 35,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Acido Fosforico"
            },
            "Acido Fosforico (PT)": {
                "codigo": "PT000000133",
                "presentacion": "Bidon x 33.65 kg",
                "factor": 33.65,
                "unidad": "kg",
                "clasificacion": "Producto Terminado",
                "linea": "Acido Fosforico"
            },
            "Acido Fosforico al 85 % - Grado Alimenticio (MRC)": {
                "codigo": "MRC000000001",
                "presentacion": "Bidon x 35 kg",
                "factor": 35,
                "unidad": "kg",
                "clasificacion": "Mercaderia",
                "linea": "Acido Fosforico"
            },
            # Quelatos
            "Organikel Vida Plus (20 lt)": {
                "codigo": "PT000000200",
                "presentacion": "Bidon x 20 lt",
                "factor": 20,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Organikel Vida Plus (1 lt)": {
                "codigo": "PT000000199",
                "presentacion": "Frasco x 1 lt",
                "factor": 1,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Citrato de Magnesio (1 lt)": {
                "codigo": "PT0000000001",
                "presentacion": "Frasco x 1 lt",
                "factor": 1,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Sulcopenta F-4 (20 lt)": {
                "codigo": "PT000000263",
                "presentacion": "Bidon x 20 lt",
                "factor": 20,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Sulcopenta (20 lt)": {
                "codigo": "PT0000000070",
                "presentacion": "Bidon x 20 lt",
                "factor": 20,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Sulcopenta F-4 (1 lt)": {
                "codigo": "PT000000264",
                "presentacion": "Frasco x 1 lt",
                "factor": 1,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Sulcopenta F-3 (1 lt)": {
                "codigo": "PT000000206",
                "presentacion": "Frasco x 1 lt",
                "factor": 1,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Organikel Zinc Plus 25% (1 lt)": {
                "codigo": "PT000000236",
                "presentacion": "Frasco x 1 lt",
                "factor": 1,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Organikel NPK 5-50-5 (1 lt)": {
                "codigo": "PT0000000057",
                "presentacion": "Frasco x 1 lt",
                "factor": 1,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Organikel NPK 5-50-5 (20 lt)": {
                "codigo": "PT0000000044",
                "presentacion": "Bidon x 20 lt",
                "factor": 20,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Organikel PK 0-40-40 (1 lt)": {
                "codigo": "PT000000148",
                "presentacion": "Frasco x 1 lt",
                "factor": 1,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Organikel PK 0-40-40 (20 lt)": {
                "codigo": "PT0000000047",
                "presentacion": "Bidon x 20 lt",
                "factor": 20,
                "unidad": "lt",
                "clasificacion": "Producto Terminado",
                "linea": "Quelatos"
            },
            "Organikel Magnesio 14.5% (20 lt)": {
                "codigo": "PT000000221",
                "presentacion": "Bidon x 20 lt",
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

# --- CONFIGURACIÓN PostgreSQL ---
def get_connection():
    """Devuelve una conexión a PostgreSQL"""
    return engine.connect()

def init_db():
    """Crea la tabla en PostgreSQL si no existe"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inventario (
                id SERIAL PRIMARY KEY,
                fecha_hora TIMESTAMP,
                codigo VARCHAR(100),
                producto VARCHAR(255),
                clasificacion VARCHAR(100),
                linea VARCHAR(100),
                presentacion VARCHAR(100),
                cantidad_unidades INTEGER,
                total_kg_lt NUMERIC,
                unidad_medida VARCHAR(50),
                almacen VARCHAR(100),
                responsable VARCHAR(100),
                observaciones TEXT,
                estado VARCHAR(50) DEFAULT 'Pendiente'
            )
        """))
        conn.commit()

def guardar_registro(datos):
    """Guarda un registro en PostgreSQL"""
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO inventario 
            (fecha_hora, codigo, producto, clasificacion, linea, presentacion, 
             cantidad_unidades, total_kg_lt, unidad_medida, almacen, 
             responsable, observaciones)
            VALUES 
            (:fecha_hora, :codigo, :producto, :clasificacion, :linea, :presentacion,
             :cantidad_unidades, :total_kg_lt, :unidad_medida, :almacen,
             :responsable, :observaciones)
        """), {
            "fecha_hora": datos['fecha_hora'],
            "codigo": datos['codigo'],
            "producto": datos['producto'],
            "clasificacion": datos['clasificacion'],
            "linea": datos['linea'],
            "presentacion": datos['presentacion'],
            "cantidad_unidades": datos['cantidad_unidades'],
            "total_kg_lt": datos['total_kg_lt'],
            "unidad_medida": datos['unidad_medida'],
            "almacen": datos['almacen'],
            "responsable": datos['responsable'],
            "observaciones": datos['observaciones']
        })
        conn.commit()

def obtener_inventario():
    """Obtiene todos los registros desde PostgreSQL"""
    query = text("SELECT * FROM inventario ORDER BY fecha_hora DESC")
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    return df

def eliminar_registro(id_registro):
    """Elimina un registro de la base de datos por ID"""
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM inventario WHERE id = :id"),
            {"id": id_registro}
        )
        conn.commit()

# Inicializar base de datos
init_db()

# --- DATOS PERSONALIZADOS ---
ALMACENES = [
    "Almacen A", "Almacen D", "Almacen E", "Almacen F", "Almacen G",
    "Almacen 13 (Sullana)", "Almacen 3 (Ica)", "Ferrofert (Paita)"
]

# --- INICIALIZAR SESSION STATE ---
if 'linea_filtro' not in st.session_state:
    st.session_state.linea_filtro = "Todas"
if 'producto_sel' not in st.session_state:
    st.session_state.producto_sel = list(CATALOGO_PRODUCTOS.keys())[0]
if 'cantidad_val' not in st.session_state:
    st.session_state.cantidad_val = 0

# SECCIÓN 0: CAMBIAR FECHA DE INVENTARIO
st.header("📅 Fecha del inventario")

usar_fecha_manual = st.checkbox("Cambiar fecha del inventario")

if usar_fecha_manual:
    fecha_manual = st.date_input("Seleccionar fecha")
    fecha_registro = datetime.combine(fecha_manual, datetime.min.time())
else:
    fecha_registro = datetime.now()

# --- SECCIÓN 1: AGREGAR PRODUCTO ---
st.header("➕ Registrar nuevo conteo")

# FILTRO POR LÍNEA
st.subheader("Paso 1: Selecciona la línea de producción")

opciones_linea = ["Todas"] + LINEAS
if st.session_state.linea_filtro == "Todas":
    index_linea = 0
else:
    try:
        index_linea = opciones_linea.index(st.session_state.linea_filtro)
    except ValueError:
        index_linea = 0

linea_anterior = st.session_state.linea_filtro
linea_seleccionada = st.selectbox(
    "Línea",
    options=opciones_linea,
    index=index_linea,
    key="linea_select"
)

# Si cambió la línea, actualizar
if linea_seleccionada != linea_anterior:
    st.session_state.linea_filtro = linea_seleccionada
    if linea_seleccionada == "Todas":
        st.session_state.producto_sel = list(CATALOGO_PRODUCTOS.keys())[0]
    else:
        productos_linea = [n for n, d in CATALOGO_PRODUCTOS.items() if d.get("linea") == linea_seleccionada]
        if productos_linea:
            st.session_state.producto_sel = productos_linea[0]
    st.rerun()

# Filtrar productos por línea
if st.session_state.linea_filtro == "Todas":
    productos_filtrados = list(CATALOGO_PRODUCTOS.keys())
else:
    productos_filtrados = [
        nombre for nombre, datos in CATALOGO_PRODUCTOS.items() 
        if datos.get("linea") == st.session_state.linea_filtro
    ]

if not productos_filtrados:
    st.warning(f"No hay productos en la línea '{st.session_state.linea_filtro}'")
    st.stop()

# SELECCIONAR PRODUCTO
st.subheader("Paso 2: Selecciona el producto")

producto_anterior = st.session_state.producto_sel
try:
    index_producto = productos_filtrados.index(st.session_state.producto_sel)
except ValueError:
    index_producto = 0

producto_desc = st.selectbox(
    "Producto", 
    options=productos_filtrados,
    index=index_producto,
    key="producto_select"
)

# Si cambió el producto, actualizar
if producto_desc != producto_anterior:
    st.session_state.producto_sel = producto_desc
    st.session_state.cantidad_val = 0
    st.rerun()

# OBTENER DATOS DEL PRODUCTO (INTERNO, NO SE MUESTRA)
datos_producto = CATALOGO_PRODUCTOS[st.session_state.producto_sel]
unidad_label = datos_producto.get("unidad", "kg")
clasificacion_auto = datos_producto.get("clasificacion", "")
linea_auto = datos_producto.get("linea", "")
factor = datos_producto.get("factor", 1)

# ENTRADA DE CANTIDAD Y TOTAL
st.subheader("Paso 3: Ingresa los datos del conteo")

col_cant, col_total = st.columns(2)
with col_cant:
    expresion = st.text_input(
        "Cantidad de unidades contadas * (puedes usar + - x)",
        value=str(st.session_state.cantidad_val)
    )

    try:
        expresion_limpia = expresion.replace("x", "*")
        cantidad_unidades = int(eval(expresion_limpia))
        st.session_state.cantidad_val = cantidad_unidades
    except:
        cantidad_unidades = 0

with col_total:
    total_calculado = cantidad_unidades * factor
    st.metric(
        label=f"Total {unidad_label}",
        value=f"{total_calculado:,.0f}"
    )

# FORMULARIO PARA LOS DATOS RESTANTES
with st.form("formulario_inventario"):
    col1, col2 = st.columns(2)
    with col1:
        almacen = st.selectbox("Almacén", ALMACENES, key="form_almacen")
    with col2:
        responsable = st.text_input("Responsable del conteo *", key="form_responsable")
    
    observaciones = st.text_input("Observaciones (opcional)", key="form_obs")
    
    st.caption("Los campos con * son obligatorios")
    guardar = st.form_submit_button("💾 Guardar en base de datos")

if guardar:
    if not responsable:
        st.error("❌ Debes ingresar el responsable del conteo")
    elif cantidad_unidades <= 0:
        st.error("❌ La cantidad debe ser mayor a 0")
    else:
        datos = {
            'fecha_hora': fecha_registro,
            'codigo': datos_producto["codigo"],
            'producto': st.session_state.producto_sel,
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
        st.success(f"✅ Guardado: {st.session_state.producto_sel} | {cantidad_unidades} unidades = {total_calculado} {unidad_label}")
        st.session_state.cantidad_val = 0
        st.rerun()

st.divider()

# --- SECCIÓN 2: MOSTRAR INVENTARIO ---
st.header("📋 Historial de inventario")

df = obtener_inventario()

if not df.empty:
    st.subheader("🔍 Filtros")

    # Asegurar formato datetime
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    # Obtener rango disponible
    fecha_min = df["fecha_hora"].min().date()
    fecha_max = df["fecha_hora"].max().date()

    # Selector de fechas
    rango_fechas = st.date_input(
        "Filtrar por rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    # Siempre comenzamos desde el dataframe original
    df_filtrado = df.copy()

    # --- FILTRO DE FECHAS CORREGIDO ---
    if isinstance(rango_fechas, tuple):

        if len(rango_fechas) == 2:
            inicio, fin = rango_fechas

            df_filtrado = df_filtrado[
                (df_filtrado["fecha_hora"].dt.date >= inicio) &
                (df_filtrado["fecha_hora"].dt.date <= fin)
            ]

        elif len(rango_fechas) == 1:
            unico_dia = rango_fechas[0]

            df_filtrado = df_filtrado[
                df_filtrado["fecha_hora"].dt.date == unico_dia
            ]

    else:
        # Cuando devuelve solo una fecha (no tupla)
        df_filtrado = df_filtrado[
            df_filtrado["fecha_hora"].dt.date == rango_fechas
        ]


    # --- OTROS FILTROS ---
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        filtro_almacen = st.multiselect("Filtrar por Almacén", ALMACENES, key="hist_almacen")

    with col_f2:
        filtro_clasificacion = st.multiselect(
            "Filtrar por Clasificación",
            ["Producto Terminado", "Mercadería"],
            key="hist_clasif"
        )

    with col_f3:
        filtro_linea_hist = st.multiselect("Filtrar por Línea", LINEAS, key="hist_linea")

    if filtro_almacen:
        df_filtrado = df_filtrado[df_filtrado["almacen"].isin(filtro_almacen)]

    if filtro_clasificacion:
        df_filtrado = df_filtrado[df_filtrado["clasificacion"].isin(filtro_clasificacion)]

    if filtro_linea_hist:
        df_filtrado = df_filtrado[df_filtrado["linea"].isin(filtro_linea_hist)]


    # Mostrar resultados
 
    columnas_mostrar = [
        'id', 'fecha_hora', 'codigo', 'producto', 'linea', 'clasificacion',
        'presentacion', 'cantidad_unidades', 'total_kg_lt',
        'unidad_medida', 'almacen', 'responsable', 'observaciones'
    ]

    df_display = df_filtrado[columnas_mostrar].sort_values(
        by="fecha_hora",
        ascending=False
    )

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
    
    def convertir_a_excel(df):
        output = io.BytesIO()
        df_export = df.copy()
        if "id" in df_export.columns:
            df_export = df_export.sort_values(by="id", ascending=True)
        df_export.columns = [
            col.replace("_", " ").title()
            for col in df_export.columns
        ]
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Inventario')
        output.seek(0)
        return output

    excel_file = convertir_a_excel(df_filtrado)

    st.download_button(
        label="Descargar Excel completo",
        data=excel_file,
        file_name="inventario_completo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # --- SECCIÓN ELIMINAR REGISTROS ---
    st.divider()
    st.subheader("🗑️ Eliminar registros del historial")
    if rol == "Administrador":
        if not df.empty:

            # Crear dataframe simplificado para eliminar
            df_eliminar = df[[
                "id",
                "fecha_hora",
                "producto",
                "cantidad_unidades",
                "responsable"
            ]].copy()

            # 🔎 Filtro opcional para facilitar búsqueda
            busqueda = st.text_input("🔎 Buscar por producto o responsable")

            if busqueda:

                # Intentar convertir a número para búsqueda por ID
                try:
                    busqueda_id = int(busqueda)
                    filtro_id = df_eliminar["id"] == busqueda_id
                except:
                    filtro_id = False

                filtro_producto = df_eliminar["producto"].str.contains(busqueda, case=False, na=False)
                filtro_responsable = df_eliminar["responsable"].str.contains(busqueda, case=False, na=False)

                df_eliminar = df_eliminar[
                    filtro_producto |
                    filtro_responsable |
                    filtro_id
                ]

            # Selección múltiple
            ids_seleccionados = st.multiselect(
                "Selecciona uno o más registros para eliminar",
                options=df_eliminar["id"],
                format_func=lambda x: (
                    f"ID {x} - "
                    f"{df_eliminar[df_eliminar['id']==x]['fecha_hora'].values[0]} | "
                    f"{df_eliminar[df_eliminar['id']==x]['producto'].values[0]} | "
                    f"{df_eliminar[df_eliminar['id']==x]['cantidad_unidades'].values[0]} und | "
                    f"{df_eliminar[df_eliminar['id']==x]['responsable'].values[0]}"
                )
            )

            if ids_seleccionados:

                st.warning("⚠️ Esta acción no se puede deshacer")

                confirmar = st.checkbox("Confirmar eliminación múltiple")

                if st.button("Eliminar registros seleccionados", type="primary", disabled=not confirmar):
                    for id_reg in ids_seleccionados:
                        eliminar_registro(id_reg)

                    st.success(f"✅ {len(ids_seleccionados)} registro(s) eliminado(s) correctamente")
                    st.rerun()

            else:
                st.info("ℹ️ Selecciona al menos un registro para habilitar la eliminación")

        else:
            st.info("No hay registros disponibles para eliminar.")
        
else:
    st.info("Aún no hay registros. Agrega tu primer producto arriba.")

# --- ADMINISTRACIÓN: AGREGAR PRODUCTOS ---
if rol == "Administrador":
with st.expander("➕ Administración: Agregar nuevos productos al catálogo"):
    st.write("Aquí puedes agregar productos nuevos sin editar el código:")
    
    with st.form("form_nuevo_producto"):
        st.subheader("Nuevo Producto")
        
        nuevo_nombre = st.text_input("Descripción del producto *", key="admin_nombre")
        nuevo_codigo = st.text_input("Código *", key="admin_codigo")
        
        col_np1, col_np2 = st.columns(2)
        with col_np1:
            nueva_clasificacion = st.selectbox("Clasificación *", ["Producto Terminado", "Mercadería"], key="admin_clasif")
        with col_np2:
            nueva_linea = st.selectbox("Línea *", LINEAS, key="admin_linea")
        
        col_np3, col_np4 = st.columns(2)
        with col_np3:
            nueva_presentacion = st.selectbox(
                "Presentación *",
                ["Sacos x 25 kg", "Bidones x 20 lt", "Bidón x 20 lt", "Bidón x 35 lt", 
                 "Botella x 1 lt", "Bigbag x 1000 kg", "Bigbag x 1250 kg", 
                 "Balde x 25 kg", "Otra"],
                key="admin_presentacion"
            )
        with col_np4:
            nueva_unidad = st.selectbox("Unidad de medida *", ["kg", "lt"], key="admin_unidad")
        
        # Calcular factor internamente según presentación
        if nueva_presentacion == "Otra":
            factor_nuevo = st.number_input("Cantidad por unidad *", min_value=0.1, value=1.0, key="admin_factor_manual")
        else:
            numeros = re.findall(r'(\d+)', nueva_presentacion)
            factor_nuevo = float(numeros[0]) if numeros else 1.0
        
        agregar = st.form_submit_button("Agregar al catálogo")
    
    if agregar:
        if nuevo_nombre and nuevo_codigo:
            CATALOGO_PRODUCTOS[nuevo_nombre] = {
                "codigo": nuevo_codigo,
                "presentacion": nueva_presentacion,
                "factor": factor_nuevo,
                "unidad": nueva_unidad,
                "clasificacion": nueva_clasificacion,
                "linea": nueva_linea
            }
            guardar_catalogo(CATALOGO_PRODUCTOS)
            st.success(f"✅ Producto '{nuevo_nombre}' agregado correctamente")
            st.rerun()
        else:
            st.error("❌ Debes completar todos los campos obligatorios (*)")
    
    # Mostrar catálogo actual
    st.subheader("Catálogo actual")
    catalogo_df = pd.DataFrame.from_dict(CATALOGO_PRODUCTOS, orient='index')
    st.dataframe(catalogo_df, use_container_width=True)
    
    # Eliminar producto
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
            st.success(f"✅ Producto '{producto_a_eliminar}' eliminado.")
            st.rerun()
