import streamlit as st
import streamlit.components.v1 as components
import gspread
import json
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import re

# Configuración de Página
st.set_page_config(page_title="Inside - Rol de Pagos", layout="wide", page_icon="💸")

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
<style>
    /* Fondo principal con leve gradiente opcional */
    .stApp {
        background: linear-gradient(135deg, #F0F2F5 0%, #E2E8F0 100%);
    }

    /* Barra lateral */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
    }
    
    /* Inputs y dropdowns */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>div,
    .stNumberInput>div>div>input {
        background-color: #F1F5F9 !important;
        color: #1E3A8A !important;
        border: 1px solid #E5E7EB !important;
    }

    /* Estilo refinado para los títulos de los expansores */
    [data-testid="stExpander"] summary p, 
    [data-testid="stExpander"] summary span, 
    [data-testid="stExpander"] summary div {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        color: #000000 !important;
        line-height: 1.2 !important;
    }
    .streamlit-expanderHeader {
        background-color: #F8FAFC !important;
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    /* Alineación a la izquierda para los popovers de ajustes */
    div[data-testid="stPopover"] {
        text-align: left !important;
        display: flex !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    div[data-testid="stPopover"] > button {
        text-align: left !important;
        justify-content: flex-start !important;
        width: auto !important; /* El botón solo ocupa lo que mide su texto */
        min-width: 0px !important;
    }
    div[data-testid="stPopover"] > button div[data-testid="stMarkdownContainer"] p {
        text-align: left !important;
        white-space: nowrap !important;
    }
    .streamlit-expanderContent {
        border-color: #E5E7EB !important;
        background-color: #FFFFFF !important;
        padding-left: 0.5rem !important; /* Reducir padding para 'pegar' elementos */
    }
    .streamlit-expanderContent div[data-testid="stVerticalBlock"] > div {
        padding-left: 0px !important;
    }
    
    /* Títulos principales */
    h1, h2, h3, h4, h5, h6 {
        color: #364350;
    }

    /* --- ESTILOS DE LOGIN --- */
    .login-box {
        background-color: #FFFFFF;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        max-width: 450px;
        margin: auto;
        text-align: center;
        border: 1px solid #E5E7EB;
    }
    div.stButton > button.login-btn-primary {
        background-color: #3B82F6 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        width: 100% !important;
        border: none !important;
    }
    /* Quitar fondo de los iframes de componentes */
    iframe {
        background: transparent !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE USUARIOS (DB) ---
@st.cache_data(ttl=1)
def obtener_usuarios_db(_client):
    try:
        spreadsheet = _client.open("Astor_Pagos_DB")
        try:
            sheet_users = spreadsheet.worksheet("Usuarios")
        except gspread.WorksheetNotFound:
            sheet_users = spreadsheet.add_worksheet(title="Usuarios", rows="100", cols="5")
            sheet_users.append_row(["Nombre", "Email", "Telefono", "Password", "Rol"])
            return []
        records = sheet_users.get_all_records()
        # Normalización robusta para obtener el rol (maneja variantes de mayúsculas/minúsculas y espacios)
        return [
            {
                "nombre": r.get("Nombre", ""),
                "email": r.get("Email", ""),
                "tel": r.get("Telefono", ""),
                "pass": str(r.get("Password", "")),
                # El rol debe ser lo que diga la BD, o "Editor" si está vacío/no existe
                "rol": (r.get("Rol") or r.get("rol") or r.get("ROL") or "Editor").strip()
            } for r in records
        ]
    except:
        return []

def registrar_usuario_db(client, nuevo_user):
    try:
        spreadsheet = client.open("Astor_Pagos_DB")
        sheet_users = spreadsheet.worksheet("Usuarios")
        sheet_users.append_row([nuevo_user["nombre"], nuevo_user["email"], nuevo_user["tel"], nuevo_user["pass"], nuevo_user["rol"]])
        obtener_usuarios_db.clear() # Invalida el cache al registrar nuevo usuario
        return True
    except:
        return False

# --- CONFIGURACIÓN DE ESTADO ---
if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None
if "vista_auth" not in st.session_state:
    st.session_state.vista_auth = "login"
if "config_panel_open" not in st.session_state:
    st.session_state.config_panel_open = False
if "monto_pago_val" not in st.session_state:
    st.session_state.monto_pago_val = 0.0
if "monto_ret_val" not in st.session_state:
    st.session_state.monto_ret_val = 0.0

# --- PARAMETROS DE NEGOCIO ---
CUENTAS = [
    "Ceballos Garratachea Juan Ricardo (BBVA)",
    "Ceballos Garratachea Juan Ricardo (Santander)",
    "Muñoz Álvarez Antonio de Jesús (Santander)",
    "Muñoz Álvarez Guillermo Damián (Banamex)",
    "Nava Durán Jorge Heriberto (BBVA)"
]

MAPEO_NOMBRES_ANTIGUOS = {
    "Juan Ricardo Ceballos Garratachea (Santander)": "Ceballos Garratachea Juan Ricardo (Santander)",
    "Juan Ricardo Ceballos Garratachea (BBVA)": "Ceballos Garratachea Juan Ricardo (BBVA)",
    "Antonio de Jesús Muñoz Álvarez (Santander)": "Muñoz Álvarez Antonio de Jesús (Santander)",
    "Guillermo Damián Muñoz Álvarez (Banamex)": "Muñoz Álvarez Guillermo Damián (Banamex)",
    "Nava Durán Jorge Heriberto (BBVA)": "Nava Durán Jorge Heriberto (BBVA)"
}

MESES_MAP = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# Inicializar variables de configuración en sesión (Movido después de la conexión a BD)

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

@st.cache_resource(show_spinner="Cargando estructura de base de datos...")
def get_db_sheets(_client):
    """Abre el spreadsheet y obtiene/inicializa todas las hojas necesarias de forma eficiente."""
    spreadsheet = _client.open("Astor_Pagos_DB")
    todas_las_hojas = spreadsheet.worksheets()
    hojas_nombres = [h.title for h in todas_las_hojas]

    # 1. Hoja de Configuración
    if "Configuracion" in hojas_nombres:
        sheet_config = spreadsheet.worksheet("Configuracion")
    else:
        sheet_config = spreadsheet.add_worksheet(title="Configuracion", rows="100", cols="20")

    # 2. Hoja de Retornos
    if "Retorno" in hojas_nombres:
        sheet_retorno = spreadsheet.worksheet("Retorno")
    else:
        sheet_retorno = spreadsheet.add_worksheet(title="Retorno", rows="100", cols="10")
        sheet_retorno.append_row(["Ticket", "Fecha", "Nombre", "Banco", "Proveedor", "Monto Total", "Diferencia", "Retorno a Pagar", "Registrado por", "Ref_Abono"])

    # 3. Hoja de Abonos (la principal)
    hojas_datos = [h for h in todas_las_hojas if h.title not in ["Configuracion", "Retorno", "Usuarios"]]
    if hojas_datos:
        sheet_abonos = hojas_datos[0]
    else:
        sheet_abonos = spreadsheet.sheet1
        
    # 4. Hoja de Retorno Manual
    if "Retorno_Manual" in hojas_nombres:
        sheet_retorno_manual = spreadsheet.worksheet("Retorno_Manual")
    else:
        sheet_retorno_manual = spreadsheet.add_worksheet(title="Retorno_Manual", rows="100", cols="7")
        sheet_retorno_manual.append_row(["Ticket", "Fecha", "Nombre", "Banco", "Proveedor", "Monto Total", "Registrado por"])

    # 5. Hoja de Auditoría
    if "Auditoria" in hojas_nombres:
        sheet_audit = spreadsheet.worksheet("Auditoria")
    else:
        sheet_audit = spreadsheet.add_worksheet(title="Auditoria", rows="100", cols="7")
        sheet_audit.append_row(["Fecha", "Usuario", "Ticket_Abono", "Ticket_Retorno", "Accion", "Dato_Anterior", "Dato_Nuevo"])

    return {
        "spreadsheet": spreadsheet,
        "config": sheet_config,
        "retorno": sheet_retorno,
        "retorno_manual": sheet_retorno_manual,
        "abonos": sheet_abonos,
        "audit": sheet_audit
    }

try:
    client = init_connection()
    db_sheets = get_db_sheets(client)
    # Limpieza forzada de cache para asegurar que no queden datos fantasma anteriores
    st.cache_data.clear()
    
    # Referencias globales para conveniencia (aunque los datos se obtengan via funciones)
    spreadsheet = db_sheets["spreadsheet"]
    sheet_config = db_sheets["config"]
    sheet_retorno = db_sheets["retorno"]
    sheet_retorno_manual = db_sheets["retorno_manual"]
    sheet_audit = db_sheets["audit"]
    sheet = db_sheets["abonos"]

    # --- MURO DE AUTENTICACIÓN ---
    usuarios_db = obtener_usuarios_db(client)
    
    if st.session_state.usuario_logueado is None:
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.session_state.vista_auth == "login":
                st.markdown('<div style="font-size: 3.5rem; text-align: center; margin-bottom: 0px;">🏢</div>', unsafe_allow_html=True)
                st.markdown('<h1 style="text-align: center; color: #1E3A8A; font-weight: 800; margin-top: 0px;">Inside</h1>', unsafe_allow_html=True)
                st.markdown('<p style="text-align: center; color: #64748B; margin-bottom: 30px;">Inicia sesión para continuar</p>', unsafe_allow_html=True)
                
                email_log = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
                pass_log = st.text_input("Contraseña", type="password", placeholder="••••••••")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Iniciar Sesión", type="primary", use_container_width=True):
                    valido = next((u for u in usuarios_db if u["email"].lower().strip() == email_log.lower().strip() and u["pass"].strip() == pass_log.strip()), None)
                    if valido:
                        st.session_state.usuario_logueado = valido
                        st.success(f"✅ ¡Bienvenido, {valido['nombre']}!")
                        st.rerun()
                    else:
                        st.error("❌ Correo o contraseña incorrectos.")
                
                st.markdown("<hr style='margin: 20px 0; border: 0.5px solid #E2E8F0;'>", unsafe_allow_html=True)
                if st.button("¿No tienes cuenta? Regístrate aquí", use_container_width=True):
                    st.session_state.vista_auth = "registro"
                    st.rerun()
            else:
                # Pantalla de Registro
                st.markdown('<div style="font-size: 3.5rem; text-align: center; margin-bottom: 0px;">🆕</div>', unsafe_allow_html=True)
                st.markdown('<h1 style="text-align: center; color: #1E3A8A; font-weight: 800; margin-top: 0px;">Crear Cuenta</h1>', unsafe_allow_html=True)
                
                editores_actuales = [u for u in usuarios_db if u.get("rol") == "Editor"]
                facturas_actuales = [u for u in usuarios_db if u.get("rol") == "Factura"]
                
                can_add_editor = len(editores_actuales) < 2
                can_add_factura = len(facturas_actuales) < 1
                
                if not can_add_editor and not can_add_factura:
                    st.error("🚫 Límite global de usuarios alcanzado (Máximo 2 Editores y 1 Factura).")
                    if st.button("⬅️ Volver", use_container_width=True):
                        st.session_state.vista_auth = "login"; st.rerun()
                else:
                    roles_disponibles = []
                    if can_add_editor: roles_disponibles.append("Editor")
                    if can_add_factura: roles_disponibles.append("Factura")
                    
                    st.info(f"💡 Disponibilidad: {len(editores_actuales)}/2 Editores, {len(facturas_actuales)}/1 Factura.")
                    
                    rol_r = st.selectbox("Selecciona tu Rol", roles_disponibles)
                    n_r = st.text_input("Nombre Completo")
                    e_r = st.text_input("Correo Electrónico")
                    t_r = st.text_input("Teléfono")
                    p_r = st.text_input("Contraseña", type="password")
                    p_c = st.text_input("Confirmar Contraseña", type="password")
                    
                    if st.button("Registrar Usuario", type="primary", use_container_width=True):
                        # 1. Validación de campos vacíos
                        if not all([n_r, e_r, t_r, p_r, p_c]):
                            st.warning("⚠️ Todos los campos son obligatorios.")
                        # 2. Validación de formato de correo
                        elif not re.match(r"[^@]+@[^@]+\.[^@]+", e_r):
                            st.error("❌ El formato del correo electrónico no es válido.")
                        # 3. Validación de teléfono (10 dígitos numéricos)
                        elif not (t_r.isdigit() and len(t_r) == 10):
                            st.error("❌ El teléfono debe tener exactamente 10 dígitos numéricos.")
                        # 4. Validación de contraseñas
                        elif p_r != p_c:
                            st.error("❌ Las contraseñas no coinciden.")
                        else:
                            if registrar_usuario_db(client, {"nombre":n_r, "email":e_r, "tel":t_r, "pass":p_r, "rol":rol_r}):
                                st.success("✅ Cuenta creada exitosamente."); st.session_state.vista_auth = "login"; st.rerun()
                if st.button("⬅️ Ya tengo cuenta", use_container_width=True):
                    st.session_state.vista_auth = "login"; st.rerun()
        st.stop()
except Exception as e:
    st.error("❌ Error de Conexión: No se pudo conectar a Google Sheets.")
    st.error(f"Detalle: {e}")
    st.info("Asegúrate de haber compartido el archivo con el correo de servicio técnico y que el nombre sea 'Astor_Pagos_DB'.")
    st.stop()

# --- FUNCIONES DE ACCESO A DATOS ---
@st.cache_data(ttl=1)
def obtener_config_db():
    try:
        data = sheet_config.get_all_values()
        if not data or len(data) <= 1:
            return None
        return data
    except Exception:
        return None

def guardar_config_db(df_prov):
    try:
        sheet_config.clear()
        encabezados = ["Proveedor", "Visible"] + CUENTAS
        sheet_config.append_row(encabezados)
        for idx, r in df_prov.iterrows():
            visible_str = "True" if r["Visible"] else "False"
            fila = [r["Nombre"], visible_str] + [float(r.get(c, 0.0)) for c in CUENTAS]
            sheet_config.append_row(fila)
        obtener_config_db.clear()
        return True
    except Exception as e:
        return False

def obtener_datos_resiliente(_sheet_obj, expected_cols):
    try:
        # Usar get_all_values para tener control total sobre los encabezados
        data = _sheet_obj.get_all_values()
        if not data or len(data) == 0:
            return pd.DataFrame(columns=expected_cols)
        
        headers = [h.strip() for h in data[0]]
        rows = data[1:]
        
        all_processed = []
        for r in rows:
            # 1. Validación básica de fila
            non_empty = [str(x).strip() for x in r if str(x).strip()]
            if len(non_empty) < 3: continue # Ignorar filas casi vacías o con basura
            
            row_dict = {}
            n = len(r)
            
            # Localizar columna con la "Cuenta" (formato con paréntesis)
            idx_cta = -1
            for i in range(min(5, n)):
                if " (" in str(r[i]):
                    idx_cta = i; break
            
            if idx_cta == 2: # Formato con Ticket: T(0), F(1), C(2), P(3), M(4), R(5)
                row_dict = {
                    "Ticket": r[0], "Fecha": r[1], "Cuenta": r[2], 
                    "Proveedor": r[3] if n > 3 else "---", 
                    "Monto Total": r[4] if n > 4 else "0.00",
                    "Registrado por": r[5] if n > 5 else "---"
                }
            elif idx_cta == 3: # Formato con Ticket + Nombre manual: T(0), F(1), Nom(2), C(3), Prov(4), Mto(5)
                row_dict = {
                    "Ticket": r[0], "Fecha": r[1], "Nombre": r[2], "Cuenta": r[3],
                    "Proveedor": r[4] if n > 4 else "---",
                    "Monto Total": r[5] if n > 5 else "0.00",
                    "Diferencia": r[6] if n > 6 else "0.00",
                    "Registrado por": r[7] if n > 7 else "---"
                }
            elif idx_cta == 1: # Formato sin Ticket: F(0), C(1), P(2), M(3), D(4)
                row_dict = {
                    "Ticket": "---", "Fecha": r[0], "Cuenta": r[1],
                    "Proveedor": r[2] if n > 2 else "---",
                    "Monto Total": r[3] if n > 3 else "0.00",
                    "Diferencia": r[4] if n > 4 else "0.00",
                    "Registrado por": r[5] if n > 5 else "---"
                }
            elif n >= 8: # Nuevo formato: T(0), F(1), Nom(2), Bco(3), Prov(4), Mto(5), Dif(6), Neto/RPP(7), R(8), Ref(9)
                row_dict = {
                    "Ticket": r[0], "Fecha": r[1], "Nombre": r[2], "Banco": r[3],
                    "Proveedor": r[4], "Monto Total": r[5], "Diferencia": r[6], "Retorno a Pagar": r[7],
                    "Registrado por": r[8] if n > 8 else "---",
                    "Ref_Abono": r[9] if n > 9 else "---"
                }
            else:
                # Fallback: Solo si no se encontró Ticket ni Cuenta, intentar por nombres
                row_dict = {c: r[i] if i < n else "" for i, c in enumerate(expected_cols)}
            
            # Limpiar ticket: Si es solo espacio o basura, poner "---"
            if str(row_dict.get("Ticket", "")).strip() in ["", "None", ".","`"]:
                row_dict["Ticket"] = "---"

            all_processed.append(row_dict)
        
        df = pd.DataFrame(all_processed)
        
        # Limpieza de valores numéricos (quitar comas, signos de pesos, etc.)
        def limpiar_numerico(val):
            if pd.isna(val) or str(val).strip() == "": return 0.0
            s = str(val).replace("$","").replace(",","").replace(" ","").replace("%","").strip()
            try: return float(s)
            except: return 0.0

        for col in ["Monto Total", "Diferencia", "Retorno a Pagar", "Monto"]:
            if col in df.columns:
                df[col] = df[col].apply(limpiar_numerico)

        # Normalización de nombres de columnas comunes
        rename_map = {"Monto": "Monto Total", "Tiket": "Ticket", "Pago Total PV": "Monto Total", "Pagado a proveedores": "Monto Total"}
        for old, new in rename_map.items():
            if old in df.columns and new not in df.columns:
                df.rename(columns={old: new}, inplace=True)

        # Compatibilidad: Si existe 'Cuenta' pero no 'Nombre' o 'Banco', desglosarlos
        if "Cuenta" in df.columns:
            if "Nombre" not in df.columns:
                df["Nombre"] = df["Cuenta"].apply(lambda x: str(x).split(" (")[0].strip() if " (" in str(x) else str(x).strip())
            if "Banco" not in df.columns:
                df["Banco"] = df["Cuenta"].apply(lambda x: str(x).split(" (")[1].replace(")", "").strip() if " (" in str(x) else "")
        
        # Asegurar que todas las columnas esperadas existan y estén limpias
        for col in expected_cols:
            if col not in df.columns:
                if col == "Cuenta" and "Nombre" in df.columns and "Banco" in df.columns:
                    df["Cuenta"] = df["Nombre"].astype(str) + " (" + df["Banco"].astype(str) + ")"
                elif col == "Retorno a Pagar" and "Diferencia" in df.columns and "Monto Total" in df.columns:
                    df["Retorno a Pagar"] = df["Monto Total"] - df["Diferencia"]
                else:
                    # Inicializar con 0.0 si es una columna numérica conocida
                    if col in ["Monto Total", "Diferencia", "Retorno a Pagar", "Monto"]:
                        df[col] = 0.0
                    else:
                        df[col] = "---"
            elif col in ["Nombre", "Banco", "Proveedor"]:
                df[col] = df[col].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"⚠️ Error cargando datos: {e}")
        return pd.DataFrame(columns=expected_cols)

@st.cache_data(ttl=1)
def obtener_datos_retorno():
    """Descarga los datos de retornos desde la hoja 'Retorno'"""
    # Admitir tanto el nombre antiguo como el nuevo en la carga
    df = obtener_datos_resiliente(sheet_retorno, ["Ticket", "Fecha", "Nombre", "Banco", "Proveedor", "Monto Total", "Diferencia", "Retorno a Pagar", "Registrado por", "Ref_Abono"])
    if "Retorno a Pagar" in df.columns:
        df.rename(columns={"Retorno a Pagar": "Retornos por pagar"}, inplace=True)
    if "Retornos por pagar" not in df.columns:
        df["Retornos por pagar"] = df["Monto Total"] - df["Diferencia"]
    return df

def registrar_retorno(nombre, banco, proveedor, monto_total, diferencia, retorno_neto, ref_abono="---"):
    """Guarda un nuevo registro de retorno en Google Sheets con 10 columnas"""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        # Calcular Ticket (Serie 20000) de forma eficiente usando el cache
        df_cache = obtener_datos_retorno()
        num_filas = len(df_cache) + 1 # +1 por el encabezado
        nuevo_ticket = 20000 + num_filas
        nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
        sheet_retorno.append_row([nuevo_ticket, fecha_actual, nombre, banco, proveedor, monto_total, diferencia, retorno_neto, nombre_usuario, ref_abono])
        obtener_datos_retorno.clear()
        return True
    except Exception:
        return False

@st.cache_data(ttl=1)
def obtener_datos_retorno_manual():
    """Descarga los datos de retornos manuales desde la hoja 'Retorno_Manual'"""
    # Usar 'Monto Total' para consistencia con el rename_map y otras hojas
    return obtener_datos_resiliente(sheet_retorno_manual, ["Ticket", "Fecha", "Nombre", "Banco", "Proveedor", "Monto Total", "Registrado por"])

def registrar_retorno_manual(nombre, banco, proveedor, monto):
    """Guarda un nuevo registro de retorno manual en Google Sheets con serie 30000"""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_cache = obtener_datos_retorno_manual()
        num_filas = len(df_cache) + 1
        nuevo_ticket = 30000 + num_filas
        nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
        sheet_retorno_manual.append_row([nuevo_ticket, fecha_actual, nombre, banco, proveedor, monto, nombre_usuario])
        obtener_datos_retorno_manual.clear()
        return True
    except Exception:
        return False

def actualizar_retorno_manual(ticket_id, nombre, banco, proveedor, monto):
    """Actualiza un retorno manual y registra en auditoría"""
    try:
        df = obtener_datos_retorno_manual()
        idx = df[df["Ticket"].astype(str) == str(ticket_id)].index
        if idx.empty: return False
        
        orig = df.loc[idx[0]]
        row_idx = idx[0] + 2
        
        cambios_ant = []; cambios_new = []
        if str(orig['Nombre']) != str(nombre): 
            cambios_ant.append(f"Nom: {orig['Nombre']}"); cambios_new.append(f"Nom: {nombre}")
        if str(orig['Banco']) != str(banco): 
            cambios_ant.append(f"Bco: {orig['Banco']}"); cambios_new.append(f"Bco: {banco}")
        if str(orig['Proveedor']) != str(proveedor): 
            cambios_ant.append(f"Prov: {orig['Proveedor']}"); cambios_new.append(f"Prov: {proveedor}")
        if float(orig['Monto']) != float(monto): 
            cambios_ant.append(f"Mto: ${float(orig['Monto']):,.2f}"); cambios_new.append(f"Mto: ${float(monto):,.2f}")
            
        if not cambios_ant: return True
        
        det_ant = " | ".join(cambios_ant); det_new = " | ".join(cambios_new)
        nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
        
        # En gspread, update espera una lista de listas para rangos
        sheet_retorno_manual.update(f"C{row_idx}:G{row_idx}", [[nombre, banco, proveedor, monto, nombre_usuario]])
        registrar_auditoria("---", ticket_id, "Edición Retorno Manual", det_ant, det_new)
        
        obtener_datos_retorno_manual.clear()
        return True
    except Exception as e:
        print(f"Error actualización manual: {e}")
        return False


# Inicializar variables de configuración en sesión desde la Base de Datos
if "ingreso_mensual" not in st.session_state or "proveedores_df" not in st.session_state:
    config_data = obtener_config_db()
    ingreso_val = 2200000.0
    prov_list = []
    
    if config_data:
        headers = config_data[0]
        # Verificar si es el nuevo formato matricial
        es_matriz = (len(headers) >= 7 and headers[2] == CUENTAS[0])
        
        for row in config_data[1:]:
            try:
                if es_matriz:
                    prov = {
                        "Nombre": row[0],
                        "Visible": (row[1] == "True")
                    }
                    for i, c in enumerate(CUENTAS):
                        prov[c] = float(row[2+i]) if (2+i) < len(row) else 0.0
                    prov_list.append(prov)
                else:
                    # Migración desde formato antiguo (JSON/Comas)
                    nombre = row[0]
                    visible = (row[2] == "True")
                    prov = {"Nombre": nombre, "Visible": visible}
                    
                    # Cargar porcentajes base o excepciones
                    pct_base = float(row[1])
                    val_cuenta = row[3] if len(row) > 3 else "Todas"
                    cuentas_base = CUENTAS if val_cuenta == "Todas" else [cx.strip() for cx in val_cuenta.split(",")]
                    
                    excepciones = {}
                    if len(row) > 4:
                        try: excepciones = json.loads(row[4])
                        except: pass
                    
                    for c in CUENTAS:
                        prov[c] = float(excepciones.get(c, pct_base)) if c in cuentas_base else 0.0
                    prov_list.append(prov)
            except:
                pass
    
    if not prov_list:
        p1 = {"Nombre": "Sulín", "Visible": True}
        p2 = {"Nombre": "Acercare", "Visible": True}
        for c in CUENTAS:
            p1[c], p2[c] = 70.0, 30.0
        prov_list = [p1, p2]
        
    st.session_state.ingreso_mensual = ingreso_val
    st.session_state.proveedores_df = pd.DataFrame(prov_list)

@st.cache_data(ttl=600)  # Mantiene los datos en memoria para cargar la página al instante
def obtener_datos():
    """Descarga los datos actuales desde Google Sheets"""
    expected = ["Ticket", "Fecha", "Cuenta", "Proveedor", "Monto Total", "Registrado por"]
    df = obtener_datos_resiliente(sheet, expected)
    if "Monto Total" in df.columns:
        df["Monto Total"] = pd.to_numeric(df["Monto Total"], errors='coerce').fillna(0.0)
    return df

def registrar_pago(cuenta, proveedor, monto):
    """Guarda un nuevo pago como una nueva fila en Google Sheets con Ticket serie 10000"""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Verificar si la hoja está vacía usando el cache (evita get_all_values)
    df_cache = obtener_datos()
    if df_cache.empty and len(spreadsheet.worksheet(sheet.title).get_all_values()) == 0:
        sheet.append_row(["Ticket", "Fecha", "Cuenta", "Proveedor", "Monto", "Registrado por"])
    
    # Calcular Ticket (Serie 10000) usando el cache
    df_cache = obtener_datos()
    num_filas = len(df_cache) + 1 # +1 por el encabezado
    nuevo_ticket = 10000 + num_filas
    nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
    
    # Agregar la nueva fila con el registro del abono y el responsable
    sheet.append_row([nuevo_ticket, fecha_actual, cuenta, proveedor, monto, nombre_usuario])
    obtener_datos.clear()  # Forzar refresco de datos
    return nuevo_ticket

def registrar_auditoria(ticket_abono, ticket_retorno, accion, anterior, nuevo):
    """Guarda un registro en la hoja de auditoría"""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
    try:
        sheet_audit.append_row([fecha_actual, usuario, ticket_abono, ticket_retorno, accion, anterior, nuevo])
        return True
    except: return False

def actualizar_pago_sincronizado(ticket_id, nueva_cuenta, nuevo_prov, nuevo_monto):
    """Actualiza un abono y su retorno asociado en Google Sheets con auditoría detallada"""
    try:
        # 1. Obtener Abono original para comparar
        df_abonos = obtener_datos()
        idx_abonos = df_abonos[df_abonos["Ticket"].astype(str) == str(ticket_id)].index
        if idx_abonos.empty: return False
        
        orig = df_abonos.loc[idx_abonos[0]]
        row_idx = idx_abonos[0] + 2 # +2 por encabezado y 1-based index
        
        # 2. Comparar campos para la auditoria multi-dato
        cambios_ant = []; cambios_new = []
        
        if str(orig['Cuenta']) != str(nueva_cuenta):
            cambios_ant.append(f"Cta: {orig['Cuenta']}")
            cambios_new.append(f"Cta: {nueva_cuenta}")
        if str(orig['Proveedor']) != str(nuevo_prov):
            cambios_ant.append(f"Prov: {orig['Proveedor']}")
            cambios_new.append(f"Prov: {nuevo_prov}")
        if float(orig['Monto Total']) != float(nuevo_monto):
            cambios_ant.append(f"Mto: ${float(orig['Monto Total']):,.0f}")
            cambios_new.append(f"Mto: ${float(nuevo_monto):,.0f}")
            
        if not cambios_ant: return True # No hay cambios reales, salir
        
        det_ant = " | ".join(cambios_ant)
        det_new = " | ".join(cambios_new)
        
        # 3. Actualizar Abono en Google Sheets
        nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
        sheet.update(f"C{row_idx}:F{row_idx}", [[nueva_cuenta, nuevo_prov, nuevo_monto, nombre_usuario]])
        
        # 4. Actualizar Retorno asociado
        df_retorn = obtener_datos_retorno()
        idx_ret = df_retorn[df_retorn["Ref_Abono"].astype(str) == str(ticket_id)].index
        
        # Recalcular valores de retorno sincrónicamente
        dif = float(nuevo_monto) * 0.04
        neto = float(nuevo_monto) - dif
        nombre_tit = nueva_cuenta.split(" (")[0] if " (" in nueva_cuenta else nueva_cuenta
        banco_tit = nueva_cuenta.split(" (")[1].replace(")", "") if " (" in nueva_cuenta else ""
        
        t_ret_id = "---"
        if not idx_ret.empty:
            r_idx_ret = idx_ret[0] + 2
            t_ret_id = df_retorn.loc[idx_ret[0], "Ticket"]
            sheet_retorno.update(f"C{r_idx_ret}:I{r_idx_ret}", [[nombre_tit, banco_tit, nuevo_prov, nuevo_monto, dif, neto, nombre_usuario]])
        
        # 5. Registrar Auditoría combinada
        registrar_auditoria(ticket_id, t_ret_id, "Edición", det_ant, det_new)
        
        obtener_datos.clear()
        obtener_datos_retorno.clear()
        obtener_auditoria.clear()
        return True
    except Exception as e:
        print(f"Error actualización: {e}")
        return False

# --- BARRA LATERAL (INFO Y LOGOUT) ---
st.sidebar.markdown(f"""
    <div style="padding: 15px; background: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 20px;">
        <p style="margin:0; font-size: 0.75rem; color: #64748B; font-weight: bold; text-transform: uppercase;">Sesión Activa</p>
        <p style="margin:5px 0 0 0; font-weight: 800; color: #1E3A8A; font-size: 1.1rem;">{st.session_state.usuario_logueado['nombre']}</p>
        <p style="margin:4px 0 0 0; font-size: 0.7rem; color: #2563EB; font-weight: 800; text-transform: uppercase; background: #DBEAFE; padding: 2px 8px; border-radius: 4px; display: inline-block;">Rol: {st.session_state.usuario_logueado['rol']}</p>
    </div>
""", unsafe_allow_html=True)

is_editor = st.session_state.usuario_logueado.get('rol') == 'Editor'
is_factura = st.session_state.usuario_logueado.get('rol') == 'Factura'

if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.usuario_logueado = None
    st.session_state.vista_auth = "login"
    st.rerun()





# --- INTERFAZ GRAFICA (UI) ---

st.title("💸 Inside - Gestión de Rol de Pagos")

# --- DASHBOARD DE TOTALES GLOBALES ---
if is_editor or is_factura:
    df_gl_abono = obtener_datos()
else:
    df_gl_abono = pd.DataFrame()
df_gl_retorno = obtener_datos_retorno()
df_gl_manual = obtener_datos_retorno_manual()

# Función para sumar solo montos que NO parecen tickets (fuera del rango 10,000-21,000)
def suma_valida(df, col):
    if df.empty or col not in df.columns: return 0.0
    vals = pd.to_numeric(df[col], errors='coerce').fillna(0)
    # Filtro: Ignorar valores que coincidan con la serie de tickets 10000+ o Retornos 20000+
    return vals[(vals < 9999) | (vals > 41000)].sum()

t_abonado = suma_valida(df_gl_abono, "Monto Total")
t_ret_efe = suma_valida(df_gl_retorno, "Retornos por pagar")
dif_ret = suma_valida(df_gl_retorno, "Diferencia")
t_manual = pd.to_numeric(df_gl_manual["Monto Total"], errors='coerce').fillna(0).sum()
adeudo = t_ret_efe - t_manual

st.write("<br>", unsafe_allow_html=True)
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

def render_metric_card(col, title, value, border_color):
    html_card = f"""
    <body style="margin:0; padding:0; overflow:hidden; background: linear-gradient(135deg, #F0F2F5 0%, #E2E8F0 100%) !important;">
    <div style="
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        border-radius: 12px;
        border-top: 5px solid {border_color};
        padding: 20px;
        background: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center;
        height: 75px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin: 0px;
    ">
        <span style="margin:0; font-size: 0.7rem; color: #64748b; font-weight: bold; text-transform: uppercase;">{title}</span>
        <span style="margin: 6px 0 0 0; color: {border_color} !important; font-size: 1.4rem; font-weight: 800; display: block;">${value:,.2f}</span>
    </div>
    </body>
    """
    with col:
        st.components.v1.html(html_card, height=120)

color_adeudo = "#10b981" if adeudo <= 0 else "#ef4444"
semaforo_m = "🟢" if adeudo <= 0 else "🔴"

render_metric_card(col_m1, "Total Abonado", t_abonado, "#3b82f6") # Azul
render_metric_card(col_m2, "Efectivo de Retorno", t_ret_efe, "#f59e0b") # Naranja
render_metric_card(col_m3, "Diferencia", dif_ret, "#ef4444") # Rojo
render_metric_card(col_m4, "Retorno Manual", t_manual, "#10b981") # Verde
render_metric_card(col_m5, f"{semaforo_m} Adeudo", adeudo, color_adeudo) # Dinámico
st.write("<br>", unsafe_allow_html=True)

@st.cache_data(ttl=1)
def obtener_auditoria():
    cols = ["Fecha", "Usuario", "Ticket_Abono", "Ticket_Retorno", "Accion", "Dato_Anterior", "Dato_Nuevo"]
    try:
        data = sheet_audit.get_all_records()
        if not data: return pd.DataFrame(columns=cols)
        return pd.DataFrame(data)
    except: return pd.DataFrame(columns=cols)

if is_editor:
    # 1. PRONÓSTICO DE INGRESO
    st.header("📈 Pronóstico de Ingreso", divider="gray")
    col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
    with col_p1:
        nuevo_ingreso = st.number_input(f"Ingreso Mensual (${st.session_state.ingreso_mensual:,.2f} MXN)", value=st.session_state.ingreso_mensual, step=1000.0)
        st.session_state.ingreso_mensual = nuevo_ingreso
    with col_p2:
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_actual_idx = datetime.now().month - 1
        st.selectbox("Mes", meses, index=mes_actual_idx)
    with col_p3:
        st.number_input("Año", value=datetime.now().year, min_value=2020, max_value=2100)
    
    # 2. REGISTRO A NUEVO PAGO A PROVEEDOR
    st.header("📝 Registro a nuevo pago a proveedor", divider="gray")
    st.write("Selecciona la cuenta, el proveedor al que se le paga y el monto del pago realizado.")
    
    # Recuadro gris para el registro
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cuenta_seleccionada = st.selectbox("Nombre / Cuenta Bancaria", CUENTAS)
        with col2:
            prov_df = st.session_state.proveedores_df
            # Identificar columna del porcentaje para la cuenta seleccionada
            col_pct = cuenta_seleccionada
            
            # Filtro: Mostrar solo proveedores visibles Y que tengan porcentaje > 0 en esta cuenta
            prov_validos = prov_df[(prov_df["Visible"] == True) & (prov_df[col_pct] > 0)]
            lista_prov_form = prov_validos["Nombre"].unique().tolist()
            
            if not lista_prov_form:
                st.warning(f"⚠️ No hay proveedores configurados para {cuenta_seleccionada}.")
                proveedor_seleccionado = None
            else:
                proveedor_seleccionado = st.selectbox("Proveedor Destino", lista_prov_form, key=f"abono_prov_{cuenta_seleccionada}")
                pct_actual = prov_validos[prov_validos["Nombre"] == proveedor_seleccionado][col_pct].iloc[0]
                st.info(f"💡 Reparto actual: {pct_actual}%")
        with col3:
            monto_ingresado = st.number_input(f"Monto del Pago (${st.session_state.monto_pago_val:,.2f} MXN)", min_value=0.01, value=50000.0, step=100.0)
            st.session_state.monto_pago_val = monto_ingresado
        
        st.write("<br>", unsafe_allow_html=True)
        btn_guardar = st.button("Guardar Registro", type="primary", use_container_width=True)
        
        if btn_guardar:
            if not proveedor_seleccionado:
                st.error("Debes seleccionar un proveedor válido con reparto activo (>0%).")
            elif monto_ingresado <= 0:
                st.warning("El monto debe ser mayor a 0.")
            else:
                # Validación de seguridad final para evitar registros "fantasma"
                pct_final = prov_df[prov_df["Nombre"] == proveedor_seleccionado][cuenta_seleccionada].iloc[0]
                
                if pct_final <= 0:
                    st.error(f"❌ Error crítico: El proveedor {proveedor_seleccionado} no tiene permisos para esta cuenta (0%).")
                else:
                    with st.spinner("Guardando Pago y Retorno en la Nube..."):
                        try:
                            # 1. Registrar Pago a Proveedor y obtener Ticket
                            id_abono = registrar_pago(cuenta_seleccionada, proveedor_seleccionado, float(monto_ingresado))
                            
                            # 2. Registrar Retorno Automáticamente cargando la referencia
                            # Desglosar cuenta en Nombre y Banco
                            nombre_tit = cuenta_seleccionada.split(" (")[0] if " (" in cuenta_seleccionada else cuenta_seleccionada
                            banco_tit = cuenta_seleccionada.split(" (")[1].replace(")", "") if " (" in cuenta_seleccionada else ""
                            
                            # Cálculo: Total * 0.04
                            dif_calculada = float(monto_ingresado) * 0.04
                            neto_retorno = float(monto_ingresado) - dif_calculada
                            
                            registrar_retorno(nombre_tit, banco_tit, proveedor_seleccionado, float(monto_ingresado), float(dif_calculada), float(neto_retorno), ref_abono=id_abono)
                            
                            st.success(f"✅ ¡Pago y Retorno de ${monto_ingresado:,.2f} MXN registrados exitosamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Ocurrió un error al guardar: {e}")


if is_editor:
    # --- HISTORIAL DE ABONO (DESPLEGABLE) ---
    with st.expander("🕒 Ver Historial de Movimientos Abono", expanded=False):
        df_historial = obtener_datos()
        if df_historial.empty:
            st.info("Aún no se han registrado abonos.")
        else:
            registros_recientes = df_historial.sort_values(by="Fecha", ascending=False).copy()
            if "Cuenta" in registros_recientes.columns:
                registros_recientes["Cuenta"] = registros_recientes["Cuenta"].replace(MAPEO_NOMBRES_ANTIGUOS)
            
            registros_recientes['Fecha_DT'] = pd.to_datetime(registros_recientes['Fecha'], errors='coerce')
            registros_recientes['Mes_Filtro'] = registros_recientes['Fecha_DT'].dt.month.map(MESES_MAP)
            registros_recientes['Nombre_Filtro'] = registros_recientes['Cuenta'].astype(str).apply(lambda x: x.split(" (")[0] if " (" in x else x)
            registros_recientes['Banco_Filtro'] = registros_recientes['Cuenta'].astype(str).apply(lambda x: x.split(" (")[1].replace(")", "") if " (" in x else "")
            
            st.markdown("##### 🔍 Filtros de Búsqueda")
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            df_filtrado = registros_recientes.copy()
            
            with f_col1:
                lista_meses = ["Todos"] + [m for m in MESES_MAP.values() if m in df_filtrado['Mes_Filtro'].values]
                sel_mes = st.selectbox("Mes", lista_meses, key="f_mes_abono")
                if sel_mes != "Todos": df_filtrado = df_filtrado[df_filtrado['Mes_Filtro'] == sel_mes]
            with f_col2:
                lista_cuentas = ["Todas"] + sorted(df_filtrado['Nombre_Filtro'].dropna().unique().tolist())
                sel_cuenta = st.selectbox("Cuenta (Titular)", lista_cuentas, key="f_cta_abono")
                if sel_cuenta != "Todas": df_filtrado = df_filtrado[df_filtrado['Nombre_Filtro'] == sel_cuenta]
            with f_col3:
                lista_bancos = ["Todos"] + sorted([b for b in df_filtrado['Banco_Filtro'].dropna().unique().tolist() if b])
                sel_banco = st.selectbox("Banco", lista_bancos, key="f_bco_abono")
                if sel_banco != "Todos": df_filtrado = df_filtrado[df_filtrado['Banco_Filtro'] == sel_banco]
            with f_col4:
                lista_provs = ["Todos"] + sorted(df_filtrado['Proveedor'].dropna().unique().tolist())
                sel_prov = st.selectbox("Proveedor", lista_provs, key="f_prov_abono")
                if sel_prov != "Todos": df_filtrado = df_filtrado[df_filtrado['Proveedor'] == sel_prov]
                    
            st.divider()
            c_tk, c1, c2, c3, c4, c5, c6 = st.columns([0.6, 1.0, 1.5, 0.7, 1.0, 1.0, 1.0])
            c_tk.markdown("**Ticket**"); c1.markdown("**Fecha**"); c2.markdown("**Nombre**"); c3.markdown("**Cuenta**"); c4.markdown("**Proveedor**"); c5.markdown("**Monto**"); c6.markdown("**Usuario**")
            st.divider()
            
            if df_filtrado.empty: st.info("No se encontraron registros.")
            else:
                for idx, row in df_filtrado.iterrows():
                    t_id = str(row.get('Ticket', '---'))
                    # Contenedor con borde para cada ticket
                    with st.container(border=True):
                        c_tk, c1, c2, c3, c4 = st.columns([1.0, 1.2, 1.5, 1.0, 1.5])
                        c_tk.write(f"🎫 **{t_id}**")
                        c1.write(f"📅 {row['Fecha'].split(' ')[0]}")
                        c2.write(f"🏦 {row['Cuenta']}")
                        c3.write(f"💰 ${float(row.get('Monto Total', 0)):,.0f}")
                        
                        with c4:
                            with st.popover("✏️ Editar Ticket", use_container_width=True):
                                # Seccion de Edicion
                                st.markdown("##### ✏️ Editar Registro")
                                nueva_cta = st.selectbox("Cambiar Cuenta", CUENTAS, index=CUENTAS.index(row['Cuenta']) if row['Cuenta'] in CUENTAS else 0, key=f"edit_cta_{t_id}")
                                
                                # Filtrar proveedores validos para la nueva cuenta
                                p_df = st.session_state.proveedores_df
                                p_validos = p_df[(p_df["Visible"] == True) & (p_df[nueva_cta] > 0)]
                                l_prov = p_validos["Nombre"].unique().tolist()
                                nueva_prov = st.selectbox("Cambiar Proveedor", l_prov, index=l_prov.index(row['Proveedor']) if row['Proveedor'] in l_prov else 0, key=f"edit_prov_{t_id}")
                                
                                nuevo_mto = st.number_input("Nuevo Monto", value=float(row.get('Monto Total', 0)), key=f"edit_mto_{t_id}")
                                
                                if st.button("💾 Actualizar y Sincronizar", key=f"btn_edit_{t_id}", type="primary", use_container_width=True):
                                    with st.spinner("Actualizando..."):
                                        if actualizar_pago_sincronizado(t_id, nueva_cta, nueva_prov, nuevo_mto):
                                            st.success("✅ Registro actualizado.")
                                            st.rerun()
                                        else:
                                            st.error("❌ Error al actualizar.")
                                
                                st.divider()
                                # Seccion de Auditoria
                                st.markdown("##### 📜 Historial de Cambios")
                                df_aud = obtener_auditoria()
                                df_este_ticket = df_aud[df_aud["Ticket_Abono"].astype(str) == t_id]
                                if df_este_ticket.empty:
                                    st.info("Sin ediciones previas.")
                                else:
                                    st.dataframe(df_este_ticket[["Fecha", "Usuario", "Accion", "Dato_Anterior", "Dato_Nuevo"]], use_container_width=True, hide_index=True)

# 3. RETORNOS POR PAGAR
st.header("🔄 Retornos por pagar", divider="gray")
st.write("El registro de retornos es ahora automático al reportar un pago a proveedor.")

if is_factura:    
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            cuenta_r = st.selectbox("Nombre / Cuenta Bancaria", CUENTAS, key="ret_cta_manual")
        with col2:
            p_df = st.session_state.proveedores_df
            p_validos = p_df[(p_df["Visible"] == True) & (p_df[cuenta_r] > 0)]
            l_prov = p_validos["Nombre"].unique().tolist()
            if not l_prov:
                st.warning(f"⚠️ Sin proveedores activos para {cuenta_r}")
                prov_r = None
            else:
                prov_r = st.selectbox("Proveedor Destino", l_prov, key="ret_prov_manual")
                pct_actual = p_validos[p_validos["Nombre"] == prov_r][cuenta_r].iloc[0]
                st.info(f"💡 Reparto actual: {pct_actual}%")
        with col3:
            # Inicializar variable de sesión para el monto del retorno si no existe
            if "monto_retorno_val" not in st.session_state:
                st.session_state.monto_retorno_val = 50000.0
            monto_r = st.number_input(f"Monto del Retorno (${st.session_state.monto_retorno_val:,.2f} MXN)", min_value=0.0, value=st.session_state.monto_retorno_val, step=100.0, key="ret_input_monto")
            st.session_state.monto_retorno_val = monto_r
        
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Guardar Registro de Retorno", type="primary", use_container_width=True, key="ret_btn_manual"):
            if not prov_r:
                st.error("Debes seleccionar un proveedor válido.")
            elif monto_r <= 0:
                st.warning("El monto debe ser mayor a 0.")
            else:
                with st.spinner("Guardando Retorno Manual..."):
                    # Desglosar cuenta
                    nombre_tit = cuenta_r.split(" (")[0] if " (" in cuenta_r else cuenta_r
                    banco_tit = cuenta_r.split(" (")[1].replace(")", "") if " (" in cuenta_r else ""
                    
                    if registrar_retorno_manual(nombre_tit, banco_tit, prov_r, float(monto_r)):
                        st.success(f"✅ ¡Retorno manual de ${monto_r:,.2f} MXN registrado exitosamente!")
                        st.session_state.monto_retorno_val = 0.0 # Reset para el siguiente
                        st.rerun()
                    else:
                        st.error("❌ Ocurrió un error al guardar el retorno manual.")




# Tabla resumen de retornos
df_h_ret = obtener_datos_retorno()
df_h_manual = obtener_datos_retorno_manual()

if not df_h_ret.empty or not df_h_manual.empty:
    resumen_ret = []
    for c in CUENTAS:
        nombre = c.split(" (")[0] if " (" in c else c
        banco = c.split(" (")[1].replace(")", "") if " (" in c else ""
        
        # 1. Datos Automáticos
        df_c = df_h_ret[(df_h_ret["Nombre"] == nombre) & (df_h_ret["Banco"] == banco)]
        total_monto_prov = pd.to_numeric(df_c["Monto Total"], errors='coerce').fillna(0).sum()
        total_ret_pagar_auto = pd.to_numeric(df_c["Diferencia"], errors='coerce').fillna(0).sum()
        retorno_auto_neto = total_monto_prov - total_ret_pagar_auto
        
        # 2. Datos Manuales (Pagados)
        df_m = df_h_manual[(df_h_manual["Nombre"] == nombre) & (df_h_manual["Banco"] == banco)]
        total_pagado_manual = pd.to_numeric(df_m["Monto Total"], errors='coerce').fillna(0).sum()
        
        # 3. Adeudo final
        adeudo_num = retorno_auto_neto - total_pagado_manual
        semaforo_t = "🟢" if adeudo_num <= 0 else "🔴"
        
        resumen_ret.append({
            "Nombre": nombre,
            "Cuenta": banco,
            "Pago Total a Proveedor": total_monto_prov,
            "Diferencia": total_ret_pagar_auto,
            "Retornos por pagar": retorno_auto_neto,
            "Retorno pagado": total_pagado_manual,
            "Adeudo": f"{semaforo_t} ${adeudo_num:,.2f}"
        })
    df_ret_final = pd.DataFrame(resumen_ret)
    
    # Formatear columnas de dinero (excepto Adeudo que ya está formateado)
    for col in ["Pago Total a Proveedor", "Diferencia", "Retornos por pagar", "Retorno pagado"]:
        df_ret_final[col] = df_ret_final[col].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(df_ret_final, use_container_width=True, hide_index=True)

else:
    st.info("No hay registros de retorno aún.")

# --- HISTORIAL DE RETORNO (DESPLEGABLE) ---
with st.expander("🕒 Ver Historial de Movimientos Retornos", expanded=False):
    df_h_ret_full = obtener_datos_retorno()
    if df_h_ret_full.empty:
        st.info("Aún no se han registrado retornos.")
    else:
        ret_recientes = df_h_ret_full.sort_values(by="Fecha", ascending=False).copy()
        ret_recientes['Fecha_DT'] = pd.to_datetime(ret_recientes['Fecha'], errors='coerce')
        ret_recientes['Mes_Filtro'] = ret_recientes['Fecha_DT'].dt.month.map(MESES_MAP)
        ret_recientes['Nombre_Filtro'] = ret_recientes['Nombre'].astype(str)
        ret_recientes['Banco_Filtro'] = ret_recientes['Banco'].astype(str)
        
        st.markdown("##### 🔍 Filtros de Búsqueda")
        fr_col1, fr_col2, fr_col3, fr_col4 = st.columns(4)
        df_ret_filtrado = ret_recientes.copy()
        
        with fr_col1:
            sel_mes_r = st.selectbox("Mes", ["Todos"] + [m for m in MESES_MAP.values() if m in df_ret_filtrado['Mes_Filtro'].values], key="f_mes_ret")
            if sel_mes_r != "Todos": df_ret_filtrado = df_ret_filtrado[df_ret_filtrado['Mes_Filtro'] == sel_mes_r]
        with fr_col2:
            sel_cta_r = st.selectbox("Cuenta (Titular)", ["Todas"] + sorted(df_ret_filtrado['Nombre_Filtro'].dropna().unique().tolist()), key="f_cta_ret")
            if sel_cta_r != "Todas": df_ret_filtrado = df_ret_filtrado[df_ret_filtrado['Nombre_Filtro'] == sel_cta_r]
        with fr_col3:
            bancos_r = ["Todos"] + sorted([b for b in df_ret_filtrado['Banco_Filtro'].dropna().unique().tolist() if b])
            sel_bco_r = st.selectbox("Banco", bancos_r, key="f_bco_ret")
            if sel_bco_r != "Todos": df_ret_filtrado = df_ret_filtrado[df_ret_filtrado['Banco_Filtro'] == sel_bco_r]
        with fr_col4:
            provs_r = ["Todos"] + sorted(df_ret_filtrado['Proveedor'].dropna().unique().tolist())
            sel_prov_r = st.selectbox("Proveedor", provs_r, key="f_prov_ret")
            if sel_prov_r != "Todos": df_ret_filtrado = df_ret_filtrado[df_ret_filtrado['Proveedor'] == sel_prov_r]
                
        st.divider()
        cr_tk, cr1, cr2, cr3, cr4, cr5, cr6, cr7, cr8 = st.columns([0.6, 0.7, 1.0, 0.5, 0.8, 0.8, 0.8, 0.8, 0.8])
        cr_tk.markdown("<small>**Ticket**</small>", unsafe_allow_html=True)
        cr1.markdown("<small>**Fecha**</small>", unsafe_allow_html=True)
        cr2.markdown("<small>**Nombre**</small>", unsafe_allow_html=True)
        cr3.markdown("<small>**Cuenta**</small>", unsafe_allow_html=True)
        cr4.markdown("<small>**Proveedor**</small>", unsafe_allow_html=True)
        cr5.markdown("<small>**P. Total**</small>", unsafe_allow_html=True)
        cr6.markdown("<small>**Diferencia**</small>", unsafe_allow_html=True)
        cr7.markdown("<small>**Retorno por pagar**</small>", unsafe_allow_html=True)
        cr8.markdown("<small>**Usuario**</small>", unsafe_allow_html=True)
        st.divider()
        
        if df_ret_filtrado.empty: st.info("No se encontraron registros.")
        else:
            for idx, row in df_ret_filtrado.iterrows():
                cr_tk, cr1, cr2, cr3, cr4, cr5, cr6, cr7, cr8 = st.columns([0.6, 0.7, 1.0, 0.5, 0.8, 0.8, 0.8, 0.8, 0.8])
                cr_tk.write(f"<small>`{row.get('Ticket', '---')}`</small>", unsafe_allow_html=True)
                fecha_str = str(row["Fecha"]).split(" ")[0]
                cr1.write(f"<small>{fecha_str}</small>", unsafe_allow_html=True)
                cr2.write(f"<small>{row.get('Nombre', '---')}</small>", unsafe_allow_html=True)
                cr3.write(f"<small>{row.get('Banco', '---')}</small>", unsafe_allow_html=True)
                cr4.write(f"<small>{str(row['Proveedor'])}</small>", unsafe_allow_html=True)
                cr5.write(f"<small>${pd.to_numeric(row.get('Monto Total', 0), errors='coerce'):,.2f}</small>", unsafe_allow_html=True)
                cr6.write(f"<small>${pd.to_numeric(row.get('Diferencia', 0), errors='coerce'):,.2f}</small>", unsafe_allow_html=True)
                cr7.write(f"<small>${pd.to_numeric(row.get('Retornos por pagar', 0), errors='coerce'):,.2f}</small>", unsafe_allow_html=True)
                cr8.write(f"<small>{row.get('Registrado por', '---')}</small>", unsafe_allow_html=True)


if is_factura:
    with st.expander("🕒 Ver Historial de Retornos Manuales (Solo Factura)", expanded=False):
        df_h_m = obtener_datos_retorno_manual()
        if df_h_m.empty:
            st.info("Aún no se han registrado retornos manuales.")
        else:
            m_recientes = df_h_m.sort_values(by="Fecha", ascending=False).copy()
            m_recientes['Fecha_DT'] = pd.to_datetime(m_recientes['Fecha'], errors='coerce')
            m_recientes['Mes_Filtro'] = m_recientes['Fecha_DT'].dt.month.map(MESES_MAP)
            
            st.markdown("##### 🔍 Filtros de Búsqueda")
            fm_col1, fm_col2, fm_col3, fm_col4 = st.columns(4)
            df_m_filtrado = m_recientes.copy()
            
            with fm_col1:
                sel_mes_m = st.selectbox("Mes", ["Todos"] + [m for m in MESES_MAP.values() if m in df_m_filtrado['Mes_Filtro'].values], key="f_mes_m")
                if sel_mes_m != "Todos": df_m_filtrado = df_m_filtrado[df_m_filtrado['Mes_Filtro'] == sel_mes_m]
            with fm_col2:
                sel_cta_m = st.selectbox("Cuenta (Titular)", ["Todas"] + sorted(df_m_filtrado['Nombre'].dropna().unique().tolist()), key="f_cta_m")
                if sel_cta_m != "Todas": df_m_filtrado = df_m_filtrado[df_m_filtrado['Nombre'] == sel_cta_m]
            with fm_col3:
                bancos_m = ["Todos"] + sorted([b for b in df_m_filtrado['Banco'].dropna().unique().tolist() if b])
                sel_bco_m = st.selectbox("Banco", bancos_m, key="f_bco_m")
                if sel_bco_m != "Todos": df_m_filtrado = df_m_filtrado[df_m_filtrado['Banco'] == sel_bco_m]
            with fm_col4:
                provs_m = ["Todos"] + sorted(df_m_filtrado['Proveedor'].dropna().unique().tolist())
                sel_prov_m = st.selectbox("Proveedor", provs_m, key="f_prov_m")
                if sel_prov_m != "Todos": df_m_filtrado = df_m_filtrado[df_m_filtrado['Proveedor'] == sel_prov_m]
                    
            st.divider()
            cm_tk, cm1, cm2, cm3, cm4, cm5, cm6 = st.columns([0.6, 1.0, 1.5, 0.7, 1.0, 1.0, 1.0])
            cm_tk.markdown("**Ticket**"); cm1.markdown("**Fecha**"); cm2.markdown("**Nombre**"); cm3.markdown("**Banco**"); cm4.markdown("**Proveedor**"); cm5.markdown("**Monto**"); cm6.markdown("**Usuario**")
            st.divider()
            
            if df_m_filtrado.empty: st.info("No se encontraron registros.")
            else:
                for idx, row in df_m_filtrado.iterrows():
                    tm_id = str(row.get('Ticket', '---'))
                    with st.container(border=True):
                        col_main, col_edit = st.columns([4, 1])
                        with col_main:
                            c_tk, c_f, c_n, c_p, c_m = st.columns([0.8, 1.2, 2.0, 1.5, 1.5])
                            c_tk.write(f"🎫 **{tm_id}**")
                            c_f.write(f"📅 {str(row['Fecha']).split(' ')[0]}")
                            c_n.write(f"🏦 {row['Nombre']} ({row['Banco']})")
                            c_p.write(f"👤 {row['Proveedor']}")
                            c_m.write(f"💰 ${pd.to_numeric(row.get('Monto Total', 0), errors='coerce'):,.0f}")
                        
                        with col_edit:
                            with st.popover("✏️ Editar", use_container_width=True):
                                st.markdown("##### ✏️ Editar Retorno Manual")
                                cta_full = f"{row['Nombre']} ({row['Banco']})"
                                e_cta = st.selectbox("Cambiar Cuenta", CUENTAS, index=CUENTAS.index(cta_full) if cta_full in CUENTAS else 0, key=f"edit_cta_m_{tm_id}")
                                
                                p_df_e = st.session_state.proveedores_df
                                p_val_e = p_df_e[(p_df_e["Visible"] == True) & (p_df_e[e_cta] > 0)]
                                l_prov_e = p_val_e["Nombre"].unique().tolist()
                                e_prov = st.selectbox("Cambiar Proveedor", l_prov_e, index=l_prov_e.index(row['Proveedor']) if row['Proveedor'] in l_prov_e else 0, key=f"edit_prov_m_{tm_id}")
                                
                                e_mto = st.number_input("Nuevo Monto", value=float(pd.to_numeric(row.get('Monto Total', 0), errors='coerce')), key=f"edit_mto_m_{tm_id}")
                                
                                if st.button("💾 Guardar Cambios", key=f"btn_edit_m_{tm_id}", type="primary", use_container_width=True):
                                    with st.spinner("Actualizando..."):
                                        nom_e = e_cta.split(" (")[0] if " (" in e_cta else e_cta
                                        bco_e = e_cta.split(" (")[1].replace(")", "") if " (" in e_cta else ""
                                        if actualizar_retorno_manual(tm_id, nom_e, bco_e, e_prov, e_mto):
                                            st.success("✅ Registro actualizado.")
                                            st.rerun()
                                        else:
                                            st.error("❌ Error al actualizar.")


if is_editor:
    # Lógica de preparación de datos para el Tablero (Validaciones)
    df_prov = st.session_state.proveedores_df
    prov_visibles = df_prov[df_prov["Visible"] == True]
    errores_porcentaje = [c for c in CUENTAS if abs(prov_visibles[c].sum() - 100.0) > 0.01]
    
    if errores_porcentaje:
        st.warning(f"⚠️ Atención: Los porcentajes no suman 100% para algunas cuentas. El tablero se habilitará cuando la configuración sea correcta.")
        # No detenemos la ejecución para permitir llegar a la sección de Configuración abajo
    else:
        # 4. TABLERO DE CONTROL
        st.header("📊 Tablero de Control - Pagos por realizar", divider="gray")
        
        df_historial = obtener_datos()
        if not df_historial.empty and "Cuenta" in df_historial.columns:
            df_historial["Cuenta"] = df_historial["Cuenta"].replace(MAPEO_NOMBRES_ANTIGUOS)
    
        filas_resumen = []
        for c in CUENTAS:
            if " (" in c:
                nombre = c.split(" (")[0]
                banco = c.split(" (")[1].replace(")", "")
            else:
                nombre = c; banco = ""
                
            for idx, row_prov in prov_visibles.iterrows():
                p = row_prov["Nombre"]
                pct = float(row_prov.get(c, 0.0))
                if pct > 0:
                    ingreso_cuenta = st.session_state.ingreso_mensual / 5.0
                    base_reparto = ingreso_cuenta * 0.40
                    pagos_a_realizar = base_reparto * (pct / 100.0)
                    filas_resumen.append({
                        "Nombre": nombre, "Cuenta": banco, "Clave_Original": c,
                        "Ingreso": ingreso_cuenta, "Proveedor": p,
                        "Porcentaje": f"{pct}%", "Pagos a realizar": pagos_a_realizar
                    })
        
        if not filas_resumen:
            df_resumen = pd.DataFrame(columns=["Nombre", "Cuenta", "Clave_Original", "Ingreso", "Proveedor", "Porcentaje", "Pagos a realizar"])
        else:
            df_resumen = pd.DataFrame(filas_resumen)
    
        if not df_historial.empty:
            df_historial["Monto Total"] = pd.to_numeric(df_historial["Monto Total"], errors='coerce').fillna(0)
            pagos_agrupados = df_historial.groupby(["Cuenta", "Proveedor"])["Monto Total"].sum().reset_index()
            pagos_agrupados.rename(columns={"Monto Total": "Pagado a proveedores", "Cuenta": "Clave_Original"}, inplace=True)
            df_resumen = pd.merge(df_resumen, pagos_agrupados, on=["Clave_Original", "Proveedor"], how="left")
            df_resumen["Pagado a proveedores"] = df_resumen["Pagado a proveedores"].fillna(0)
        else:
            df_resumen["Pagado a proveedores"] = 0.0
    
        if "Pagos a realizar" not in df_resumen.columns:
            df_resumen["Pagos a realizar"] = 0.0
        
        df_resumen["Saldo pendiente"] = df_resumen["Pagos a realizar"] - df_resumen["Pagado a proveedores"]
    
        def semaforo_saldo(row):
            pago, abono, saldo = row["Pagos a realizar"], row["Pagado a proveedores"], row["Saldo pendiente"]
            pct = abono / pago if pago > 0 else 1.0
            saldo_str = f"${saldo:,.2f}"
            if pct <= 0.35: return f"🔴 {saldo_str}"
            elif pct < 0.80: return f"🟡 {saldo_str}"
            else: return f"🟢 {saldo_str}"
    
        for col in ["Ingreso", "Pagos a realizar", "Pagado a proveedores"]:
            df_resumen[col + "_str"] = df_resumen[col].apply(lambda x: f"${x:,.2f}")
        df_resumen["Saldo pendiente_str"] = df_resumen.apply(semaforo_saldo, axis=1)
    
        for c in CUENTAS:
            df_cuenta = df_resumen[df_resumen["Clave_Original"] == c].copy()
            if df_cuenta.empty: continue
            ingreso = df_cuenta.iloc[0]["Ingreso"]
            total_pago = df_cuenta["Pagos a realizar"].sum()
            total_abono = df_cuenta["Pagado a proveedores"].sum()
            total_saldo = df_cuenta["Saldo pendiente"].sum()
            
            bg_color = 'rgba(100, 149, 237, 0.15)' if "BBVA" in c else ('rgba(255, 105, 97, 0.15)' if "Santander" in c else ('rgba(173, 216, 230, 0.15)' if "Banamex" in c else 'rgba(240, 240, 240, 0.1)'))
            logo_banco = "🏦" if "BBVA" in c else ("💳" if "Santander" in c else ("🏛️" if "Banamex" in c else "👤"))
            pct_str = f"({(total_abono/total_pago)*100:.0f}%)" if total_pago > 0 else "(0%)"
            estado_saldo = "🟢" if total_saldo <= 0 else ("🟡" if total_abono > 0 else "🔴")
            
            # Formateo tipo tabla usando una fuente más pequeña y etiquetas cortas
            def pad_nbsp(text, length):
                return str(text) + ("\u00A0" * max(0, length - len(str(text))))
    
            nombre_col = pad_nbsp(f"{logo_banco} {c}", 46)
            monto_ing_col = pad_nbsp(f"Ing: ${ingreso:,.0f}", 16)
            monto_pag_col = pad_nbsp(f"Pag: ${total_abono:,.0f}", 15)
            monto_sal_col = f"Sal: {estado_saldo} ${total_saldo:,.0f} {pct_str}"
            
            titulo_expander = f"{nombre_col} | {monto_ing_col} | {monto_pag_col} | {monto_sal_col}"
            
            with st.expander(titulo_expander, expanded=True):
                df_disp = df_cuenta[["Proveedor", "Porcentaje", "Pagos a realizar_str", "Pagado a proveedores_str", "Saldo pendiente_str"]].copy()
                df_disp.rename(columns={
                    "Pagos a realizar_str": "Pagado a Realizar", 
                    "Pagado a proveedores_str": "Pagado a proveedores", 
                    "Saldo pendiente_str": "Saldo pendiente"
                }, inplace=True)
                st.dataframe(df_disp.style.apply(lambda x: pd.DataFrame(f'background-color: {bg_color}', index=x.index, columns=x.columns), axis=None), use_container_width=True, hide_index=True)

if is_editor:
    # 5. GESTIÓN DE PROVEEDORES
    st.header("⚙️ Gestión de Proveedores", divider="gray")
    with st.expander(" Panel de Configuración de Proveedores", expanded=st.session_state.config_panel_open):
        st.write("Registra proveedores y ajusta sus porcentajes por cliente.")
        if "provs_temp" not in st.session_state:
            st.session_state.provs_temp = st.session_state.proveedores_df.to_dict('records')
        
        h1, h2, h3 = st.columns([4, 2, 1])
        h1.markdown("**Nombre del Proveedor**")
        h2.markdown("**Estado**")
        for i, p in enumerate(st.session_state.provs_temp):
            c1, c2, c3 = st.columns([4, 2, 1])
            with c1: p["Nombre"] = st.text_input("Nombre", value=p["Nombre"], key=f"n_{i}", label_visibility="collapsed")
            with c2: p["Visible"] = st.checkbox("Activo", value=bool(p["Visible"]), key=f"v_{i}")
            with c3:
                if st.button("🗑", key=f"del_{i}"):
                    st.session_state.provs_temp.pop(i)
                    st.session_state.config_panel_open = True
                    st.rerun()
        if st.button("➕ Nuevo Proveedor"):
            nuevo_p = {"Nombre": "", "Visible": True}
            for c in CUENTAS: nuevo_p[c] = 0.0
            st.session_state.provs_temp.append(nuevo_p)
            st.session_state.config_panel_open = True
            st.rerun()
        st.divider()
        st.markdown("### 🔧 Ajustes por Cuenta")
        prov_activos = [p for p in st.session_state.provs_temp if p["Visible"] and p["Nombre"].strip() != ""]
        for c_idx, c_name in enumerate(CUENTAS):
            suma_actual = sum([float(p.get(c_name, 0.0)) for p in prov_activos])
            estado = "✅ Suma 100%" if abs(suma_actual - 100.0) <= 0.01 else f"⚠️ Suma {suma_actual}%"
            with st.popover(f"👤 {c_name} — {estado}", use_container_width=False):
                if not prov_activos: st.warning("No hay proveedores activos.")
                else:
                    for p_idx, p in enumerate(st.session_state.provs_temp):
                        if p["Visible"] and p["Nombre"].strip() != "":
                            r1, r2 = st.columns([3, 2])
                            with r1: is_sel = st.checkbox(p["Nombre"], value=(float(p.get(c_name, 0.0)) > 0), key=f"chk_{c_idx}_{p_idx}")
                            with r2: 
                                if is_sel: p[c_name] = st.number_input("%", value=float(p.get(c_name, 0.0)), step=1.0, min_value=0.0, max_value=100.0, key=f"val_{c_idx}_{p_idx}", label_visibility="collapsed")
                                else: p[c_name] = 0.0
        if st.button("💾 Guardar Configuración Final", type="primary", use_container_width=False):
            df_prov_val = pd.DataFrame(st.session_state.provs_temp)
            if any(abs(df_prov_val[df_prov_val["Visible"] == True][c].sum() - 100.0) > 0.01 for c in CUENTAS):
                st.error("Todas las cuentas deben sumar 100%.")
                st.session_state.config_panel_open = True
            else:
                with st.spinner("Guardando en la base de datos..."):
                    if guardar_config_db(df_prov_val):
                        st.session_state.proveedores_df = df_prov_val
                        st.session_state.pop("provs_temp", None)
                        st.session_state.config_panel_open = False
                        st.toast("✅ Configuración guardada con éxito")
                        st.success("✅ Configuración guardada exitosamente.")
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar en Google Sheets. Intenta de nuevo.")
                        st.session_state.config_panel_open = True



