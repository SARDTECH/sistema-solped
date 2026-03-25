import streamlit as st
import pandas as pd
from supabase import create_client
import datetime

# ==========================================
# CONFIGURACIÓN TOP Y DISEÑO METRO CDMX
# ==========================================
# Aquí puedes cambiar "SIGAS" por el nombre que elijan
st.set_page_config(page_title="SIGAS - Metro CDMX", page_icon="🚇", layout="wide")

st.markdown("""
    <style>
    /* Ocultar marcas de agua de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    :root {
        --metro-naranja: #F6831E;
        --metro-oscuro: #2C2C2C;
    }
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 4px solid var(--metro-naranja);
    }
    h1, h2, h3 { color: var(--metro-oscuro) !important; font-family: 'Arial', sans-serif; }
    [data-testid="stMetricValue"] { color: var(--metro-naranja) !important; font-weight: 900 !important; font-size: 2.5rem !important; }
    .stButton>button { background-color: var(--metro-naranja); color: white; border-radius: 6px; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: var(--metro-oscuro); color: var(--metro-naranja); }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A LA NUBE (SUPABASE) ---
SUPABASE_URL = "https://emickgfmgyzkabmxbmqn.supabase.co"
SUPABASE_KEY = "sb_publishable_WvpRWnDzmRJ-mmrZedWrTA_agKAp_Kg"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- MENÚ DE NAVEGACIÓN ---
try:
    st.sidebar.image("logo m.png", width=150)
except:
    pass

# CAMBIO 1: Nuevo nombre oficial de la Subgerencia
st.sidebar.title("Subgerencia de Adquisiciones")
menu = st.sidebar.radio(
    "Navegación del Sistema:",
    ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar y Editar")
)

# ==========================================
# FUNCIONES DE LIMPIEZA DE FECHAS
# ==========================================
def limpiar_fecha_metro(fecha_str):
    try:
        if pd.isna(fecha_str) or str(fecha_str).strip() == "": return pd.NaT
        f = str(fecha_str).replace('/', '-').strip()
        partes = f.split('-')
        if len(partes) == 3 and len(partes[2]) == 2:
            partes[2] = "20" + partes[2]
            f = f"{partes[0]}-{partes[1]}-{partes[2]}"
        return pd.to_datetime(f, format='%d-%m-%Y', errors='coerce')
    except:
        return pd.to_datetime(str(fecha_str), errors='coerce', dayfirst=True)

# ==========================================
# PANTALLA 1: DASHBOARD GERENCIAL
# ==========================================
if menu == "📊 Dashboard Gerencial":
    st.title("📈 Panel de Control Gerencial - SOLPEDs")
    
    try:
        res_solpeds = supabase.table("solicitudes_solped").select("*").execute()
        df = pd.DataFrame(res_solpeds.data)
        
        if df.empty:
            st.info("No hay datos para mostrar en la base de datos.")
        else:
            df['fecha_limpia'] = df['fecha_oficio'].apply(limpiar_fecha_metro)
            
            fechas_validas = df['fecha_limpia'].dropna()
            if not fechas_validas.empty:
                min_date = fechas_validas.min().date()
                max_date = fechas_validas.max().date()
            else:
                min_date = datetime.date.today() - datetime.timedelta(days=30)
                max_date = datetime.date.today()
            
            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Rango de Fechas")
            
            rango_fechas = st.sidebar.date_input(
                "Periodo de Consulta:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY"
            )
            
            df_filtrado = df.copy()
            if len(rango_fechas) == 2:
                fecha_inicio, fecha_fin = rango_fechas
                df_filtrado = df_filtrado[
                    (df_filtrado['fecha_limpia'].dt.date >= fecha_inicio) & 
                    (df_filtrado['fecha_limpia'].dt.date <= fecha_fin)
                ]

            df_filtrado['monto'] = pd.to_numeric(df_filtrado['monto'], errors='coerce').fillna(0)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de SOLPEDs", len(df_filtrado))
            col2.metric("Monto Total Invertido", f"${df_filtrado['monto'].sum():,.2f}")
            col3.metric("Promedio por Oficio", f"${(df_filtrado['monto'].mean() if len(df_filtrado)>0 else 0):,.2f}")
            st.divider()
            
            colA, colB = st.columns(2)
            with colA:
                st.write("**Gasto por Área Usuaria**")
                st.bar_chart(df_filtrado.groupby('area_usuaria')['monto'].sum())
            with colB:
                st.write("**Estatus de SOLPEDs**")
                if 'estatus' in df_filtrado.columns: st.bar_chart(df_filtrado['estatus'].value_counts())
            
            st.subheader("📋 Base de Datos Filtrada")
            # CAMBIO 2: Agregamos la columna 'descripcion' para que se vea en la tabla principal
            cols_mostrar = ['numero_solped', 'area_usuaria', 'descripcion', 'monto', 'fecha_oficio', 'estatus', 'link_pdf']
            cols_reales = [c for c in cols_mostrar if c in df_filtrado.columns]
            st.dataframe(df_filtrado[cols_reales], column_config={"link_pdf": st.column_config.LinkColumn("Carpeta / Archivo")}, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error de sistema: {e}")

# ==========================================
# PANTALLA 2: REGISTRAR SOLPED
# ==========================================
elif menu == "📝 Registrar SOLPED":
    st.title("📝 Alta de Nueva SOLPED")
    with st.form("form_nube"):
        col1, col2 = st.columns(2)
        with col1:
            numero = st.text_input("Número de SOLPED / Oficio *")
            area = st.selectbox("Área Usuaria", ["DIRECCIÓN DE INSTALACIONES FIJAS", "DIRECCIÓN DE MANTENIMIENTO DE MATERIAL RODANTE", "CAPITAL HUMANO", "DIRECCIÓN GENERAL DE OPERACIÓN", "OTRO"])
            fecha = st.date_input("Fecha del Documento", format="DD/MM/YYYY")
            monto = st.number_input("Monto Estimado ($)", min_value=0.0)
        with col2:
            coord = st.radio("Coordinación Asignada", ["CCP (Nacional)", "CCE (Extranjero)"])
            estatus = st.selectbox("Estatus de la Compra", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
            link_pdf = st.text_input("Enlace a la Carpeta del Expediente (Drive, OneDrive, etc.)")
            st.caption("☝️ Pega aquí el enlace de la carpeta que contiene la SOLPED, contratos y anexos.")
            
        desc = st.text_area("Justificación / Descripción Breve")
        if st.form_submit_button("Subir al Sistema"):
            if numero == "":
                st.error("❌ El Número de SOLPED es obligatorio.")
            else:
                fecha_formato_db = fecha.strftime('%d-%m-%Y')
                supabase.table("solicitudes_solped").insert({"numero_solped": numero, "area_usuaria": area, "coordinacion_asignada": coord, "monto": monto, "fecha_oficio": fecha_formato_db, "link_pdf": link_pdf, "descripcion": desc, "estatus": estatus}).execute()
                st.success(f"✅ SOLPED {numero} registrada.")

# ==========================================
# PANTALLA 3: AGREGAR ARTÍCULOS
# ==========================================
elif menu == "🛒 Agregar Artículos":
    st.title("🛒 Catálogo de Partidas")
    try:
        res_solpeds = supabase.table("solicitudes_solped").select("id, numero_solped").execute()
        if res_solpeds.data:
            opciones = {str(s['numero_solped']): s['id'] for s in res_solpeds.data}
            with st.form("form_articulos"):
                seleccion = st.selectbox("Asignar a SOLPED:", list(opciones.keys()))
                codigo = st.text_input("Código de Partida *")
                desc_art = st.text_input("Descripción")
                monto_art = st.number_input("Monto de Partida ($)", min_value=0.0)
                if st.form_submit_button("Guardar Partida") and codigo:
                    supabase.table("partidas_codigos").insert({"solped_id": opciones[seleccion], "codigo_articulo": codigo, "descripcion": desc_art, "monto": monto_art}).execute()
                    st.success(f"✅ Partida guardada en SOLPED {seleccion}")
    except Exception as e: st.error(f"Error: {e}")

# ==========================================
# PANTALLA 4: BUSCAR Y EDITAR (CON AUTO-RESETEO)
# ==========================================
elif menu == "🔍 Buscar y Editar":
    st.title("🔍 Localizador y Edición de Documentos")
    
    if 'busqueda_activa' not in st.session_state:
        st.session_state.busqueda_activa = ""

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        busqueda_actual = st.text_input("Ingrese el Número exacto de SOLPED:")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True) 
        if st.button("🔍 Buscar SOLPED", use_container_width=True):
            st.session_state.busqueda_activa = busqueda_actual
            
    if st.session_state.busqueda_activa:
        res = supabase.table("solicitudes_solped").select("*").eq("numero_solped", st.session_state.busqueda_activa).execute()
        
        if res.data:
            datos = res.data[0]
            st.success("✅ Expediente Localizado")
            
            tab1, tab2 = st.tabs(["📄 Ver Detalles", "⚙️ Editar Documento"])
            
            with tab1:
                colA, colB = st.columns(2)
                with colA:
                    st.write(f"**Área Responsable:** {datos.get('area_usuaria', 'N/A')}")
                    st.write(f"**Coordinación:** {datos.get('coordinacion_asignada', 'N/A')}")
                    st.write(f"**Monto:** ${datos.get('monto', 0):,.2f}")
                with colB:
                    st.write(f"**Estatus:** {datos.get('estatus', 'N/A')}")
                    st.write(f"**Fecha Registro:** {datos.get('fecha_oficio', 'N/A')}")
                    link = datos.get('link_pdf', '')
                    if link and link.startswith("http"):
                        st.link_button("📂 Abrir Carpeta del Expediente", link)
                    else:
                        st.info("Sin expediente digital anexado.")
            
            with tab2:
                st.info("Actualiza los datos de la SOLPED aquí mismo.")
                with st.form("form_editar"):
                    lista_estatus = ["EN PROCESO", "COMPLETADA", "CANCELADA"]
                    estatus_actual = datos.get('estatus', 'EN PROCESO')
                    idx_estatus = lista_estatus.index(estatus_actual) if estatus_actual in lista_estatus else 0
                    
                    nuevo_estatus = st.selectbox("Actualizar Estatus", lista_estatus, index=idx_estatus)
                    nuevo_link = st.text_input("Actualizar Enlace de la Carpeta", value=datos.get('link_pdf', ''))
                    nuevo_monto = st.number_input("Corregir Monto ($)", value=float(datos.get('monto', 0)), min_value=0.0)
                    
                    if st.form_submit_button("💾 Guardar Cambios"):
                        try:
                            supabase.table("solicitudes_solped").update({
                                "estatus": nuevo_estatus,
                                "link_pdf": nuevo_link,
                                "monto": nuevo_monto
                            }).eq("id", datos['id']).execute()
                            
                            st.success("✅ ¡Base de datos actualizada! Cerrando expediente...")
                            st.balloons() 
                            
                            import time
                            time.sleep(2.5) 
                            st.session_state.busqueda_activa = "" 
                            st.rerun() 
                            
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
        else:
            st.error("❌ El número de SOLPED no existe en los registros.")
