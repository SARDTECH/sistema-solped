import streamlit as st
import pandas as pd
from supabase import create_client
import re

# ==========================================
# CONFIGURACIÓN TOP Y DISEÑO METRO CDMX
# ==========================================
st.set_page_config(page_title="Gerencia SOLPED - Metro CDMX", page_icon="🚇", layout="wide")

st.markdown("""
    <style>
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
# ¡Aquí está el arreglo del logo! Lee el nombre exacto de tu GitHub
try:
    st.sidebar.image("logo m.png", width=150)
except:
    pass # Si no lo encuentra, no pone mensaje de error, solo se lo salta

st.sidebar.title("Gerencia de Compras")
menu = st.sidebar.radio(
    "Navegación del Sistema:",
    ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar y Editar")
)

# ==========================================
# FUNCIONES DE EXTRACCIÓN SÚPER SEGURA
# ==========================================
def extraer_año_seguro(fecha_str):
    try:
        if pd.isna(fecha_str) or str(fecha_str).strip() == "": return None
        partes = str(fecha_str).replace('/', '-').split('-')
        if len(partes) == 3:
            year = partes[2].strip()
            if len(year) == 2: return int("20" + year)
            if len(year) == 4: return int(year)
        return pd.to_datetime(fecha_str, errors='coerce', dayfirst=True).year
    except:
        return None

def extraer_mes_seguro(fecha_str):
    try:
        partes = str(fecha_str).replace('/', '-').split('-')
        if len(partes) == 3: return int(partes[1].strip())
        return pd.to_datetime(fecha_str, errors='coerce', dayfirst=True).month
    except:
        return None

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
            df['año_real'] = df['fecha_oficio'].apply(extraer_año_seguro)
            df['mes_real'] = df['fecha_oficio'].apply(extraer_mes_seguro)
            
            años_lista = df['año_real'].dropna().astype(int).unique().tolist()
            años_lista.sort(reverse=True)
            
            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Filtros de Consulta")
            f_año = st.sidebar.selectbox("Seleccionar Año", ["Todos"] + años_lista)
            
            meses_nombres = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                             7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
            f_mes = st.sidebar.selectbox("Seleccionar Mes", ["Todos"] + list(meses_nombres.values()))
            
            df_filtrado = df.copy()
            if f_año != "Todos":
                df_filtrado = df_filtrado[df_filtrado['año_real'] == int(f_año)]
            if f_mes != "Todos":
                num_mes = [k for k, v in meses_nombres.items() if v == f_mes][0]
                df_filtrado = df_filtrado[df_filtrado['mes_real'] == num_mes]

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
            cols_mostrar = ['numero_solped', 'area_usuaria', 'monto', 'fecha_oficio', 'estatus', 'link_pdf']
            cols_reales = [c for c in cols_mostrar if c in df_filtrado.columns]
            st.dataframe(df_filtrado[cols_reales], column_config={"link_pdf": st.column_config.LinkColumn("Archivo PDF")}, use_container_width=True)
            
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
            fecha = st.date_input("Fecha del Documento")
            monto = st.number_input("Monto Estimado ($)", min_value=0.0)
        with col2:
            coord = st.radio("Coordinación Asignada", ["CCP (Nacional)", "CCE (Extranjero)"])
            link_pdf = st.text_input("Enlace al Documento (Google Drive)")
            estatus = st.selectbox("Estatus de la Compra", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
        
        desc = st.text_area("Justificación / Descripción Breve")
        if st.form_submit_button("Subir al Sistema"):
            if numero == "":
                st.error("❌ El Número de SOLPED es obligatorio.")
            else:
                supabase.table("solicitudes_solped").insert({"numero_solped": numero, "area_usuaria": area, "coordinacion_asignada": coord, "monto": monto, "fecha_oficio": str(fecha), "link_pdf": link_pdf, "descripcion": desc, "estatus": estatus}).execute()
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
# PANTALLA 4: BUSCAR Y EDITAR (CON BOTÓN)
# ==========================================
elif menu == "🔍 Buscar y Editar":
    st.title("🔍 Localizador y Edición de Documentos")
    
    # --- FORMULARIO DE BÚSQUEDA ---
    with st.form("form_buscar"):
        busqueda = st.text_input("Ingrese el Número exacto de SOLPED:")
        boton_buscar = st.form_submit_button("🔍 Buscar SOLPED")
    
    if boton_buscar:
        if busqueda:
            res = supabase.table("solicitudes_solped").select("*").eq("numero_solped", busqueda).execute()
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
                            st.link_button("📂 Consultar Expediente PDF", link)
                        else:
                            st.info("Sin expediente digital anexado.")
                
                with tab2:
                    st.info("Actualiza los datos de la SOLPED aquí mismo.")
                    with st.form("form_editar"):
                        lista_estatus = ["EN PROCESO", "COMPLETADA", "CANCELADA"]
                        estatus_actual = datos.get('estatus', 'EN PROCESO')
                        idx_estatus = lista_estatus.index(estatus_actual) if estatus_actual in lista_estatus else 0
                        
                        nuevo_estatus = st.selectbox("Actualizar Estatus", lista_estatus, index=idx_estatus)
                        nuevo_link = st.text_input("Actualizar Enlace PDF (Drive)", value=datos.get('link_pdf', ''))
                        nuevo_monto = st.number_input("Corregir Monto ($)", value=float(datos.get('monto', 0)), min_value=0.0)
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            supabase.table("solicitudes_solped").update({
                                "estatus": nuevo_estatus,
                                "link_pdf": nuevo_link,
                                "monto": nuevo_monto
                            }).eq("id", datos['id']).execute()
                            st.success("✅ ¡Actualización exitosa! Vuelve a buscar el número para ver los cambios.")
                            
            else:
                st.error("❌ El número de SOLPED no existe en los registros.")
        else:
            st.warning("⚠️ Por favor ingresa un número de SOLPED para buscar.")
