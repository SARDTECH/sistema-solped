import streamlit as st
import pandas as pd
from supabase import create_client
import datetime
import time

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO METRO CDMX
# ==========================================
st.set_page_config(page_title="SIGAS - Metro CDMX", page_icon="🚇", layout="wide")

st.markdown("""
    <style>
    /* 🛡️ BOTÓN ANTIPÁNICO: Flecha siempre visible */
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
    }
    [data-testid="stSidebarCollapseButton"] svg { color: #F6831E !important; width: 28px !important; height: 28px !important; }
    .main .block-container { padding-top: 4.5rem !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Identidad Visual Metro CDMX */
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
# 2. CONEXIÓN SUPABASE
# ==========================================
SUPABASE_URL = "https://emickgfmgyzkabmxbmqn.supabase.co"
SUPABASE_KEY = "sb_publishable_WvpRWnDzmRJ-mmrZedWrTA_agKAp_Kg"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- Funciones de Apoyo (Blindaje de Fechas) ---
def procesar_fecha_dashboard(df_col):
    # Convertimos a datetime, forzamos día primero, y quitamos la zona horaria (tz=None)
    fechas = pd.to_datetime(df_col, dayfirst=True, errors='coerce')
    if fechas.dt.tz is not None:
        fechas = fechas.dt.tz_localize(None)
    return fechas

# ==========================================
# 3. BARRA LATERAL
# ==========================================
try: st.sidebar.image("logo m.png", width=140)
except: st.sidebar.title("🚇 METRO")

st.sidebar.title("Subgerencia de Adquisiciones")
menu = st.sidebar.radio("Navegación:", ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar y Editar"))

# ==========================================
# PANTALLA 1: DASHBOARD GERENCIAL
# ==========================================
if menu == "📊 Dashboard Gerencial":
    st.title("📈 Panel de Control Gerencial")
    
    try:
        res = supabase.table("solicitudes_solped").select("*").execute()
        df = pd.DataFrame(res.data)
        
        if df.empty:
            st.info("Sin registros en la base de datos.")
        else:
            # 1. Limpieza técnica de montos y fechas (Blindaje total)
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            df['fecha_limpia'] = procesar_fecha_dashboard(df['fecha_oficio'])
            
            # 2. Configuración de Rango de Consulta en Sidebar
            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Rango de Consulta")
            
            f_validas = df['fecha_limpia'].dropna()
            if not f_validas.empty:
                min_d = f_validas.min().date()
                max_d = f_validas.max().date()
            else:
                min_d = datetime.date.today()
                max_d = datetime.date.today()
            
            rango = st.sidebar.date_input("Periodo (Inicio - Fin):", 
                                          value=(min_d, max_d), 
                                          min_value=min_d, 
                                          max_value=max_d, 
                                          format="DD/MM/YYYY")
            
            # 3. Aplicar Filtro (Evitando el error de zona horaria)
            df_final = df.copy()
            if isinstance(rango, tuple) and len(rango) == 2:
                df_final = df_final[
                    (df_final['fecha_limpia'].dt.date >= rango[0]) & 
                    (df_final['fecha_limpia'].dt.date <= rango[1])
                ]

            # 4. MÉTRICAS FINANCIERAS (Comas y 2 decimales)
            c1, c2, c3 = st.columns(3)
            total_pesos = df_final['monto'].sum()
            promedio = df_final['monto'].mean() if len(df_final) > 0 else 0
            
            c1.metric("Total SOLPEDs", f"{len(df_final)}")
            c2.metric("Inversión Total", f"${total_pesos:,.2f}")
            c3.metric("Ticket Promedio", f"${promedio:,.2f}")
            
            st.divider()
            
            # 5. TABLA MAESTRA (Comas y 2 decimales configurados)
            st.subheader("📋 Listado Maestro de SOLPEDs")
            cols = ['numero_solped', 'area_usuaria', 'descripcion', 'monto', 'fecha_oficio', 'estatus', 'link_pdf']
            existentes = [c for c in cols if c in df_final.columns]
            
            st.dataframe(
                df_final[existentes],
                column_config={
                    "monto": st.column_config.NumberColumn("Monto ($ MXN)", format="$ %,.2f"),
                    "link_pdf": st.column_config.LinkColumn("Expediente Digital"),
                    "numero_solped": "SOLPED #"
                },
                use_container_width=True, hide_index=True
            )
    except Exception as e: st.error(f"Error de sistema: {e}")

# ==========================================
# PANTALLA 2: REGISTRAR SOLPED
# ==========================================
elif menu == "📝 Registrar SOLPED":
    st.title("📝 Registro de Nueva SOLPED")
    with st.form("registro_form"):
        col1, col2 = st.columns(2)
        with col1:
            num = st.text_input("Número de SOLPED / Oficio *")
            area = st.selectbox("Área Usuaria", ["DIRECCIÓN DE INSTALACIONES FIJAS", "DIRECCIÓN DE MANTENIMIENTO DE MATERIAL RODANTE", "CAPITAL HUMANO", "DIRECCIÓN GENERAL DE OPERACIÓN", "OTRO"])
            fec = st.date_input("Fecha de Documento", format="DD/MM/YYYY")
        with col2:
            mon = st.number_input("Monto Estimado ($)", min_value=0.0, step=100.0)
            coord = st.radio("Coordinación", ["CCP (Nacional)", "CCE (Extranjero)"], horizontal=True)
            est = st.selectbox("Estatus Inicial", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
        
        det = st.text_area("Descripción / Justificación")
        lnk = st.text_input("Enlace a Carpeta (Drive/OneDrive)")
        
        if st.form_submit_button("💾 Guardar SOLPED"):
            if not num: st.error("❌ El número es obligatorio.")
            else:
                try:
                    f_db = fec.strftime('%d-%m-%Y')
                    supabase.table("solicitudes_solped").insert({
                        "numero_solped": num, "area_usuaria": area, "monto": mon, 
                        "fecha_oficio": f_db, "coordinacion_asignada": coord, 
                        "estatus": est, "descripcion": det, "link_pdf": lnk
                    }).execute()
                    st.success(f"✅ ¡SOLPED {num} guardada exitosamente!")
                    st.balloons()
                except Exception as e:
                    if "duplicate key" in str(e).lower():
                        st.warning(f"⚠️ La SOLPED {num} ya existe. Búscala en 'Buscar y Editar'.")
                    else: st.error(f"Error: {e}")

# ==========================================
# PANTALLA 3: AGREGAR ARTÍCULOS
# ==========================================
elif menu == "🛒 Agregar Artículos":
    st.title("🛒 Catálogo de Partidas")
    try:
        res = supabase.table("solicitudes_solped").select("id, numero_solped").execute()
        if res.data:
            opciones = {str(s['numero_solped']): s['id'] for s in res.data}
            with st.form("art_form"):
                c1, c2 = st.columns(2)
                with c1:
                    sol_sel = st.selectbox("Asignar a SOLPED:", list(opciones.keys()))
                    cod = st.text_input("Código de Partida *")
                    mto = st.number_input("Costo Unitario ($)", min_value=0.0)
                with c2:
                    tipo = st.radio("Coordinación:", ["CCP (Nacional)", "CCE (Extranjero)"])
                    dsc = st.text_input("Descripción breve")
                
                if st.form_submit_button("🚀 Registrar Artículo"):
                    if cod:
                        supabase.table("partidas_codigos").insert({
                            "solped_id": opciones[sol_sel], "codigo_articulo": cod.upper(), 
                            "descripcion": dsc, "monto": mto, "coordinacion": tipo
                        }).execute()
                        st.success(f"✅ Partida registrada."); st.balloons()
                    else: st.error("Falta código.")
    except Exception as e: st.error(f"Error: {e}")

# ==========================================
# PANTALLA 4: BUSCAR Y EDITAR
# ==========================================
elif menu == "🔍 Buscar y Editar":
    st.title("🔍 Localizador y Edición")
    if 'bus_id' not in st.session_state: st.session_state.bus_id = ""
    col_s, col_b = st.columns([3, 1])
    with col_s: t = st.text_input("Número de SOLPED a buscar:")
    with col_b:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Buscar"): st.session_state.bus_id = t
            
    if st.session_state.bus_id:
        res = supabase.table("solicitudes_solped").select("*").eq("numero_solped", st.session_state.bus_id).execute()
        if res.data:
            item = res.data[0]
            with st.form("edit_form"):
                ca, cb = st.columns(2)
                with ca:
                    n_m = st.number_input("Monto ($)", value=float(item.get('monto', 0)))
                    n_l = st.text_input("Enlace PDF", value=item.get('link_pdf', ''))
                with cb:
                    n_e = st.selectbox("Estatus", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
                if st.form_submit_button("💾 Guardar y Cerrar"):
                    supabase.table("solicitudes_solped").update({"monto": n_m, "link_pdf": n_l, "estatus": n_e}).eq("id", item['id']).execute()
                    st.success("✅ Cambios aplicados."); st.balloons(); time.sleep(2); st.session_state.bus_id = ""; st.rerun()
        else: st.error("❌ No encontrado.")
