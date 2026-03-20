import streamlit as st
import sqlite3
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Sistema SOLPED", page_icon="📊", layout="centered")

st.title("📊 Gestor de SOLPEDs")
st.write("Bienvenido al sistema automatizado de compras y requisiciones.")

menu = st.sidebar.selectbox(
    "Menú de Opciones",
    ("Registrar Nueva SOLPED", "Agregar Códigos a SOLPED", "Buscar SOLPED", "Ver Dashboard (Gerencia)")
)

# ---------------------------------------------------------
# PANTALLA 1: REGISTRAR DATOS GENERALES
# ---------------------------------------------------------
if menu == "Registrar Nueva SOLPED":
    st.subheader("📝 Registrar Nueva Solicitud")
    with st.form("form_registro"):
        numero = st.text_input("Número de SOLPED (Oficio)")
        
        lista_areas = [
            "🟡 DIRECCIÓN GENERAL DE OPERACIÓN",
            "🟢 GERENCIA DE INGENIERÍA Y NUEVOS PROYECTOS",
            "🔵 CAPITAL HUMANO",
            "🩷 COORDINACIÓN DE EVALUACIÓN DE PROYECTOS Y MANTENIMIENTO DE ÁREAS GENERALES",
            "🟠 DIRECCIÓN GENERAL DE ADMINISTRACIÓN Y FINANZAS",
            "🔴 DIRECCIÓN DE MANTENIMIENTO DE MATERIAL RODANTE",
            "🟣 DIRECCIÓN DE INSTALACIONES FIJAS",
            "⚫ DIRECCIÓN DE TRANSPORTACIÓN",
            "🟤 GERENCIA DE SEGURIDAD INSTITUCIONAL",
            "⚪ DIRECCIÓN DE MEDIOS",
            "🍷 GERENCIA DE ALMACENES Y SUMINISTROS",
            "🔘 GERENCIA DE SALUD Y BIENESTAR SOCIAL",
            "🌐 GERENCIA DE ORGANIZACIÓN Y SISTEMAS",
            "🩵 PREVIAS"
]
        
  area = st.selectbox("Área Usuaria", lista_areas)
    coordinacion = st.radio("Coordinación Asignada", ["CCP (Nacional)", "CCE (Extranjero)"])
    
    # --- LOS NUEVOS CAMBIOS ESTRELLA ---
    st.divider()
    st.write("📌 **Estatus y Documentación**")
    estatus = st.selectbox("Estatus de la SOLPED", ["En Proceso", "Adjudicado", "Cancelado"])
    
    archivo_solped = st.file_uploader("📥 Subir SOLPED escaneada (PDF)", type=["pdf"])
    archivo_contrato = st.file_uploader("📥 Subir Contrato (PDF)", type=["pdf"])
    st.divider()
    # -----------------------------------
    
    enviado = st.form_submit_button("Guardar SOLPED")
    
    if enviado:
            if numero == "":
                st.warning("⚠️ Por favor, ingresa el Número de SOLPED.")
            else:
                try:
                    # Simulamos que leemos el PDF para el demo
                    estado_archivos = "Sin archivos"
                    if archivo_solped or archivo_contrato:
                        estado_archivos = "📁 Expedientes cargados"
                        
                    conexion = sqlite3.connect('solped_data.db')
                    cursor = conexion.cursor()
                    cursor.execute('''
                        INSERT INTO solicitudes_solped (numero_solped, area_usuaria, coordinacion_asignada, estatus, link_pdf)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (numero, area, coordinacion, estatus, estado_archivos))
                    conexion.commit()
                    conexion.close()
                    st.success(f"✅ ¡Éxito! La SOLPED {numero} quedó como '{estatus}' y sus documentos fueron procesados.")
                except sqlite3.IntegrityError:
                    st.error(f"❌ Error: La SOLPED {numero} ya está registrada en el sistema.")
                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")

# ---------------------------------------------------------
# PANTALLA 2: AGREGAR LOS "MIL CÓDIGOS"
# ---------------------------------------------------------
elif menu == "Agregar Códigos a SOLPED":
    st.subheader("🛒 Agregar Artículos a una SOLPED")
    conexion = sqlite3.connect('solped_data.db')
    cursor = conexion.cursor()
    cursor.execute("SELECT id, numero_solped FROM solicitudes_solped")
    solpeds_guardadas = cursor.fetchall()
    
    if len(solpeds_guardadas) == 0:
        st.warning("⚠️ No hay SOLPEDs registradas aún.")
    else:
        opciones_solped = {f"SOLPED: {s[1]}": s[0] for s in solpeds_guardadas}
        with st.form("form_codigos"):
            solped_seleccionada = st.selectbox("Selecciona la SOLPED", list(opciones_solped.keys()))
            codigo = st.text_input("Código del Artículo")
            descripcion = st.text_input("Descripción del artículo")
            monto = st.number_input("Monto ($)", min_value=0.0, format="%.2f")
            btn_guardar_codigo = st.form_submit_button("Guardar Código")
            
            if btn_guardar_codigo:
                if codigo == "":
                    st.error("❌ El código no puede estar vacío.")
                else:
                    solped_id = opciones_solped[solped_seleccionada]
                    cursor.execute('''
                        INSERT INTO partidas_codigos (solped_id, codigo_articulo, descripcion, monto)
                        VALUES (?, ?, ?, ?)
                    ''', (solped_id, codigo, descripcion, monto))
                    conexion.commit()
                    st.success(f"✅ ¡Código {codigo} agregado exitosamente a la {solped_seleccionada}!")
    conexion.close()

# ---------------------------------------------------------
# PANTALLA 3: BUSCAR SOLPED (¡NUEVA!)
# ---------------------------------------------------------
elif menu == "Buscar SOLPED":
    st.subheader("🔍 Buscar y Consultar SOLPED")
    numero_buscar = st.text_input("Ingresa el Número de Oficio exacto para buscar:")
    
    if st.button("Buscar"):
        if numero_buscar != "":
            conexion = sqlite3.connect('solped_data.db')
            # Buscamos la SOLPED general
            query_solped = "SELECT * FROM solicitudes_solped WHERE numero_solped = ?"
            df_solped = pd.read_sql_query(query_solped, conexion, params=(numero_buscar,))
            
            if df_solped.empty:
                st.error(f"❌ No se encontró ninguna SOLPED con el número '{numero_buscar}'.")
            else:
                st.success("✅ SOLPED Encontrada")
                st.write("**Datos Generales:**")
                st.dataframe(df_solped.drop(columns=['id']), use_container_width=True)
                
                # Buscamos los artículos relacionados a esa SOLPED
                solped_id = df_solped.iloc[0]['id']
                query_articulos = "SELECT codigo_articulo as Código, descripcion as Descripción, monto as Monto FROM partidas_codigos WHERE solped_id = ?"
                df_articulos = pd.read_sql_query(query_articulos, conexion, params=(int(solped_id),))
                
                st.write("**Artículos Registrados:**")
                if df_articulos.empty:
                    st.info("Esta SOLPED aún no tiene artículos registrados.")
                else:
                    st.dataframe(df_articulos, use_container_width=True)
                    st.write(f"**Total de la SOLPED:** ${df_articulos['Monto'].sum():,.2f}")
                    
            conexion.close()

# ---------------------------------------------------------
# PANTALLA 4: DASHBOARD (PANEL GERENCIAL)
# ---------------------------------------------------------
elif menu == "Ver Dashboard (Gerencia)":
    st.subheader("📈 Panel de Control Gerencial")
    conexion = sqlite3.connect('solped_data.db')
    df_solpeds = pd.read_sql_query("SELECT * FROM solicitudes_solped", conexion)
    df_articulos = pd.read_sql_query("SELECT * FROM partidas_codigos", conexion)
    
    if df_solpeds.empty:
        st.info("Aún no hay datos para mostrar en el Dashboard.")
    else:
        st.markdown("### 📊 Resumen General")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de SOLPEDs", len(df_solpeds))
        col2.metric("Artículos Capturados", len(df_articulos))
        col3.metric("Monto Total Invertido", f"${df_articulos['monto'].sum() if not df_articulos.empty else 0:,.2f}")
        
        st.divider()
        st.markdown("### 🎯 Análisis de Coordinaciones y Estatus")
        colA, colB = st.columns(2)
        with colA:
            st.write("**Carga de trabajo por Coordinación**")
            st.bar_chart(df_solpeds['coordinacion_asignada'].value_counts())
        with colB:
            st.write("**Estatus de las SOLPEDs**")
            st.bar_chart(df_solpeds['estatus'].value_counts())
        
        st.divider()
        st.markdown("### 📋 Base de Datos Maestra")
        query_union = '''
            SELECT s.numero_solped as "Oficio SOLPED", s.area_usuaria as "Área", 
                   s.coordinacion_asignada as "Coordinación", s.estatus as "Estatus",
                   p.codigo_articulo as "Código", p.descripcion as "Descripción", p.monto as "Monto"
            FROM solicitudes_solped s LEFT JOIN partidas_codigos p ON s.id = p.solped_id
        '''
        st.dataframe(pd.read_sql_query(query_union, conexion), use_container_width=True)
    conexion.close()
