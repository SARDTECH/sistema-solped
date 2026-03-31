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
# 3. FUNCIONES DE APOYO (FECHAS Y DINERO)
# ==========================================
def limpiar_fecha_segura(f_str):
    try:
        dt = pd.to_datetime(f_str, dayfirst=True, errors='coerce')
        if dt is not pd.NaT and dt.tzinfo is not None:
            dt = dt.tz_localize(None)
        return dt
    except:
        return pd.NaT

# 🌟 NUEVA FUNCIÓN: Transforma el texto de Bubu (con comas) en número real para la base de datos
def limpiar_dinero(val_str):
    try:
        # Quitamos espacios, signos de dólar y comas
        val_limpio = str(val_str).replace('$', '').replace(',', '').strip()
        return float(val_limpio)
    except:
        return 0.0

# ==========================================
# 4. BARRA LATERAL (SIDEBAR)
# ==========================================
try: st.sidebar.image("logo m.png", width=140)
except: st.sidebar.title("🚇 METRO")

st.sidebar.title("Subgerencia de Adquisiciones")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación del Sistema:",
    ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar y Editar")
)

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
                min_f = df_con_fecha['fecha_dt'].min().date()
                max_f = df_con_fecha['fecha_dt'].max().date()
                
                rango = st.sidebar.date_input("Seleccione Periodo:", value=(min_f, max_f), min_value=min_f, max_value=max_f, format="DD/MM/YYYY")
                
                if isinstance(rango, tuple) and len(rango) == 2:
                    df_final = df_con_fecha[(df_con_fecha['fecha_dt'].dt.date >= rango[0]) & (df_con_fecha['fecha_dt'].dt.date <= rango[1])]
                else:
                    df_final = df_con_fecha
            else:
                df_final = df

            c1, c2, c3 = st.columns(3)
            c1.metric("Total SOLPEDs", f"{len(df_final)}")
            c2.metric("Inversión Total", f"${df_final['monto'].sum():,.2f} MXN")
            c3.metric("Ticket Promedio", f"${(df_final['monto'].mean() if len(df_final) > 0 else 0):,.2f} MXN")
            
            st.divider()
            
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
    except Exception as e:
        st.error(f"Error al cargar Dashboard: {e}")

# ==========================================
# PANTALLA 2: REGISTRAR SOLPED
# ==========================================
elif menu == "📝 Registrar SOLPED":
    st.title("📝 Registro de Nueva SOLPED")
    st.info("Complete los campos para dar de alta un nuevo expediente en la nube.")
    
    with st.form("registro_form"):
        col1, col2 = st.columns(2)
        with col1:
            num = st.text_input("Número de SOLPED / Oficio *")
            area = st.selectbox("Área Usuaria", ["DIRECCIÓN DE INSTALACIONES FIJAS", "DIRECCIÓN DE MANTENIMIENTO DE MATERIAL RODANTE", "CAPITAL HUMANO", "DIRECCIÓN GENERAL DE OPERACIÓN", "OTRO"])
            fec = st.date_input("Fecha de Documento", format="DD/MM/YYYY")
        with col2:
            # 🌟 HACK: Caja de texto libre para que Bubu pueda poner comas
            mon_str = st.text_input("Monto Inicial ($ MXN)", placeholder="Ej. 12,332,302.00")
            
            coord = st.radio("Coordinación", ["CCP (Nacional)", "CCE (Extranjero)", "CCP y CCE (Ambas)"], horizontal=True)
            est = st.selectbox("Estatus Inicial", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
        
        det = st.text_area("Descripción / Justificación del Gasto")
        lnk = st.text_input("Enlace a Carpeta (Drive/OneDrive)")
        
        if st.form_submit_button("💾 Guardar en Base de Datos"):
            if not num:
                st.error("❌ El número de SOLPED es obligatorio.")
            else:
                try:
                    f_db = fec.strftime('%d-%m-%Y')
                    # Procesamos el monto para quitar las comas antes de guardar
                    monto_limpio = limpiar_dinero(mon_str)
                    
                    supabase.table("solicitudes_solped").insert({
                        "numero_solped": num, "area_usuaria": area, "monto": monto_limpio,
                        "fecha_oficio": f_db, "coordinacion_asignada": coord,
                        "estatus": est, "descripcion": det, "link_pdf": lnk
                    }).execute()
                    st.success(f"✅ ¡SOLPED {num} registrada exitosamente por ${monto_limpio:,.2f}!")
                    st.balloons()
                except Exception as e:
                    if "duplicate key" in str(e).lower():
                        st.warning(f"⚠️ La SOLPED **{num}** ya existe. Ve a 'Buscar y Editar'.")
                    else:
                        st.error(f"🚨 Error técnico: {e}")

# ==========================================
# PANTALLA 3: AGREGAR ARTÍCULOS
# ==========================================
elif menu == "🛒 Agregar Artículos":
    st.title("🛒 Catálogo de Partidas por Oficio")
    try:
        res = supabase.table("solicitudes_solped").select("id, numero_solped").execute()
        if res.data:
            opciones = {str(s['numero_solped']): s['id'] for s in res.data}
            with st.form("art_form"):
                c1, c2 = st.columns(2)
                with c1:
                    sol_sel = st.selectbox("Vincular a SOLPED:", list(opciones.keys()))
                    cod = st.text_input("Código de Partida / Artículo *")
                    
                    # 🌟 HACK: Caja de texto para comas
                    mto_str = st.text_input("Monto de la Partida ($ MXN)", placeholder="Ej. 1,500.00")
                with c2:
                    tipo = st.radio("Segmentación de Compra:", ["CCP (Nacional)", "CCE (Extranjero)", "CCP y CCE (Ambas)"])
                    dsc = st.text_input("Descripción del Bien/Servicio")
                
                if st.form_submit_button("🚀 Registrar Artículo"):
                    if cod:
                        monto_partida = limpiar_dinero(mto_str)
                        supabase.table("partidas_codigos").insert({
                            "solped_id": opciones[sol_sel], "codigo_articulo": cod.upper(),
                            "descripcion": dsc, "monto": monto_partida, "coordinacion": tipo
                        }).execute()
                        st.success(f"✅ Partida {cod.upper()} añadida por ${monto_partida:,.2f}.")
                        st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# PANTALLA 4: BUSCAR Y EDITAR
# ==========================================
elif menu == "🔍 Buscar y Editar":
    st.title("🔍 Localizador de Expedientes")
    if 'busqueda_id' not in st.session_state: st.session_state.busqueda_id = ""

    col_srch, col_btn = st.columns([3, 1])
    with col_srch:
        txt = st.text_input("Ingrese el número exacto de SOLPED a editar:")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Localizar"): st.session_state.busqueda_id = txt
            
    if st.session_state.busqueda_id:
        res = supabase.table("solicitudes_solped").select("*").eq("numero_solped", st.session_state.busqueda_id).execute()
        if res.data:
            item = res.data[0]
            st.success(f"✅ Expediente de la SOLPED {st.session_state.busqueda_id} listo para edición.")
            
            with st.form("edit_form"):
                ca, cb = st.columns(2)
                with ca:
                    # 🌟 HACK: Mostramos el monto actual YA CON COMAS para que lo vea claro
                    monto_actual = float(item.get('monto', 0))
                    new_m_str = st.text_input("Actualizar Monto ($ MXN)", value=f"{monto_actual:,.2f}")
                    
                    new_l = st.text_input("Actualizar Link Drive", value=item.get('link_pdf', ''))
                with cb:
                    lista_estatus = ["EN PROCESO", "COMPLETADA", "CANCELADA"]
                    estatus_actual =
