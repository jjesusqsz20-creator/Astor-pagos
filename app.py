import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Configuración de Página
st.set_page_config(page_title="Astor - Rol de Pagos", layout="wide", page_icon="💸")

# --- PARAMETROS DE NEGOCIO ---
CUENTAS = [
    "Juan Ricardo Cevallos Garratachea (Santander)",
    "Juan Ricardo Cevallos Garratachea (BBVA)",
    "Antonio de Jesús Muñoz Álvarez (Santander)",
    "Guillermo Damián Muñoz Álvarez (Banamex)",
    "Nava Durán Jorge Heriberto (BBVA)"
]
PROVEEDORES = ["Sulín", "Acercare"]
PRESUPUESTO_TOTAL = 440000.0  # Mensual por cuenta
PORCENTAJE_SULIN = 0.70
PORCENTAJE_ACERCARE = 0.30

PRESUPUESTOS = {
    "Sulín": PRESUPUESTO_TOTAL * PORCENTAJE_SULIN,
    "Acercare": PRESUPUESTO_TOTAL * PORCENTAJE_ACERCARE
}

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource(show_spinner="Conectando a base de datos...")
def init_connection():
    # Define los permisos (scopes) para leer y escribir en Google Sheets
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Obtiene las credenciales desde los secretos de Streamlit
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    # Autoriza y retorna el cliente
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    # Asegúrate de haber nombrado tu hoja de cálculo "Astor_Pagos_DB" en Google Drive
    # O cambia "Astor_Pagos_DB" por el nombre exacto de tu archivo.
    spreadsheet = client.open("Astor_Pagos_DB") 
    sheet = spreadsheet.sheet1
except Exception as e:
    st.error("❌ Error de Conexión: No se pudo conectar a Google Sheets.")
    st.error(f"Detalle: {e}")
    st.info("Asegúrate de haber creado tu archivo Google Sheets, haberle puesto el nombre correcto, y haberlo compartido (como Editor) con el 'client_email' que se encuentra en tu archivo JSON de credenciales.")
    st.stop()

# --- FUNCIONES DE ACCESO A DATOS ---
def obtener_datos():
    """Descarga los datos actuales desde Google Sheets"""
    data = sheet.get_all_records()
    if not data:
        # Si la hoja está vacía, devuelve un DataFrame vacío con las columnas esperadas
        return pd.DataFrame(columns=["Fecha", "Cuenta", "Proveedor", "Monto"])
    return pd.DataFrame(data)

def borrar_pago(indice):
    """Elimina una fila específica de Google Sheets apuntando al índice real."""
    sheet.delete_rows(indice)

def registrar_pago(cuenta, proveedor, monto):
    """Guarda un nuevo pago como una nueva fila en Google Sheets"""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Si la hoja no tiene encabezados, agregarlos primero
    if not sheet.get_all_values():
        sheet.append_row(["Fecha", "Cuenta", "Proveedor", "Monto"])
    
    # Agregar la nueva fila con el registro del abono
    sheet.append_row([fecha_actual, cuenta, proveedor, monto])

# --- INTERFAZ GRAFICA (UI) ---

st.title("💸 Astor - Gestión de Rol de Pagos")
st.markdown("**Plataforma interna (SaaS) para registro y control de abonos en tiempo real.**")

# Obtener historial desde la BD
df_historial = obtener_datos()

# 1. TABLERO DE CONTROL - RESUMEN DE SALDOS
st.header("📊 Tablero de Control - Saldos Pendientes", divider="gray")

# Construir resumen base con todas las combinaciones posibles
filas_resumen = []
for c in CUENTAS:
    for p in PROVEEDORES:
        filas_resumen.append({
            "Cuenta": c,
            "Proveedor": p,
            "Presupuesto Asignado": PRESUPUESTOS[p]
        })
df_resumen = pd.DataFrame(filas_resumen)

# Calcular totales abonados basándonos en el historial
if not df_historial.empty:
    # Convertir Monto a numérico de forma segura
    df_historial["Monto"] = pd.to_numeric(df_historial["Monto"], errors='coerce').fillna(0)
    # Agrupar abonos por cuenta y proveedor
    pagos_agrupados = df_historial.groupby(["Cuenta", "Proveedor"])["Monto"].sum().reset_index()
    pagos_agrupados.rename(columns={"Monto": "Total Abonado"}, inplace=True)
    
    # Mezclar (Merge) el resumen base con los totales calculados
    df_resumen = pd.merge(df_resumen, pagos_agrupados, on=["Cuenta", "Proveedor"], how="left")
    df_resumen["Total Abonado"] = df_resumen["Total Abonado"].fillna(0)
else:
    df_resumen["Total Abonado"] = 0.0

# Calcular diferencial
df_resumen["Saldo Pendiente"] = df_resumen["Presupuesto Asignado"] - df_resumen["Total Abonado"]

# Dar formato de moneda para una bonita visualización
df_mostrar = df_resumen.copy()
for col in ["Presupuesto Asignado", "Total Abonado", "Saldo Pendiente"]:
    df_mostrar[col] = df_mostrar[col].apply(lambda x: f"${x:,.2f}")

# Destacar las celdas de "Saldo Pendiente" con colores usando el st.dataframe integrado
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)


# 2. FORMULARIO DE REGISTRO
st.header("📝 Registrar Nuevo Abono", divider="gray")
st.write("Selecciona la cuenta, el proveedor al que se le paga y el monto del abono realizado.")

with st.form("form_registro_pago"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cuenta_seleccionada = st.selectbox("Cuenta Bancaria", CUENTAS)
    with col2:
        proveedor_seleccionado = st.selectbox("Proveedor Destino", PROVEEDORES)
    with col3:
        monto_ingresado = st.number_input("Monto del Abono ($ MXN)", min_value=0.01, step=100.0)
    
    btn_guardar = st.form_submit_button("Guardar Registro", type="primary", use_container_width=True)
    
    if btn_guardar:
        if monto_ingresado <= 0:
            st.warning("El monto debe ser mayor a 0.")
        else:
            with st.spinner("Guardando registro en la Nube..."):
                try:
                    registrar_pago(cuenta_seleccionada, proveedor_seleccionado, float(monto_ingresado))
                    st.success(f"✅ ¡Abono de ${monto_ingresado:,.2f} MXN a {proveedor_seleccionado} registrado exitosamente!")
                    # Recargar la página automáticamente para actualizar la vista
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Ocurrió un error al guardar: {e}")

# 3. HISTORIAL DE MOVIMIENTOS
st.header("🕒 Historial de Movimientos", divider="gray")

if df_historial.empty:
    st.info("Aún no se han registrado abonos. Los registros aparecerán aquí.")
else:
    # Mostramos los registros recientes primero
    registros_recientes = df_historial.sort_values(by="Fecha", ascending=False)
    
    # Encabezados de tabla
    col1, col2, col3, col4, col5 = st.columns([1.5, 3, 1.5, 1.5, 1])
    col1.markdown("**Fecha**")
    col2.markdown("**Cuenta**")
    col3.markdown("**Proveedor**")
    col4.markdown("**Monto**")
    col5.markdown("**Borrar**")
    
    st.divider()
    
    # Listar los abonos con su botón individual
    for idx, row in registros_recientes.iterrows():
        c1, c2, c3, c4, c5 = st.columns([1.5, 3, 1.5, 1.5, 1])
        c1.write(str(row["Fecha"]))
        c2.write(str(row["Cuenta"]))
        c3.write(str(row["Proveedor"]))
        c4.write(f"${float(row['Monto']):,.2f}")
        
        # El índice real en Sheets es el índice del dataframe original + 2
        idx_sheet = idx + 2
        
        # Botón de basura con popover (pequeño cuadro flotante confirmando)
        with c5.popover("🗑️"):
            st.markdown("¿**Confirmas** borrar el abono?")
            st.button("Eliminar", key=f"del_{idx_sheet}", type="primary", use_container_width=True, on_click=borrar_pago, args=(idx_sheet,))
