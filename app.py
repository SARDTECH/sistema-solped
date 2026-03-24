import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Sistema SOLPED - Metro CDMX", page_icon="🚇", layout="wide")

# --- CONEXIÓN A LA NUBE (SUPABASE) ---
SUPABASE_URL = "https://emickgfmgyzkabmxbmqn.supabase.co"
SUPABASE_KEY = "sb_publishable_WvpRWnDzmRJ-mmrZedWrTA_agKAp_Kg"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- MENÚ DE NAVEGACIÓN ---
st.sidebar.image("https://logodownload.org/wp-content/uploads/2021/11/metro-cdmx-logo-0.png", width=120) 
st.sidebar.title("Menú Principal")
menu = st.sidebar.radio(
    "Navegación:",
    ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar SOLPED")
)

# ==========================================
# PANTALLA 1: DASHBOARD GERENCIAL
# ==========================================
if menu == "📊 Dashboard Gerencial":
    st.title("📈 Panel de Control Gerencial")
    
    # Descargar datos de la nube
    try:
        res_solpeds = supabase.table("solicitudes_solped").select("*").execute()
        df = pd.DataFrame(res_solpeds.data)
        
        if df.empty:
            st.info("No hay datos para mostrar todavía.")
        else:
            # FIX DE FECHAS: dayfirst=True para leer las fechas del Metro
            df['fecha_limpia'] = pd.to_datetime(df['fecha_oficio'], dayfirst=True, errors='coerce')
            
            # Filtros
            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Filtros")
            
            # Obtener años válidos
            if pd.api.types.is_datetime64_any_dtype(df['fecha_limpia']):
                años_disp = df['fecha_limpia'].dt.year.dropna().unique()
                años = sorted(años_disp.astype(int), reverse=True)
            else:
                años = []
                
            meses_nombres = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                             7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
