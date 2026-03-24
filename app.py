import streamlit as st
import pandas as pd
from supabase import create_client

# ==========================================
# CONFIGURACIÓN TOP Y DISEÑO METRO CDMX
# ==========================================
st.set_page_config(page_title="Gerencia SOLPED - Metro CDMX", page_icon="🚇", layout="wide")

# Inyección de CSS (Colores oficiales del Metro)
st.markdown("""
    <style>
    /* Naranja Oficial Metro CDMX */
    :root {
        --metro-naranja: #F6831E;
        --metro-oscuro: #2C2C2C;
    }
    
    /* Barra lateral */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 4px solid var(--metro-naranja);
    }
    
    /* Títulos principales */
    h1, h2, h3 {
        color: var(--metro-oscuro) !important;
        font-family: 'Arial', sans-serif;
    }
    
    /* Números de las métricas (El dinero) */
    [data-testid="stMetricValue"] {
        color: var(--metro-naranja) !important;
        font-weight: 900 !important;
        font-size: 2.5rem !important;
    }
    
    /* Botones */
    .stButton>button {
        background-color: var(--metro-naranja);
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: var(--metro-oscuro);
        color: var(--metro-naranja);
        border: 1px solid var(--metro-naranja);
    }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A LA NUBE (SUPABASE) ---
SUPABASE_URL = "https://emickgfmgyzkabmxbmqn.supabase.co"
SUPABASE_KEY = "sb_publishable_WvpRWnDzmRJ-mmrZedWrTA_agKAp_Kg"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- MENÚ DE NAVEGACIÓN INSTITUCIONAL ---
# Logo forzado por HTML para que no se rompa nunca
st.sidebar.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Metro_de_la_Ciudad_de_M%C3%A9xico.svg/200px-Metro_de_la_Ciudad_de_M%C3%A9xico.svg.png" width="120">
</div>
""", unsafe_allow_html=True)

st.sidebar.title("Gerencia de Compras")
menu = st.sidebar.radio(
    "Navegación del Sistema:",
    ("📊 Dashboard Gerencial", "📝 Registrar SOLPED", "🛒 Agregar Artículos", "🔍 Buscar Documento")
)

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
            # EXTRACCIÓN SÚPER SEGURA DE FECHAS (El escudo protector)
            df['fecha_oficio'] = df['fecha_oficio'].astype(str)
            df['fecha_limpia'] = pd.to_datetime(df['fecha_oficio'], errors='coerce')
            
            # Filtros en la barra lateral
            st.sidebar.markdown("---")
            st.sidebar.subheader("📅 Filtros de Consulta")
            
            # Verificamos si logramos convertir fechas antes de sacar los años
            if pd.api.types.is_datetime64_any_dtype(df['fecha_limpia']) and not df['fecha_limpia'].isna().all():
                años_validos = df['fecha_limpia'].dt.year.dropna().astype(int).unique().tolist()
                años_validos.sort(reverse=True)
            else:
                años_validos = []
                
            meses_nombres = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                             7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
            
            f_año = st.sidebar.selectbox("Seleccionar Año", ["Todos"] + años_validos)
            f_mes = st.sidebar.selectbox("Seleccionar Mes", ["Todos"] + list(meses_nombres.values()))
            
            # Aplicar Filtros
            df_filtrado = df.copy()
            if f_año != "Todos" and años_validos:
                df_filtrado = df_filtrado[df_filtrado['fecha_limpia'].dt.year == int(f_año)]
            if f_mes != "Todos":
                num_mes = [k for k, v in meses_nombres.items() if v == f_mes][0]
                # Verificación extra antes de filtrar por mes
                if pd.api.types.is_datetime64_any_dtype(df_filtrado['fecha_limpia']):
                    df_filtrado = df_filtrado[df_filtrado['fecha_limpia'].dt.month == num_mes]

            # Convertir monto a numérico de forma segura
            df_filtrado['monto'] = pd.to_numeric(df_filtrado['monto'], errors='coerce').fillna(0)

            # --- TARJETAS DE RESUMEN METRO ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de SOLPEDs", len(df_filtrado))
            col2.metric("Monto Total Invertido", f"${df_filtrado['monto'].sum():,.2f}")
            promedio = df_filtrado['monto'].mean() if len(df_filtrado) > 0 else 0
            col3.metric("Promedio por Oficio", f"${promedio:,.2f}")
            
            st.divider()
            
            # --- GRÁFICAS ---
            colA, colB = st.columns(2)
            with colA:
                st.write("**Gasto por Área Usuaria**")
                st.bar_chart(df_filtrado.groupby('area_usuaria')['monto'].sum())
            with colB:
                st.write("**Estatus de SOLPEDs**")
                if 'estatus' in df_filtrado.columns:
                    st.bar_chart(df_filtrado['estatus'].value_counts())
                else:
                    st.info("Columna de estatus no disponible")
            
            # --- TABLA DE DETALLES ---
            st.subheader("📋 Base de Datos Filtrada")
            columnas_mostrar = ['numero_solped', 'area_usuaria', 'monto', 'fecha_oficio', 'estatus', 'link_pdf']
            columnas_reales = [col for col in columnas_mostrar if col in df_filtrado.columns]
            
            # Mostrar tabla con links clickeables
            st.dataframe(df_filtrado[columnas_reales], 
                         column_config={"link_pdf": st.column_config.LinkColumn("Archivo PDF")},
                         use_container_width=True)
            
    except Exception as e:
        st.error(f"Error de conexión o datos: {e}")

# ==========================================
# PANTALLA 2: REGISTRAR SOLPED
# ==========================================
elif menu == "📝 Registrar SOLPED":
    st.title("📝 Alta de Nueva SOLPED")
    
    with st.form("form_nube"):
        col1, col2 = st.columns(2)
        with col1:
            numero = st.text_input("Número de SOLPED / Oficio *")
            area = st.selectbox("Área Usuaria", [
                "DIRECCIÓN DE INSTALACIONES FIJAS", "DIRECCIÓN DE MANTENIMIENTO DE MATERIAL RODANTE",
                "CAPITAL HUMANO", "DIRECCIÓN GENERAL DE OPERACIÓN", "OTRO"
            ])
            fecha = st.date_input("Fecha del Documento")
            monto = st.number_input("Monto Estimado ($)", min_value=0.0)
        with col2:
            coord = st.radio("Coordinación Asignada", ["CCP (Nacional)", "CCE (Extranjero)"])
            link_pdf = st.text_input("Enlace al Documento (Google Drive)")
            estatus = st.selectbox("Estatus de la Compra", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
        
        desc = st.text_area("Justificación / Descripción Breve")
        enviado = st.form_submit_button("Subir al Sistema")
        
        if enviado:
            if numero == "":
                st.error("❌ El Número de SOLPED es obligatorio.")
            else:
                nuevo_registro = {
                    "numero_solped": numero,
                    "area_usuaria": area,
                    "coordinacion_asignada": coord,
                    "monto": monto,
                    "fecha_oficio": str(fecha),
                    "link_pdf": link_pdf,
                    "descripcion": desc,
                    "estatus": estatus
                }
                try:
                    supabase.table("solicitudes_solped").insert(nuevo_registro).execute()
                    st.success(f"✅ ¡La SOLPED {numero} ha sido registrada con éxito!")
                except Exception as e:
                    st.error(f"Error de sistema: {e}")

# ==========================================
# PANTALLA 3: AGREGAR ARTÍCULOS
# ==========================================
elif menu == "🛒 Agregar Artículos":
    st.title("🛒 Catálogo de Conceptos / Partidas")
    st.info("Asigna artículos específicos a una SOLPED existente.")
    
    try:
        res_solpeds = supabase.table("solicitudes_solped").select("id, numero_solped").execute()
        if not res_solpeds.data:
            st.warning("No hay SOLPEDs en el sistema.")
        else:
            # Lista limpia solo con números
            opciones = {str(s['numero_solped']): s['id'] for s in res_solpeds.data}
            
            with st.form("form_articulos"):
                seleccion = st.selectbox("Seleccionar número de SOLPED:", list(opciones.keys()))
                codigo = st.text_input("Código de Partida *")
                desc_art = st.text_input("Descripción del Bien o Servicio")
                monto_art = st.number_input("Monto de la Partida ($)", min_value=0.0)
                
                guardar_art = st.form_submit_button("Guardar Partida")
                
                if guardar_art:
                    if codigo == "":
                        st.error("El Código es obligatorio.")
                    else:
                        id_solped = opciones[seleccion]
                        nuevo_art = {
                            "solped_id": id_solped,
                            "codigo_articulo": codigo,
                            "descripcion": desc_art,
                            "monto": monto_art
                        }
                        supabase.table("partidas_codigos").insert(nuevo_art).execute()
                        st.success(f"✅ Partida {codigo} guardada en SOLPED {seleccion}")
    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# PANTALLA 4: BUSCADOR OFICIAL
# ==========================================
elif menu == "🔍 Buscar Documento":
    st.title("🔍 Localizador de Documentos Oficiales")
    
    busqueda = st.text_input("Ingrese el Número exacto de SOLPED:")
    if st.button("Buscar en Base de Datos"):
        if busqueda:
            try:
                res = supabase.table("solicitudes_solped").select("*").eq("numero_solped", busqueda).execute()
                if res.data:
                    datos = res.data[0]
                    st.success("✅ Expediente Localizado")
                    
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
                else:
                    st.error("❌ El número de SOLPED no existe en los registros.")
            except Exception as e:
                st.error(f"Error: {e}")
