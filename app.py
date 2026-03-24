import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Sistema SOLPED - Metro CDMX", page_icon="🚇", layout="wide")

# --- CONEXIÓN A LA NUBE (SUPABASE) ---
# Llaves inyectadas listas para funcionar
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
            # Limpieza de fechas para evitar el error de Pandas
            df['fecha_limpia'] = pd.to_datetime(df['fecha_oficio'], errors='coerce')
            
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
            
            f_año = st.sidebar.selectbox("Año", ["Todos"] + list(años))
            f_mes = st.sidebar.selectbox("Mes", ["Todos"] + list(meses_nombres.values()))
            
            # Aplicar Filtros
            df_filtrado = df.copy()
            if f_año != "Todos" and años:
                df_filtrado = df_filtrado[df_filtrado['fecha_limpia'].dt.year == int(f_año)]
            if f_mes != "Todos":
                num_mes = [k for k, v in meses_nombres.items() if v == f_mes][0]
                if pd.api.types.is_datetime64_any_dtype(df_filtrado['fecha_limpia']):
                    df_filtrado = df_filtrado[df_filtrado['fecha_limpia'].dt.month == num_mes]

            # Convertir monto a numérico por si acaso
            df_filtrado['monto'] = pd.to_numeric(df_filtrado['monto'], errors='coerce').fillna(0)

            # Tarjetas de Resumen
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de SOLPEDs", len(df_filtrado))
            col2.metric("Monto Total", f"${df_filtrado['monto'].sum():,.2f}")
            promedio = df_filtrado['monto'].mean() if len(df_filtrado) > 0 else 0
            col3.metric("Promedio Invertido", f"${promedio:,.2f}")
            
            st.divider()
            
            # Gráficas
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
            
            # Tabla visible
            st.subheader("📋 Detalles")
            columnas_mostrar = ['numero_solped', 'area_usuaria', 'monto', 'fecha_oficio', 'link_pdf']
            # Filtramos solo las columnas que existen
            columnas_reales = [col for col in columnas_mostrar if col in df_filtrado.columns]
            st.dataframe(df_filtrado[columnas_reales], use_container_width=True)
            
    except Exception as e:
        st.error(f"Error cargando el Dashboard: {e}")

# ==========================================
# PANTALLA 2: REGISTRAR SOLPED
# ==========================================
elif menu == "📝 Registrar SOLPED":
    st.title("📝 Nueva Solicitud (Directo a la Nube)")
    
    with st.form("form_nube"):
        col1, col2 = st.columns(2)
        with col1:
            numero = st.text_input("Número de SOLPED (Oficio) *")
            area = st.selectbox("Área Usuaria", [
                "DIRECCIÓN GENERAL DE OPERACIÓN", "CAPITAL HUMANO", 
                "DIRECCIÓN DE INSTALACIONES FIJAS", "OTRO"
            ])
            fecha = st.date_input("Fecha del Oficio")
            monto = st.number_input("Monto Estimado General ($)", min_value=0.0)
        with col2:
            coord = st.radio("Coordinación Asignada", ["CCP (Nacional)", "CCE (Extranjero)"])
            link_pdf = st.text_input("Link del PDF (Google Drive)")
            estatus = st.selectbox("Estatus Inicial", ["EN PROCESO", "COMPLETADA", "CANCELADA"])
        
        desc = st.text_area("Descripción Breve")
        enviado = st.form_submit_button("🚀 Guardar SOLPED")
        
        if enviado:
            if numero == "":
                st.error("❌ El número de SOLPED es obligatorio.")
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
                    st.success(f"✅ ¡SOLPED {numero} guardada exitosamente en la nube!")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

# ==========================================
# PANTALLA 3: AGREGAR ARTÍCULOS (PARTIDAS)
# ==========================================
elif menu == "🛒 Agregar Artículos":
    st.title("🛒 Catálogo de Artículos por SOLPED")
    st.info("Selecciona una SOLPED existente para agregarle conceptos o partidas.")
    
    try:
        # Traer las solpeds para el selector
        res_solpeds = supabase.table("solicitudes_solped").select("id, numero_solped").execute()
        if not res_solpeds.data:
            st.warning("No hay SOLPEDs registradas para agregarles artículos.")
        else:
            opciones = {f"Oficio: {s['numero_solped']}": s['id'] for s in res_solpeds.data}
            
            with st.form("form_articulos"):
                seleccion = st.selectbox("Asignar a SOLPED:", list(opciones.keys()))
                codigo = st.text_input("Código del Artículo *")
                desc_art = st.text_input("Descripción del Artículo")
                monto_art = st.number_input("Costo de esta partida ($)", min_value=0.0)
                
                guardar_art = st.form_submit_button("➕ Agregar Artículo")
                
                if guardar_art:
                    if codigo == "":
                        st.error("El código es obligatorio.")
                    else:
                        id_solped = opciones[seleccion]
                        nuevo_art = {
                            "solped_id": id_solped,
                            "codigo_articulo": codigo,
                            "descripcion": desc_art,
                            "monto": monto_art
                        }
                        supabase.table("partidas_codigos").insert(nuevo_art).execute()
                        st.success(f"✅ Artículo {codigo} agregado a {seleccion}")
    except Exception as e:
        st.error(f"Error: Asegúrate de tener la tabla 'partidas_codigos' en Supabase. Detalles: {e}")

# ==========================================
# PANTALLA 4: BUSCAR SOLPED Y VER PDF
# ==========================================
elif menu == "🔍 Buscar SOLPED":
    st.title("🔍 Buscador de Documentos")
    
    busqueda = st.text_input("Ingresa el Número de Oficio a buscar:")
    if st.button("Buscar"):
        if busqueda:
            try:
                res = supabase.table("solicitudes_solped").select("*").eq("numero_solped", busqueda).execute()
                if res.data:
                    datos = res.data[0]
                    st.success("✅ Documento Encontrado")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        st.write(f"**Área Usuaria:** {datos.get('area_usuaria', 'N/A')}")
                        st.write(f"**Coordinación:** {datos.get('coordinacion_asignada', 'N/A')}")
                        st.write(f"**Monto:** ${datos.get('monto', 0):,.2f}")
                    with colB:
                        st.write(f"**Estatus:** {datos.get('estatus', 'N/A')}")
                        st.write(f"**Fecha:** {datos.get('fecha_oficio', 'N/A')}")
                        
                        # EL BOTÓN MÁGICO PARA EL PDF
                        link = datos.get('link_pdf', '')
                        if link and link.startswith("http"):
                            st.link_button("📂 Abrir PDF en Google Drive", link)
                        else:
                            st.info("Esta SOLPED no tiene un link de PDF válido registrado.")
                else:
                    st.error("❌ No se encontró la SOLPED.")
            except Exception as e:
                st.error(f"Error en la búsqueda: {e}")
