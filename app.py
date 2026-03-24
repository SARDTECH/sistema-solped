import streamlit as st
import sqlite3
import pandas as pd
from config import LISTA_AREAS
from supabase import create_client, Client

# --- CONEXIÓN A LA BÓVEDA DE SUPABASE ---
url_bd = st.secrets["SUPABASE_URL"]
llave_bd = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url_bd, llave_bd)
# ----------------------------------------

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
    st.subheader("📝 Registrar Nueva Solicitud (Fase 2)")
    
    with st.form("form_registro", clear_on_submit=True):
        # --- SECCIÓN 1: DATOS GENERALES ---
        st.write("📌 **Datos Generales**")
        col1, col2 = st.columns(2) # Partimos la pantalla en 2
        
        with col1:
            numero = st.text_input("Número de SOLPED (Obligatorio)*")
            fecha_oficio = st.text_input("Fecha Oficio (ej. 01-08-25)")
            oficio = st.text_input("Oficio")
            
        with col2:
            area = st.selectbox("Área Usuaria", LISTA_AREAS)
            coordinacion = st.radio("Coordinación Asignada", ["CCP (Nacional)", "CCE (Extranjero)"])
        
        # --- SECCIÓN 2: DETALLES DE LA COMPRA ---
        st.divider()
        st.write("🛒 **Detalles de la Compra**")
        descripcion = st.text_area("Descripción de la SOLPED")
        
        col3, col4 = st.columns(2)
        with col3:
            no_partidas = st.number_input("No. Partidas", min_value=0, step=1)
            suficiencia_01 = st.text_input("Suficiencia 01")
            procedimiento = st.text_input("Procedimiento")
            
        with col4:
            monto = st.number_input("Monto Estimado ($)", min_value=0.0, step=100.0)
            suficiencia_02 = st.text_input("Suficiencia 02")
            fecha_recibido = st.text_input("Fecha de Recibido en Área Operadora")

        # --- SECCIÓN 3: CONTRATO Y ESTATUS ---
        st.divider()
        st.write("📋 **Contrato y Estatus**")
        col5, col6 = st.columns(2)
        
        with col5:
            contrato = st.text_input("Número de Contrato")
            estatus = st.selectbox("Estatus de la SOLPED", ["En Proceso", "Adjudicado", "Cancelado"])
            
        with col6:
            monto_contrato = st.number_input("Monto de Contrato ($)", min_value=0.0, step=100.0)
        
        # --- SECCIÓN 4: DOCUMENTOS ---
        st.write("📂 **Documentación (Opcional)**")
        archivo_solped = st.file_uploader("📥 Subir SOLPED escaneada (PDF)", type=["pdf"])
        archivo_contrato = st.file_uploader("📥 Subir Contrato (PDF)", type=["pdf"])
        
        st.divider()
        enviado = st.form_submit_button("Guardar SOLPED Completa")
        
        # --- LÓGICA DE GUARDADO EN LA BÓVEDA ---
        if enviado:
            if numero == "":
                st.warning("⚠️ Por favor, ingresa el Número de SOLPED.")
            else:
                with st.spinner('Procesando datos y guardando...'):
                    try:
                        estado_archivos = "Sin archivos"
                        if archivo_solped or archivo_contrato:
                            estado_archivos = "📁 Expedientes cargados"
                            
                        # Empacamos TODOS los datos nuevos
                        datos = {
                            "numero_solped": numero,
                            "area_usuaria": area,
                            "coordinacion_asignada": coordinacion,
                            "estatus": estatus,
                            "link_pdf": estado_archivos,
                            "no_partidas": no_partidas,
                            "monto": monto,
                            "fecha_oficio": fecha_oficio,
                            "oficio": oficio,
                            "descripcion": descripcion,
                            "suficiencia_01": suficiencia_01,
                            "suficiencia_02": suficiencia_02,
                            "procedimiento": procedimiento,
                            "fecha_recibido": fecha_recibido,
                            "contrato": contrato,
                            "monto_contrato": monto_contrato
                        }
                        
                        # Inyectamos en Supabase
                        respuesta = supabase.table("solicitudes_solped").insert(datos).execute()
                        st.success(f"✅ Guardado con éxito. La SOLPED {numero} fue registrada correctamente con todos sus detalles.")
                        
                    except Exception as e:
                        if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                            st.error(f"❌ Error: La SOLPED {numero} ya está registrada en el sistema.")
                        else:
                            st.error(f"Ocurrió un error en la conexión: {e}")
                        
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
