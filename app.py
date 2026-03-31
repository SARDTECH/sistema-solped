import streamlit as st
import pandas as pd
from supabase import create_client
import datetime
import time

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO METRO
# ==========================================
st.set_page_config(page_title="SIGAS - Metro CDMX", page_icon="🚇", layout="wide")

st.markdown("""
    <style>
    /* 🛡️ BOTÓN ANTIPÁNICO */
    [data-testid="stSidebarCollapseButton"] {
        display: block !important;
        visibility: visible !important;
        position: fixed !important;
        top: 15px !important;
        left: 15px !important;
        background-color: white !important;
        border: 2px solid #F6831E !important; 
        border-radius: 8px !important;
        z-index: 999999 !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2) !important;
        padding: 5px !important;
    }
    [data-testid="stSidebarCollapseButton"] svg { color: #F6831E !important; width: 28px !important; height: 28px !important; }

    .main .block-container { padding-top: 4.5rem !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

    :root { --metro-naranja: #F6831E; --metro-oscuro: #2C2C2C; }
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 4px solid var(--metro-naranja); }
    h1, h2, h3 { color: var(--metro-oscuro) !important; font-family: 'Arial', sans-serif; }
    [data-testid="stMetricValue"] { color: var(--metro-naranja) !important; font-weight: 900 !important; }
    
    .stButton>button { 
        background-color: var(--metro-naranja); color: white; border-radius: 6px; 
        border: none; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: var(--metro-oscuro); color: var(--metro-naranja); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN A BASE DE DATOS (SUPABASE)
# ==========================================
SUPABASE_URL = "https://emickgfmgyzkabmxbmqn.supabase.co"
SUPABASE_KEY = "sb_publishable_WvpRWnDzmRJ-mmrZedWrTA_agKAp_Kg"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# 3. FUNCIONES DE APOYO Y CALLBACKS (AUTO-FORMATO)
# ==========================================
def limpiar_fecha_segura(f_str):
    try:
        dt = pd.to_datetime(f_str, dayfirst=True, errors='coerce')
        if dt is not pd.NaT and dt.tzinfo is not None: dt = dt.tz_localize(None)
        return dt
    except: return pd.NaT

def limpiar_dinero(val_str):
    try:
        val_limpio = str(val_str).replace('$', '').replace(',', '').strip()
        return float(val_limpio)
    except: return 0.0

# 🌟 MAGIA EN VIVO: Estas funciones se disparan al salir de la casilla
def format_reg():
    if st.session_state.reg_m: st.session_state.reg_m = f"{limpiar_dinero(st.session_state.reg_m):,.2f}"
def format_art():
    if st.session_state.art_m: st.session_state.art_m = f"{limpiar_dinero(st.session_state.art_m):,.2f}"
def format_edit():
    if st.session_state.edi_m: st.session_state.edi_m = f"{limpiar_dinero(st
