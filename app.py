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
    /* 🛡️ BOTÓN ANTIPÁNICO: Flecha de menú siempre visible con borde naranja */
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
    [data-testid="stSidebarCollapseButton"] svg {
        color: #F6831E !important;
        width: 28px !important;
        height: 28px !important;
    }

    /* Ajuste de espacio para que el título no choque con el botón */
    .main .block-container { padding-top: 4.5rem !important; }

    /* Ocultar elementos nativos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Identidad Visual Metro CDMX */
    :root {
        --metro-naranja: #F6831E;
        --metro-oscuro: #2C2C2C;
    }
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 4px solid var(--metro-naranja);
    }
    h1, h2, h3 { color: var(--metro-oscuro) !important; font-family: 'Arial', sans-serif; }
    [data-testid="stMetricValue"] { color: var(--metro-naranja) !important; font-weight: 900 !important; }
    
    /* Botones Naranjas Estilo Institucional */
    .stButton>button { 
        background-color: var(--metro-naranja); 
        color: white; 
        border-radius: 6px; 
        border: none; 
        font-weight: bold;
        width: 100%;
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
# 3. BARRA LATERAL (SIDEBAR)
# ==========================================
try:
    st.sidebar.image("logo m.png", width=140)
except:
    st.sidebar.title("🚇 METRO")

st.sidebar.title("Subgerencia de Adquisiciones")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación del Sistema:",
    ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar y Editar")
)

# --- Función de apoyo para fechas ---
def limpiar_fecha(f_str):
    try:
        return pd.to_datetime(f_str, dayfirst=True, errors='coerce')
    except:
        return pd.NaT

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
            # Procesamiento de montos y fechas
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0)
            df['fecha_dt'] = df['fecha_oficio'].apply(limpiar_fecha)
            
            # Métricas Principales
            c1, c2, c3 = st.columns(3)
            c1.metric("Total SOLPEDs", f"{len(df)}")
            c2.metric("Inversión Total", f"${df['monto'].sum():,.2f}")
            c3.metric("Ticket Promedio", f"${(df['monto'].mean()):,.2f}")
            
            st.divider()
            
            # Tabla de Datos con Formato de Moneda $ MXN
            st.subheader("📋 Listado Maestro de SOLPEDs")
            cols = ['numero_solped', 'area_usuaria', 'descripcion', 'monto', 'fecha_oficio', 'estatus', 'link_pdf']
            existentes = [c for c in cols if c in df.columns]
            
            st.dataframe(
                df[existentes],
                column_config={
                    "monto": st.column_config.NumberColumn("Monto ($ MXN)", format="$ %.2f"),
                    "link_pdf": st.column_config.LinkColumn("Expediente Digital"),
                    "numero_solped": "SOLPED #"
                },
                use_container_width=True,
                hide_index=True
            )
    except Exception as e:
        st.error(f"Error al cargar Dashboard: {e}")

# ==========================================
# PANTALLA 2: REGISTRAR SOLPED (CON ESCUDO ANTI-DUPLICADOS)
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
            mon = st.number_input("Monto Inicial ($)", min_value=0.0, step=100.0)
            coord = st.radio("Coordinación", ["CCP (Nacional)", "CCE (Extranjero)"], horizontal=True)
            est = st.selectbox("Estatus Inicial", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
        
        det = st.text_area("Descripción / Justificación del Gasto")
        lnk = st.text_input("Enlace a Carpeta (Drive/OneDrive)")
        
        if st.form_submit_button("💾 Guardar en Base de Datos"):
            if not num:
                st.error("❌ El número de SOLPED es obligatorio.")
            else:
                try:
                    f_db = fec.strftime('%d-%m-%Y')
                    supabase.table("solicitudes_solped").insert({
                        "numero_solped": num, "area_usuaria": area, "monto": mon,
                        "fecha_oficio": f_db, "coordinacion_asignada": coord,
                        "estatus": est, "descripcion": det, "link_pdf": lnk
                    }).execute()
                    st.success(f"✅ ¡SOLPED {num} registrada exitosamente!")
                    st.balloons()
                except Exception as e:
                    # ESCUDO PARA BUBU: Detectar si el número ya existe
                    if "duplicate key" in str(e).lower():
                        st.warning(f"⚠️ La SOLPED **{num}** ya fue registrada anteriormente.")
                        st.info("💡 **Acción recomendada:** Si quieres actualizar sus datos, ve al módulo **'🔍 Buscar y Editar'**.")
                    else:
                        st.error(f"🚨 Error técnico: {e}")

# ==========================================
# PANTALLA 3: AGREGAR ARTÍCULOS (SEGMENTACIÓN CCP/CCE)
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
                    mto = st.number_input("Monto de la Partida ($)", min_value=0.0)
                with c2:
                    tipo = st.radio("Segmentación de Compra:", ["CCP (Nacional)", "CCE (Extranjero)"])
                    dsc = st.text_input("Descripción del Bien/Servicio")
                
                if st.form_submit_button("🚀 Registrar Artículo"):
                    if cod:
                        supabase.table("partidas_codigos").insert({
                            "solped_id": opciones[sol_sel], "codigo_articulo": cod.upper(),
                            "descripcion": dsc, "monto": mto, "coordinacion": tipo
                        }).execute()
                        st.success(f"✅ Partida {cod.upper()} añadida a la SOLPED {sol_sel}")
                    else:
                        st.error("❌ Indique el código del artículo.")
    except Exception as e:
        st.error(f"Error en módulo de artículos: {e}")

# ==========================================
# PANTALLA 4: BUSCAR Y EDITAR (CON AUTO-RESETEO)
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
                    new_m = st.number_input("Actualizar Monto ($)", value=float(item.get('monto', 0)))
                    new_l = st.text_input("Actualizar Link Drive", value=item.get('link_pdf', ''))
                with cb:
                    new_e = st.selectbox("Cambiar Estatus", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
                
                if st.form_submit_button("💾 Actualizar y Cerrar"):
                    supabase.table("solicitudes_solped").update({
                        "monto": new_m, "link_pdf": new_l, "estatus": new_e
                    }).eq("id", item['id']).execute()
                    
                    st.success("✅ Cambios guardados. Regresando al inicio...")
                    st.balloons()
                    time.sleep(2)
                    st.session_state.busqueda_id = ""
                    st.rerun()
        else:
            st.error("❌ No se encontró ningún registro con ese número.")
