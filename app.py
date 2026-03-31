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
    if st.session_state.edi_m: st.session_state.edi_m = f"{limpiar_dinero(st.session_state.edi_m):,.2f}"

# ==========================================
# 4. BARRA LATERAL (SIDEBAR)
# ==========================================
try: st.sidebar.image("logo m.png", width=140)
except: st.sidebar.title("🚇 METRO")

st.sidebar.title("Subgerencia de Adquisiciones")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navegación del Sistema:", ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar y Editar"))

# ==========================================
# PANTALLA 1: DASHBOARD GERENCIAL
# ==========================================
if menu == "📊 Dashboard Gerencial":
    st.title("📈 Panel de Control Gerencial")
    try:
        res = supabase.table("solicitudes_solped").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            st.info("No hay datos registrados aún.")
        else:
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0).astype(float)
            df['fecha_dt'] = df['fecha_oficio'].apply(limpiar_fecha_segura)
            
            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Rango de Consulta")
            df_con_fecha = df.dropna(subset=['fecha_dt'])
            
            if not df_con_fecha.empty:
                min_f, max_f = df_con_fecha['fecha_dt'].min().date(), df_con_fecha['fecha_dt'].max().date()
                rango = st.sidebar.date_input("Seleccione Periodo:", value=(min_f, max_f), min_value=min_f, max_value=max_f, format="DD/MM/YYYY")
                df_final = df_con_fecha[(df_con_fecha['fecha_dt'].dt.date >= rango[0]) & (df_con_fecha['fecha_dt'].dt.date <= rango[1])] if isinstance(rango, tuple) and len(rango) == 2 else df_con_fecha
            else: df_final = df

            c1, c2, c3 = st.columns(3)
            c1.metric("Total SOLPEDs", f"{len(df_final)}")
            c2.metric("Inversión Total", f"${df_final['monto'].sum():,.2f} MXN")
            c3.metric("Ticket Promedio", f"${(df_final['monto'].mean() if len(df_final) > 0 else 0):,.2f} MXN")
            st.divider()
            
            st.subheader("📋 Listado Maestro de SOLPEDs")
            cols = ['numero_solped', 'area_usuaria', 'descripcion', 'monto', 'fecha_oficio', 'estatus', 'link_pdf']
            existentes = [c for c in cols if c in df_final.columns]
            st.dataframe(df_final[existentes], column_config={"monto": st.column_config.NumberColumn("Monto ($ MXN)", format="$ %,.2f"), "link_pdf": st.column_config.LinkColumn("Expediente Digital"), "numero_solped": "SOLPED #"}, use_container_width=True, hide_index=True)
    except Exception as e: st.error(f"Error al cargar Dashboard: {e}")

# ==========================================
# PANTALLA 2: REGISTRAR SOLPED
# ==========================================
elif menu == "📝 Registrar SOLPED":
    st.title("📝 Registro de Nueva SOLPED")
    st.info("💡 Consejo: Escribe el monto y da clic en otra casilla para que se pongan las comas automáticamente.")
    
    # 🌟 Formulario liberado (Sin 'st.form') para permitir edición en vivo
    col1, col2 = st.columns(2)
    with col1:
        num = st.text_input("Número de SOLPED / Oficio *")
        area = st.selectbox("Área Usuaria", ["DIRECCIÓN DE INSTALACIONES FIJAS", "DIRECCIÓN DE MANTENIMIENTO DE MATERIAL RODANTE", "CAPITAL HUMANO", "DIRECCIÓN GENERAL DE OPERACIÓN", "OTRO"])
        fec = st.date_input("Fecha de Documento", format="DD/MM/YYYY")
    with col2:
        if "reg_m" not in st.session_state: st.session_state.reg_m = ""
        # 🌟 AQUÍ ESTÁ EL DISPARADOR EN VIVO (on_change=format_reg)
        mon_str = st.text_input("Monto Inicial ($ MXN)", key="reg_m", on_change=format_reg, placeholder="Ej. 12332302 (Las comas se pondrán solas)")
        coord = st.radio("Coordinación", ["CCP (Nacional)", "CCE (Extranjero)", "CCP y CCE (Ambas)"], horizontal=True)
        est = st.selectbox("Estatus Inicial", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
    
    det = st.text_area("Descripción / Justificación del Gasto")
    lnk = st.text_input("Enlace a Carpeta (Drive/OneDrive)")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Guardar en Base de Datos"):
        if not num: st.error("❌ El número de SOLPED es obligatorio.")
        else:
            try:
                f_db = fec.strftime('%d-%m-%Y')
                monto_limpio = limpiar_dinero(st.session_state.reg_m)
                supabase.table("solicitudes_solped").insert({"numero_solped": num, "area_usuaria": area, "monto": monto_limpio, "fecha_oficio": f_db, "coordinacion_asignada": coord, "estatus": est, "descripcion": det, "link_pdf": lnk}).execute()
                st.success(f"✅ ¡SOLPED {num} registrada exitosamente por ${monto_limpio:,.2f}!")
                st.balloons()
                st.session_state.reg_m = "" # Limpiamos el monto tras guardar
            except Exception as e:
                if "duplicate key" in str(e).lower(): st.warning(f"⚠️ La SOLPED **{num}** ya existe. Ve a 'Buscar y Editar'.")
                else: st.error(f"🚨 Error técnico: {e}")

# ==========================================
# PANTALLA 3: AGREGAR ARTÍCULOS
# ==========================================
elif menu == "🛒 Agregar Artículos":
    st.title("🛒 Catálogo de Partidas por Oficio")
    try:
        res = supabase.table("solicitudes_solped").select("id, numero_solped").execute()
        if res.data:
            opciones = {str(s['numero_solped']): s['id'] for s in res.data}
            
            c1, c2 = st.columns(2)
            with c1:
                sol_sel = st.selectbox("Vincular a SOLPED:", list(opciones.keys()))
                cod = st.text_input("Código de Partida / Artículo *")
                if "art_m" not in st.session_state: st.session_state.art_m = ""
                mto_str = st.text_input("Monto de la Partida ($ MXN)", key="art_m", on_change=format_art, placeholder="Escribe y da clic fuera...")
            with c2:
                tipo = st.radio("Segmentación de Compra:", ["CCP (Nacional)", "CCE (Extranjero)", "CCP y CCE (Ambas)"])
                dsc = st.text_input("Descripción del Bien/Servicio")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Registrar Artículo"):
                if cod:
                    monto_partida = limpiar_dinero(st.session_state.art_m)
                    supabase.table("partidas_codigos").insert({"solped_id": opciones[sol_sel], "codigo_articulo": cod.upper(), "descripcion": dsc, "monto": monto_partida, "coordinacion": tipo}).execute()
                    st.success(f"✅ Partida {cod.upper()} añadida por ${monto_partida:,.2f}.")
                    st.balloons()
                    st.session_state.art_m = ""
    except Exception as e: st.error(f"Error: {e}")

# ==========================================
# PANTALLA 4: BUSCAR Y EDITAR
# ==========================================
elif menu == "🔍 Buscar y Editar":
    st.title("🔍 Localizador de Expedientes")
    if 'busqueda_id' not in st.session_state: st.session_state.busqueda_id = ""

    col_srch, col_btn = st.columns([3, 1])
    with col_srch: txt = st.text_input("Ingrese el número exacto de SOLPED a editar:")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Localizar"): st.session_state.busqueda_id = txt
            
    if st.session_state.busqueda_id:
        res = supabase.table("solicitudes_solped").select("*").eq("numero_solped", st.session_state.busqueda_id).execute()
        if res.data:
            item = res.data[0]
            st.success(f"✅ Expediente de la SOLPED {st.session_state.busqueda_id} listo para edición.")
            
            # Si es la primera vez que buscamos esta SOLPED, cargamos su monto a la memoria
            if 'edi_loaded' not in st.session_state or st.session_state.edi_loaded != st.session_state.busqueda_id:
                st.session_state.edi_m = f"{float(item.get('monto', 0)):,.2f}"
                st.session_state.edi_loaded = st.session_state.busqueda_id

            ca, cb = st.columns(2)
            with ca:
                new_m_str = st.text_input("Actualizar Monto ($ MXN)", key="edi_m", on_change=format_edit)
                new_l = st.text_input("Actualizar Link Drive", value=item.get('link_pdf', ''))
            with cb:
                lista_estatus = ["EN PROCESO", "COMPLETADA", "CANCELADA"]
                estatus_actual = item.get('estatus', 'EN PROCESO')
                idx_estatus = lista_estatus.index(estatus_actual) if estatus_actual in lista_estatus else 0
                new_e = st.selectbox("Cambiar Estatus", lista_estatus, index=idx_estatus)
            
            new_d = st.text_area("Actualizar Descripción / Justificación", value=item.get('descripcion', ''))
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Actualizar y Cerrar"):
                monto_actualizado = limpiar_dinero(st.session_state.edi_m)
                supabase.table("solicitudes_solped").update({"monto": monto_actualizado, "link_pdf": new_l, "estatus": new_e, "descripcion": new_d}).eq("id", item['id']).execute()
                st.success("✅ Cambios guardados correctamente.")
                st.balloons()
                time.sleep(2)
                st.session_state.busqueda_id = ""
                st.rerun()
        else: st.error("❌ No se encontró el registro. Verifique el número de SOLPED.")
