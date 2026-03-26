import streamlit as st
import pandas as pd
from supabase import create_client
import datetime
import time

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO INSTITUCIONAL
# ==========================================
st.set_page_config(page_title="SIGAS - Metro CDMX", page_icon="🚇", layout="wide")

st.markdown("""
    <style>
    /* 🛡️ BOTÓN DE MENÚ SIEMPRE VISIBLE */
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
    .main .block-container { padding-top: 4rem !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Identidad Metro */
    :root { --metro-naranja: #F6831E; --metro-oscuro: #2C2C2C; }
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 4px solid var(--metro-naranja); }
    h1, h2, h3 { color: var(--metro-oscuro) !important; font-family: 'Arial', sans-serif; }
    [data-testid="stMetricValue"] { color: var(--metro-naranja) !important; font-weight: 900 !important; }
    
    .stButton>button { 
        background-color: var(--metro-naranja); color: white; border-radius: 6px; 
        font-weight: bold; width: 100%; border: none;
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

# ==========================================
# 3. NAVEGACIÓN Y SIDEBAR
# ==========================================
try: st.sidebar.image("logo m.png", width=140)
except: st.sidebar.title("🚇 METRO")

st.sidebar.title("Subgerencia de Adquisiciones")
menu = st.sidebar.radio("Navegación:", ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar y Editar"))

# ==========================================
# PANTALLA 1: DASHBOARD GERENCIAL (CORREGIDA)
# ==========================================
if menu == "📊 Dashboard Gerencial":
    st.title("📈 Panel de Control Gerencial")
    
    try:
        # Traer datos
        res = supabase.table("solicitudes_solped").select("*").execute()
        df = pd.DataFrame(res.data)
        
        if df.empty:
            st.info("No hay datos en la nube.")
        else:
            # LIMPIEZA CRÍTICA DE DATOS
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            
            # Conversión de fecha Robusta (Solución al error .dt)
            df['fecha_limpia'] = pd.to_datetime(df['fecha_oficio'], dayfirst=True, errors='coerce')
            # Quitamos zona horaria para evitar conflictos de comparación
            df['fecha_limpia'] = df['fecha_limpia'].dt.tz_localize(None)
            
            # Eliminar filas donde la fecha no se pudo procesar para el filtro
            df_con_fecha = df.dropna(subset=['fecha_limpia'])
            
            # --- RANGO DE CONSULTA EN SIDEBAR ---
            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Rango de Consulta")
            
            if not df_con_fecha.empty:
                min_f = df_con_fecha['fecha_limpia'].min().date()
                max_f = df_con_fecha['fecha_limpia'].max().date()
                
                rango = st.sidebar.date_input(
                    "Seleccione Periodo:",
                    value=(min_f, max_f),
                    min_value=min_f,
                    max_value=max_f,
                    format="DD/MM/YYYY"
                )
                
                # Filtrar DataFrame
                if isinstance(rango, tuple) and len(rango) == 2:
                    df_filtrado = df_con_fecha[
                        (df_con_fecha['fecha_limpia'].dt.date >= rango[0]) & 
                        (df_con_fecha['fecha_limpia'].dt.date <= rango[1])
                    ]
                else:
                    df_filtrado = df_con_fecha
            else:
                df_filtrado = df
                st.sidebar.warning("No se detectaron fechas válidas.")

            # MÉTRICAS CON FORMATO CONTABLE (Comas y 2 decimales)
            c1, c2, c3 = st.columns(3)
            inv_total = df_filtrado['monto'].sum()
            ticket_prom = df_filtrado['monto'].mean() if not df_filtrado.empty else 0
            
            c1.metric("Total SOLPEDs", f"{len(df_filtrado)}")
            c2.metric("Inversión Total", f"${inv_total:,.2f}")
            c3.metric("Ticket Promedio", f"${ticket_prom:,.2f}")
            
            st.divider()
            
            # TABLA MAESTRA CON FORMATO $ MXN
            st.subheader("📋 Listado Maestro de SOLPEDs")
            cols_ok = ['numero_solped', 'area_usuaria', 'descripcion', 'monto', 'fecha_oficio', 'estatus', 'link_pdf']
            existentes = [c for c in cols_ok if c in df_filtrado.columns]
            
            st.dataframe(
                df_filtrado[existentes],
                column_config={
                    "monto": st.column_config.NumberColumn("Monto ($ MXN)", format="$ %,.2f"),
                    "link_pdf": st.column_config.LinkColumn("Expediente"),
                    "numero_solped": "SOLPED #"
                },
                use_container_width=True, hide_index=True
            )
            
    except Exception as e:
        st.error(f"Error de sistema: {e}")

# ==========================================
# PANTALLA 2: REGISTRAR (ESCUDO ANTI-DUPLICADOS)
# ==========================================
elif menu == "📝 Registrar SOLPED":
    st.title("📝 Registro de Nueva SOLPED")
    with st.form("reg_form"):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Número de SOLPED / Oficio *")
            a = st.selectbox("Área Usuaria", ["DIRECCIÓN DE INSTALACIONES FIJAS", "DIRECCIÓN DE MANTENIMIENTO DE MATERIAL RODANTE", "CAPITAL HUMANO", "DIRECCIÓN GENERAL DE OPERACIÓN", "OTRO"])
            f = st.date_input("Fecha de Documento", format="DD/MM/YYYY")
        with c2:
            m = st.number_input("Monto Estimado ($)", min_value=0.0, step=100.0)
            co = st.radio("Coordinación", ["CCP (Nacional)", "CCE (Extranjero)"], horizontal=True)
            es = st.selectbox("Estatus", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
        
        d = st.text_area("Descripción")
        l = st.text_input("Enlace a Carpeta")
        
        if st.form_submit_button("💾 Guardar"):
            if not n: st.error("Número obligatorio.")
            else:
                try:
                    f_db = f.strftime('%d-%m-%Y')
                    supabase.table("solicitudes_solped").insert({"numero_solped": n, "area_usuaria": a, "monto": m, "fecha_oficio": f_db, "coordinacion_asignada": co, "estatus": es, "descripcion": d, "link_pdf": l}).execute()
                    st.success("✅ Guardado con éxito."); st.balloons()
                except Exception as e:
                    if "duplicate key" in str(e).lower():
                        st.warning(f"⚠️ La SOLPED {n} ya existe. Ve a 'Buscar y Editar'.")
                    else: st.error(f"Error: {e}")

# ==========================================
# PANTALLAS RESTANTES (SIMPLIFICADAS PARA ESTABILIDAD)
# ==========================================
elif menu == "🛒 Agregar Artículos":
    st.title("🛒 Catálogo de Partidas")
    try:
        res = supabase.table("solicitudes_solped").select("id, numero_solped").execute()
        if res.data:
            ops = {str(s['numero_solped']): s['id'] for s in res.data}
            with st.form("art_f"):
                cx, cy = st.columns(2)
                with cx:
                    sel = st.selectbox("SOLPED:", list(ops.keys()))
                    cod = st.text_input("Código de Partida *")
                    mt = st.number_input("Monto Partida ($)", min_value=0.0)
                with cy:
                    tip = st.radio("Tipo:", ["CCP (Nacional)", "CCE (Extranjero)"])
                    ds = st.text_input("Descripción Partida")
                if st.form_submit_button("🚀 Guardar"):
                    supabase.table("partidas_codigos").insert({"solped_id": ops[sel], "codigo_articulo": cod.upper(), "descripcion": ds, "monto": mt, "coordinacion": tip}).execute()
                    st.success("✅ Partida añadida."); st.balloons()
    except Exception as e: st.error(f"Error: {e}")

elif menu == "🔍 Buscar y Editar":
    st.title("🔍 Localizador")
    if 'b_id' not in st.session_state: st.session_state.b_id = ""
    cs, cb = st.columns([3, 1])
    with cs: tx = st.text_input("SOLPED a buscar:")
    with cb:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Buscar"): st.session_state.b_id = tx
    if st.session_state.b_id:
        res = supabase.table("solicitudes_solped").select("*").eq("numero_solped", st.session_state.b_id).execute()
        if res.data:
            it = res.data[0]
            with st.form("ed_f"):
                c_a, c_b = st.columns(2)
                with c_a: nm = st.number_input("Monto ($)", value=float(it.get('monto', 0)))
                with c_b: ne = st.selectbox("Estatus", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
                nl = st.text_input("Link Drive", value=it.get('link_pdf', ''))
                if st.form_submit_button("💾 Actualizar"):
                    supabase.table("solicitudes_solped").update({"monto": nm, "link_pdf": nl, "estatus": ne}).eq("id", it['id']).execute()
                    st.success("✅ Cambios guardados."); time.sleep(1.5); st.session_state.b_id = ""; st.rerun()
        else: st.error("No encontrado.")
