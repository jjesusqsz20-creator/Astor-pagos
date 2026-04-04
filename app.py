import streamlit as st
import streamlit.components.v1 as components
import gspread
import json
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import re
import requests
import extra_streamlit_components as stx

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
        background-color: #F8FAFC !important;
        color: #1E3A8A !important;
        border: 1.5px solid #CBD5E1 !important; /* Borde más pronunciado */
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* Efecto Hover y Focus para inputs */
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* v3.7 - Ajuste de legibilidad: Tamaño intermedio óptimo */
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary p * {
        font-family: 'Roboto Mono', 'Courier New', monospace !important;
        font-size: 0.92rem !important; 
        font-weight: 800 !important;
        color: #000000 !important;
        background-color: transparent !important;
        line-height: inherit !important;
        display: inline !important;
        white-space: pre !important;
    }
    
    /* Ocultar cualquier residuo de texto interno del sistema */
    [data-testid="stExpander"] summary span[aria-hidden="true"] {
        display: none !important;
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
    /* --- ESTILOS EXCLUSIVOS PARA LOS HISTORIALES (VERDE PASTEL Y CENTRADO) --- */
    /* --- CENTRADO DINÁMICO PARA HISTORIALES (Basado en IDs únicos) --- */
    /* Target del contenedor del expansor que sigue al marcador ID */
    div:has(> .element-container #historial-abonos) + div [data-testid="stExpander"],
    div:has(> .element-container #historial-retornos) + div [data-testid="stExpander"] {
        width: 100% !important;
    }

    div:has(> .element-container #historial-abonos) + div [data-testid="stExpanderHeader"],
    div:has(> .element-container #historial-retornos) + div [data-testid="stExpanderHeader"] {
        justify-content: center !important;
        background-color: #F8FAFC !important;
        border-radius: 10px !important;
    }

    div:has(> .element-container #historial-abonos) + div [data-testid="stExpanderHeader"] p,
    div:has(> .element-container #historial-retornos) + div [data-testid="stExpanderHeader"] p {
        text-align: center !important;
        width: 100% !important;
        display: block !important;
        color: #364350 !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        font-family: inherit !important; /* Salir del modo monospace para centrar */
    }

    [data-testid="stTable"] th, [data-testid="stTable"] td {
        text-align: center !important;
        padding: 0.8rem 0.8rem !important; /* Reducción del 25% aproximadamente */
        vertical-align: middle !important;
        font-size: 0.98rem !important;
        color: #1F2937 !important;
    }

    /* Aumento de tamaño GLOBAL para etiquetas de campos (Inputs y Selects) */
    [data-testid="stNumberInput"] label p,
    [data-testid="stSelectbox"] label p {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        color: #1E3A8A !important;
    }
    /* Monospace for Tablero para alinear barras verticales */
    .stExpander details summary p {
        letter-spacing: -0.01rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- ESTILOS DE TABLAS HTML PERSONALIZADAS ---
def generar_tabla_html(df, headers=None, bg_header="#f3f4f6", text_color="#1f2937"):
    """Genera una tabla HTML premium con contenido centrado y diseño moderno."""
    if df.empty: return "<p style='text-align:center;'>No hay datos disponibles.</p>"
    
    cols = headers if headers else df.columns
    html = f"""
    <div style="overflow-x:auto; border-radius:12px; border: 1px solid #e5e7eb; margin: 10px 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <table style="width:100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.95rem;">
            <thead>
                <tr style="background-color: {bg_header}; border-bottom: 2px solid #e5e7eb;">
                    {"".join([f'<th style="padding: 12px 15px; text-align: center; color: #4b5563; font-weight: 700; text-transform: uppercase; font-size: 0.75rem;">{c}</th>' for c in cols])}
                </tr>
            </thead>
            <tbody>
    """
    for _, row in df.iterrows():
        html += '<tr style="border-bottom: 1px solid #f3f4f6; transition: background-color 0.2s; cursor: default;" onmouseover="this.style.backgroundColor=\'#f9fafb\'" onmouseout="this.style.backgroundColor=\'transparent\'">'
        for col in df.columns:
            val = row[col]
            html += f'<td style="padding: 12px 15px; text-align: center; color: {text_color};">{val}</td>'
        html += '</tr>'
    
    html += """
            </tbody>
        </table>
    </div>
    """
    return html

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
                # El rol debe ser lo que diga la BD, o "Administrador" si está vacío/no existe
                "rol": (r.get("Rol") or r.get("rol") or r.get("ROL") or "Administrador").strip()
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

# --- WHATSAPP NOTIFICACIONES ---
def formatear_telefono(tel):
    """Limpia y asegura el formato E.164 (52 + 10 dígitos) para México"""
    tel_limpio = "".join(filter(str.isdigit, str(tel)))
    if len(tel_limpio) == 10:
        return "52" + tel_limpio
    return tel_limpio

def enviar_notificacion_whatsapp(ticket, monto, accion="registro"):
    """
    Envía notificaciones a los editores según la lógica:
    - Factura -> Notifica a todos los Editores.
    - Editor X -> Notifica al otro Editor.
    """
    if "usuario_logueado" not in st.session_state or not st.session_state.usuario_logueado:
        return

    user_actual = st.session_state.usuario_logueado
    rol_actual = user_actual.get("rol", "Administrador")
    email_actual = user_actual.get("email", "").lower().strip()
    nombre_actual = user_actual.get("nombre", "Usuario")

    # Obtener todos los administradores
    todos_usuarios = obtener_usuarios_db(client)
    editores = [u for u in todos_usuarios if u.get("rol") == "Administrador"]

    # Filtrar destinatarios
    destinatarios = []
    if rol_actual == "Colaborador":
        destinatarios = editores
    else:
        # Es un Administrador, notificar a los otros administradores
        destinatarios = [u for u in editores if u.get("email", "").lower().strip() != email_actual]

    if not destinatarios:
        return

    # Credenciales de Meta (desde secretos)
    try:
        token = st.secrets["whatsapp"]["token"]
        phone_id = st.secrets["whatsapp"]["phone_id"]
        template = st.secrets["whatsapp"]["template_name"]
    except:
        # Fail silently if config is missing to avoid stopping the app
        return

    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for dest in destinatarios:
        tel = formatear_telefono(dest.get("tel", ""))
        if not tel: continue

        payload = {
            "messaging_product": "whatsapp",
            "to": tel,
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": dest.get("nombre", "Administrador")}, # {{1}}
                            {"type": "text", "text": str(ticket)},                 # {{2}}
                            {"type": "text", "text": f"{float(monto):,.2f}"},       # {{3}}
                            {"type": "text", "text": nombre_actual}                # {{4}}
                        ]
                    }
                ]
            }
        }
        try:
            requests.post(url, headers=headers, json=payload, timeout=5)
        except:
            pass

# --- CONFIGURACIÓN DE ESTADO ---
# --- GESTIÓN DE COOKIES (SESIÓN) ---
# Inicializar el componente de cookies al nivel más alto posible
cookie_manager = stx.CookieManager(key="inside_cookie_manager_v2")

if "usuario_logueado" not in st.session_state:
    st.session_state.usuario_logueado = None
if "manual_logout" not in st.session_state:
    st.session_state.manual_logout = False

# Sincronización de Autologin (Reintentos para evitar cierre de sesión en refresh)
if "cookie_retries" not in st.session_state:
    st.session_state.cookie_retries = 0

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

    # 6. Hoja de Configuración de Ingresos
    if "Config_Ingresos" in hojas_nombres:
        sheet_config_ingresos = spreadsheet.worksheet("Config_Ingresos")
    else:
        sheet_config_ingresos = spreadsheet.add_worksheet(title="Config_Ingresos", rows="100", cols="3")
        sheet_config_ingresos.append_row(["Mes", "Año", "Ingreso"])

    return {
        "spreadsheet": spreadsheet,
        "config": sheet_config,
        "config_ingresos": sheet_config_ingresos,
        "retorno": sheet_retorno,
        "retorno_manual": sheet_retorno_manual,
        "abonos": sheet_abonos,
        "audit": sheet_audit
    }

try:
    client = init_connection()
    db_sheets = get_db_sheets(client)
    # Referencias globales para conveniencia (aunque los datos se obtengan via funciones)
    spreadsheet = db_sheets["spreadsheet"]
    sheet_config = db_sheets["config"]
    sheet_config_ingresos = db_sheets["config_ingresos"]
    sheet_retorno = db_sheets["retorno"]
    sheet_retorno_manual = db_sheets["retorno_manual"]
    sheet_audit = db_sheets["audit"]
    sheet = db_sheets["abonos"]

    # --- MURO DE AUTENTICACIÓN ---
    usuarios_db = obtener_usuarios_db(client)
    
    # Lógica de Autologin con Cookie (Sincronización agresiva V3)
    # Solo intentar si el usuario no ha forzado un Logout manual en esta sesión
    if st.session_state.usuario_logueado is None and not st.session_state.manual_logout:
        # Forzar sincronización de cookies
        try:
            cookies = cookie_manager.get_all()
            if cookies and 'inside_session_email' in cookies:
                email_c = str(cookies['inside_session_email']).lower().strip()
                usuario_encontrado = next((u for u in usuarios_db if str(u["email"]).lower().strip() == email_c), None)
                if usuario_encontrado:
                    st.session_state.usuario_logueado = usuario_encontrado
                    st.session_state.cookie_retries = 0
                    st.rerun()
            
            # Si no hay cookies, reintentar hasta 5 veces para dar tiempo al navegador
            if st.session_state.cookie_retries < 5:
                st.session_state.cookie_retries += 1
                st.rerun()
        except:
            # Fallback a reintento si get_all falla
            if st.session_state.cookie_retries < 5:
                st.session_state.cookie_retries += 1
                st.rerun()

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
                            st.session_state.manual_logout = False # Resetear bandera al loguearse
                            # Guardar cookie por 30 días para persistencia agresiva
                            expires = datetime.now() + timedelta(days=30)
                            cookie_manager.set('inside_session_email', email_log.lower().strip(), expires_at=expires)
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
                
                editores_actuales = [u for u in usuarios_db if u.get("rol") == "Administrador"]
                facturas_actuales = [u for u in usuarios_db if u.get("rol") == "Colaborador"]
                
                can_add_editor = len(editores_actuales) < 2
                can_add_factura = len(facturas_actuales) < 1
                
                if not can_add_editor and not can_add_factura:
                    st.error("🚫 Límite global de usuarios alcanzado (Máximo 2 Administradores y 1 Colaborador).")
                    if st.button("⬅️ Volver", use_container_width=True):
                        st.session_state.vista_auth = "login"; st.rerun()
                else:
                    roles_disponibles = []
                    if can_add_editor: roles_disponibles.append("Administrador")
                    if can_add_factura: roles_disponibles.append("Colaborador")
                    
                    st.info(f"💡 Disponibilidad: {len(editores_actuales)}/2 Administradores, {len(facturas_actuales)}/1 Colaborador.")
                    
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
@st.cache_data(ttl=60)
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

@st.cache_data(ttl=60)
def obtener_todos_ingresos_periodo():
    try:
        data = sheet_config_ingresos.get_all_records()
        return pd.DataFrame(data)
    except: return pd.DataFrame(columns=["Mes", "Año", "Ingreso"])

def obtener_ingreso_periodo(mes, anio):
    df = obtener_todos_ingresos_periodo()
    if df.empty: return 2200000.0
    res = df[(df["Mes"] == mes) & (df["Año"].astype(str) == str(anio))]
    if not res.empty:
        return float(res.iloc[0]["Ingreso"])
    return 2200000.0

def guardar_ingreso_periodo(mes, anio, monto):
    try:
        df = obtener_todos_ingresos_periodo()
        idx = df[(df["Mes"] == mes) & (df["Año"].astype(str) == str(anio))].index
        if not idx.empty:
            row_idx = idx[0] + 2 # +2 por encabezado y 1-based
            sheet_config_ingresos.update(f"C{row_idx}", [[monto]])
        else:
            sheet_config_ingresos.append_row([mes, str(anio), monto])
        obtener_todos_ingresos_periodo.clear()
        return True
    except: return False

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

@st.cache_data(ttl=60)
def obtener_datos_retorno():
    """Descarga los datos de retornos desde la hoja 'Retorno'"""
    # Admitir tanto el nombre de la hoja como el estandarizado
    df = obtener_datos_resiliente(sheet_retorno, ["Ticket", "Fecha", "Nombre", "Banco", "Proveedor", "Monto Total", "Diferencia", "Retorno a Pagar", "Registrado por", "Ref_Abono"])
    
    # Estandarizar nombre de columna a singular para toda la app
    if "Retorno a Pagar" in df.columns:
        df.rename(columns={"Retorno a Pagar": "Retorno por pagar"}, inplace=True)
    
    # Asegurar que la columna existe y el cálculo es correcto
    if "Retorno por pagar" not in df.columns:
        df["Retorno por pagar"] = df["Monto Total"] - df["Diferencia"]
    
    # Recalcular si el valor es 0 pero hay montos (evita el error de visualización $0.00)
    def corregir_neto(row):
        monto = float(row.get("Monto Total", 0))
        dif = float(row.get("Diferencia", 0))
        neto = float(row.get("Retorno por pagar", 0))
        if neto == 0 and monto > 0:
            return monto - dif
        return neto
        
    df["Retorno por pagar"] = df.apply(corregir_neto, axis=1)
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

@st.cache_data(ttl=60)
def obtener_datos_retorno_manual():
    """Descarga los datos de retornos manuales desde la hoja 'Retorno_Manual'"""
    # Usar 'Monto Total' para consistencia con el rename_map y otras hojas
    return obtener_datos_resiliente(sheet_retorno_manual, ["Ticket", "Fecha", "Nombre", "Banco", "Proveedor", "Monto Total", "Registrado por"])

def registrar_retorno_manual(monto):
    """Guarda un nuevo registro de retorno manual en Google Sheets con serie 30000"""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_cache = obtener_datos_retorno_manual()
        num_filas = len(df_cache) + 1
        nuevo_ticket = 30000 + num_filas
        nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
        # Usamos nombre_usuario en la columna 'Nombre' para indicar quién registró el retorno (ahora global)
        sheet_retorno_manual.append_row([nuevo_ticket, fecha_actual, nombre_usuario, "---", "---", monto, nombre_usuario])
        obtener_datos_retorno_manual.clear()
        enviar_notificacion_whatsapp(nuevo_ticket, monto)
        return True
    except Exception:
        return False

def actualizar_retorno_manual(ticket_id, monto):
    """Actualiza un retorno manual (solo monto) y registra en auditoría"""
    try:
        df = obtener_datos_retorno_manual()
        idx = df[df["Ticket"].astype(str) == str(ticket_id)].index
        if idx.empty: return False
        
        orig = df.loc[idx[0]]
        row_idx = idx[0] + 2
        
        cambios_ant = []; cambios_new = []
        # Solo permitimos editar el monto en el nuevo flujo simplificado
        if float(orig['Monto Total']) != float(monto): 
            cambios_ant.append(f"Mto: ${float(orig['Monto Total']):,.2f}"); cambios_new.append(f"Mto: ${float(monto):,.2f}")
            
        if not cambios_ant: return True
        
        det_ant = " | ".join(cambios_ant); det_new = " | ".join(cambios_new)
        nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
        
        # Mantener Banco y Proveedor como "---" si se edita un registro nuevo, o respetar los antiguos si se edita uno viejo
        nuevo_nombre = orig['Nombre']
        nuevo_banco = orig['Banco']
        nuevo_prov = orig['Proveedor']
        
        sheet_retorno_manual.update(f"C{row_idx}:G{row_idx}", [[nuevo_nombre, nuevo_banco, nuevo_prov, monto, nombre_usuario]])
        registrar_auditoria("---", ticket_id, "Edición Retorno Manual", det_ant, det_new)
        enviar_notificacion_whatsapp(ticket_id, monto, accion="edición")
        
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
    enviar_notificacion_whatsapp(nuevo_ticket, monto)
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
        enviar_notificacion_whatsapp(ticket_id, nuevo_monto, accion="edición")
        
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

is_editor = st.session_state.usuario_logueado.get('rol') == 'Administrador'
is_factura = st.session_state.usuario_logueado.get('rol') == 'Colaborador'

if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.usuario_logueado = None
    st.session_state.vista_auth = "login"
    st.session_state.manual_logout = True # Bloquear autologin hasta login manual
    st.session_state.cookie_wait_done = False # Resetear espera de sincronización
    cookie_manager.delete('inside_session_email')
    st.rerun()

if st.sidebar.button("🔄 Refrescar Datos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()





# --- INTERFAZ GRAFICA (UI) ---

# Inicialización de estados de inputs para etiquetas dinámicas y persistencia
if "sel_mes" not in st.session_state:
    st.session_state.sel_mes = MESES_MAP[datetime.now().month]
if "sel_anio" not in st.session_state:
    st.session_state.sel_anio = datetime.now().year

# Inicializar los valores de los widgets (usando sus 'key')
if "ing_input" not in st.session_state:
    st.session_state.ing_input = obtener_ingreso_periodo(st.session_state.sel_mes, st.session_state.sel_anio)

if "pago_input" not in st.session_state:
    st.session_state.pago_input = 50000.0

if "ret_input_monto" not in st.session_state:
    st.session_state.ret_input_monto = 50000.0

# Sincronización para etiquetas (labels)
st.session_state.ingreso_mensual = st.session_state.ing_input
st.session_state.monto_pago_val = st.session_state.pago_input
st.session_state.monto_retorno_val = st.session_state.ret_input_monto

# Asegurar que el monto del pago sea válido para el min_value de 0.01
if st.session_state.pago_input < 0.01:
    st.session_state.pago_input = 50000.0
    st.session_state.monto_pago_val = 50000.0

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
t_ret_auto_bruto = suma_valida(df_gl_retorno, "Retorno por pagar")
dif_ret = suma_valida(df_gl_retorno, "Diferencia")
t_manual = pd.to_numeric(df_gl_manual["Monto Total"], errors='coerce').fillna(0).sum()
# 'Retorno por pagar' neto es la suma automática menos lo entregado manualmente (global)
t_ret_neto = t_ret_auto_bruto - t_manual
adeudo = t_ret_neto

st.write("<br>", unsafe_allow_html=True)
# --- DASHBOARD LAYOUT (Centered Rows) ---
col_r1_1, col_r1_2, col_r1_3 = st.columns(3)

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

# Fila 1: 3 cuadros (Solo Administradores)
if is_editor:
    col_r1_1, col_r1_2, col_r1_3 = st.columns(3)
    render_metric_card(col_r1_1, "Pago total a proveedor", t_abonado, "#3b82f6") # Azul
    render_metric_card(col_r1_2, "Retorno por pagar", t_ret_neto, "#f59e0b") # Naranja
    render_metric_card(col_r1_3, "Diferencia Inside", dif_ret, "#ef4444") # Rojo

# Fila 2: 2 cuadros centrados
st.write("<br>", unsafe_allow_html=True)
col_r2_space1, col_r2_1, col_r2_2, col_r2_space2 = st.columns([1, 2, 2, 1])
render_metric_card(col_r2_1, "Retorno entregado", t_manual, "#10b981") # Verde
render_metric_card(col_r2_2, f"{semaforo_m} Diferencia Proveedor", adeudo, color_adeudo) # Dinámico
st.write("<br>", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def obtener_auditoria():
    cols = ["Fecha", "Usuario", "Ticket_Abono", "Ticket_Retorno", "Accion", "Dato_Anterior", "Dato_Nuevo"]
    try:
        data = sheet_audit.get_all_records()
        if not data: return pd.DataFrame(columns=cols)
        return pd.DataFrame(data)
    except: return pd.DataFrame(columns=cols)

if is_editor:
    # 1. PRONÓSTICO DE INGRESO
    with st.container(border=True):
        # Franjita azul claro (estilo métricas)
        st.markdown('<div style="background-color: #60A5FA; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
        st.markdown("<h5 style='margin-top: -0.5rem; margin-bottom: 1rem; color: #364350; font-weight: 800;'>📈 Pronóstico de Ingreso</h5>", unsafe_allow_html=True)
        
        col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
        
        def reload_ingreso():
            st.session_state.ingreso_mensual = obtener_ingreso_periodo(st.session_state.sel_mes, st.session_state.sel_anio)

        with col_p2:
            meses_lista = list(MESES_MAP.values())
            st.selectbox("Mes", meses_lista, key="sel_mes", on_change=reload_ingreso)
        with col_p3:
            st.number_input("Año", min_value=2020, max_value=2100, key="sel_anio", on_change=reload_ingreso)

        with col_p1:
            def update_ingreso_persistente():
                monto_nuevo = st.session_state.ing_input
                st.session_state.ingreso_mensual = monto_nuevo
                guardar_ingreso_periodo(st.session_state.sel_mes, st.session_state.sel_anio, monto_nuevo)
            
            st.number_input(f"💸 Ingreso Mensual (${st.session_state.ingreso_mensual:,.2f} MXN)", 
                            step=1000.0, key="ing_input", on_change=update_ingreso_persistente)
            nuevo_ingreso = st.session_state.ingreso_mensual
    
    # 2. REGISTRO DE PAGO A PROVEEDOR
    with st.container(border=True):
        # Franjita verde
        st.markdown('<div style="background-color: #10b981; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
        st.markdown("<h5 style='margin-top: -0.5rem; color: #364350; font-weight: 800;'>📝 Registro de pago a proveedor</h5>", unsafe_allow_html=True)
        st.write("<small>Selecciona la cuenta, el proveedor al que se le paga y el monto del pago realizado.</small>", unsafe_allow_html=True)
        
        st.write("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1.2])
        
        with c1:
            cuenta_seleccionada = st.selectbox("Nombre / Cuenta Bancaria", CUENTAS)
        with c2:
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

        with c3:
            def update_pago():
                st.session_state.monto_pago_val = st.session_state.pago_input
            
            st.number_input(f"💰 Monto del Pago (${st.session_state.pago_input:,.2f} MXN)", 
                            min_value=0.01, step=100.0, 
                            key="pago_input", on_change=update_pago)
            monto_ingresado = st.session_state.monto_pago_val
        
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

        # --- HISTORIAL DE PAGO A PROVEEDOR (DESPLEGABLE) ---
        st.markdown('<div id="historial-abonos"></div>', unsafe_allow_html=True)
        with st.expander("🕒 Ver historial de pago a proveedor", expanded=False):
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
                with st.form("form_filtros_abonos"):
                    f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns(6)
                    
                    with f_col1:
                        lista_users = ["Todos"] + sorted(registros_recientes["Registrado por"].dropna().astype(str).unique().tolist())
                        sel_user = st.selectbox("Usuario", lista_users, key="f_user_abono")
                    with f_col2:
                        f_tk = st.text_input("Ticket", key="f_tk_abono", placeholder="Buscar...")
                    with f_col3:
                        f_fecha = st.date_input("Fecha", value=None, key="f_fecha_abono")
                    with f_col4:
                        lista_cuentas = ["Todas"] + sorted(registros_recientes['Nombre_Filtro'].dropna().unique().tolist())
                        sel_cuenta = st.selectbox("Titular", lista_cuentas, key="f_cta_abono")
                    with f_col5:
                        lista_bancos = ["Todos"] + sorted([b for b in registros_recientes['Banco_Filtro'].dropna().unique().tolist() if b])
                        sel_banco = st.selectbox("Banco", lista_bancos, key="f_bco_abono")
                    with f_col6:
                        lista_provs = ["Todos"] + sorted(registros_recientes['Proveedor'].dropna().unique().tolist())
                        sel_prov = st.selectbox("Proveedor", lista_provs, key="f_prov_abono")
                    
                    st.form_submit_button("🔍 Buscar en Historial", use_container_width=True)

                # Aplicar filtrado basado en los widgets del formulario
                df_filtrado = registros_recientes.copy()
                if sel_user != "Todos": df_filtrado = df_filtrado[df_filtrado["Registrado por"] == sel_user]
                if f_tk: df_filtrado = df_filtrado[df_filtrado['Ticket'].astype(str).str.contains(f_tk, case=False)]
                if f_fecha: df_filtrado = df_filtrado[df_filtrado['Fecha_DT'].dt.date == f_fecha]
                if sel_cuenta != "Todas": df_filtrado = df_filtrado[df_filtrado['Nombre_Filtro'] == sel_cuenta]
                if sel_banco != "Todos": df_filtrado = df_filtrado[df_filtrado['Banco_Filtro'] == sel_banco]
                if sel_prov != "Todos": df_filtrado = df_filtrado[df_filtrado['Proveedor'] == sel_prov]
                        
                st.divider()
                # Pesos de columna sincronizados para cabecera y filas
                COL_PESOS = [0.6, 0.9, 1.8, 1.2, 0.9, 1.4]
                
                c_tk, c_f, c_c, c_p, c_m, c_u = st.columns(COL_PESOS)
                c_tk.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Ticket</b></p>", unsafe_allow_html=True)
                c_f.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Fecha</b></p>", unsafe_allow_html=True)
                c_c.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Cuenta</b></p>", unsafe_allow_html=True)
                c_p.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Proveedor</b></p>", unsafe_allow_html=True)
                c_m.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Monto</b></p>", unsafe_allow_html=True)
                c_u.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Usuario</b></p>", unsafe_allow_html=True)
                st.divider()
                
                if df_filtrado.empty: st.info("No se encontraron registros.")
                else:
                    for idx, row in df_filtrado.iterrows():
                        t_id = str(row.get('Ticket', '---'))
                        # Contenedor con borde para cada ticket
                        with st.container(border=True):
                            c_tk, c_f, c_c, c_p, c_m, c_u = st.columns(COL_PESOS)
                            c_tk.markdown(f"<p style='text-align: center; margin: 0; display: block;'>🎫 <b>{t_id}</b></p>", unsafe_allow_html=True)
                            c_f.markdown(f"<p style='text-align: center; margin: 0; display: block;'>📅 {row['Fecha'].split(' ')[0]}</p>", unsafe_allow_html=True)
                            c_c.markdown(f"<p style='text-align: center; margin: 0; display: block;'>🏦 {row['Cuenta']}</p>", unsafe_allow_html=True)
                            c_p.markdown(f"<p style='text-align: center; margin: 0; display: block;'>👤 {row.get('Proveedor', '---')}</p>", unsafe_allow_html=True)
                            c_m.markdown(f"<p style='text-align: center; margin: 0; display: block;'>💰 <b>${float(row.get('Monto Total', 0)):,.0f}</b></p>", unsafe_allow_html=True)
                            c_u.markdown(f"<p style='text-align: center; margin: 0; display: block;'>👨‍💻 {row.get('Registrado por', '---')}</p>", unsafe_allow_html=True)
                            
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

# 3. RETORNO ENTREGADO


if is_editor or is_factura:
    # 3. RETORNO ENTREGADO (GLOBAL)
    with st.container(border=True):
        # Franjita naranja
        st.markdown('<div style="background-color: #f59e0b; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
        st.markdown("<h5 style='margin-top: -0.5rem; color: #364350; font-weight: 800;'>🔄 Retorno entregado</h5>", unsafe_allow_html=True)
        st.write("<small>Registra el monto total de retorno entregado al proveedor de forma global.</small>", unsafe_allow_html=True)
        
        st.write("<br>", unsafe_allow_html=True)
        # Solo columna para el monto
        def update_retorno():
            st.session_state.monto_retorno_val = st.session_state.ret_input_monto
            
        monto_r = st.number_input(f"🔄 Monto del Retorno Entregado Global (${st.session_state.ret_input_monto:,.2f} MXN)", 
                                  min_value=0.0, step=100.0, 
                                  key="ret_input_monto", on_change=update_retorno)
        
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Guardar Registro de Retorno", type="primary", use_container_width=True, key="ret_btn_manual"):
            if monto_r <= 0:
                st.warning("El monto debe ser mayor a 0.")
            else:
                with st.spinner("Guardando Retorno Global..."):
                    if registrar_retorno_manual(float(monto_r)):
                        st.success(f"✅ ¡Retorno global de ${monto_r:,.2f} MXN registrado exitosamente!")
                        st.session_state.monto_retorno_val = 50000.0 # Reset
                        st.rerun()
                    else:
                        st.error("❌ Ocurrió un error al guardar el retorno global.")
        
        # --- HISTORIAL DE RETORNO (DESPLEGABLE) ---
        st.markdown('<div id="historial-retornos"></div>', unsafe_allow_html=True)
        with st.expander("🕒 Ver historial de retorno entregado", expanded=False):
            df_h_m = obtener_datos_retorno_manual()
            if df_h_m.empty:
                st.info("Aún no se han registrado retornos manuales.")
            else:
                m_recientes = df_h_m.sort_values(by="Fecha", ascending=False).copy()
                m_recientes['Fecha_DT'] = pd.to_datetime(m_recientes['Fecha'], errors='coerce')
                m_recientes['Mes_Filtro'] = m_recientes['Fecha_DT'].dt.month.map(MESES_MAP)
                
                st.markdown("##### 🔍 Filtros de Búsqueda")
                with st.form("form_filtros_retornos"):
                    fm_col1, fm_col2, fm_col3 = st.columns(3)
                    
                    with fm_col1:
                        lista_users_m = ["Todos"] + sorted(m_recientes["Registrado por"].dropna().astype(str).unique().tolist())
                        sel_user_m = st.selectbox("Usuario", lista_users_m, key="f_user_m")
                    with fm_col2:
                        f_tk_m = st.text_input("Ticket", key="f_tk_m", placeholder="Buscar...")
                    with fm_col3:
                        f_fecha_m = st.date_input("Fecha", value=None, key="f_fecha_m")
                    
                    st.form_submit_button("🔍 Buscar en Historial", use_container_width=True)

                # Aplicar filtrado basado en los widgets del formulario
                df_m_filtrado = m_recientes.copy()
                if sel_user_m != "Todos": df_m_filtrado = df_m_filtrado[df_m_filtrado["Registrado por"] == sel_user_m]
                if f_tk_m: df_m_filtrado = df_m_filtrado[df_m_filtrado['Ticket'].astype(str).str.contains(f_tk_m, case=False)]
                if f_fecha_m: df_m_filtrado = df_m_filtrado[df_m_filtrado['Fecha_DT'].dt.date == f_fecha_m]
                        
                st.divider()
                # Pesos de columna sincronizados para cabecera y filas
                CM_PESOS = [0.6, 0.9, 2.2, 1.0, 0.8]
                
                cm_tk, cm_f, cm_p, cm_m, cm_e = st.columns(CM_PESOS)
                cm_tk.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Ticket</b></p>", unsafe_allow_html=True)
                cm_f.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Fecha</b></p>", unsafe_allow_html=True)
                cm_p.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Registrado por</b></p>", unsafe_allow_html=True)
                cm_m.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Monto</b></p>", unsafe_allow_html=True)
                cm_e.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Acción</b></p>", unsafe_allow_html=True)
                st.divider()
                
                if df_m_filtrado.empty: st.info("No se encontraron registros.")
                else:
                    for idx, row in df_m_filtrado.iterrows():
                        tm_id = str(row.get('Ticket', '---'))
                        with st.container(border=True):
                            c_tk, c_f, c_p, c_m, c_e = st.columns(CM_PESOS)
                            c_tk.markdown(f"<p style='text-align: center; margin: 0; display: block;'>🎫 <b>{tm_id}</b></p>", unsafe_allow_html=True)
                            c_f.markdown(f"<p style='text-align: center; margin: 0; display: block;'>📅 {str(row['Fecha']).split(' ')[0]}</p>", unsafe_allow_html=True)
                            c_p.markdown(f"<p style='text-align: center; margin: 0; display: block;'>👤 {row['Nombre']}</p>", unsafe_allow_html=True)
                            c_m.markdown(f"<p style='text-align: center; margin: 0; display: block;'>💰 ${pd.to_numeric(row.get('Monto Total', 0), errors='coerce'):,.0f}</p>", unsafe_allow_html=True)
                            
                            with c_e:
                                with st.popover("✏️ Editar", use_container_width=True):
                                    st.markdown("##### ✏️ Editar Retorno Manual")
                                    st.info(f"Ticket: {tm_id}")
                                    
                                    nuevo_mto = st.number_input("Nuevo Monto", value=float(pd.to_numeric(row.get('Monto Total', 0), errors='coerce')), key=f"edit_mto_m_{tm_id}")
                                    
                                    if st.button("💾 Guardar Cambios", key=f"btn_edit_m_{tm_id}", type="primary", use_container_width=True):
                                        with st.spinner("Actualizando..."):
                                            if actualizar_retorno_manual(tm_id, nuevo_mto):
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
        with st.container(border=True):
            # Franjita índigo para el tablero
            st.markdown('<div style="background-color: #6366f1; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top: -0.5rem; color: #312e81; font-weight: 800;'>📊 Tablero de Control - Pagos por realizar</h4>", unsafe_allow_html=True)
            
            # --- TABLA RESUMEN DE RETORNOS ---
            df_h_ret_dash = obtener_datos_retorno()
            df_h_manual_dash = obtener_datos_retorno_manual()
            
            if not df_h_ret_dash.empty:
                resumen_ret_dash = []
                sum_pago_prov = 0; sum_dif_inside = 0; sum_ret_pagar_bruto = 0
                
                for c in CUENTAS:
                    nombre_c = c.split(" (")[0] if " (" in c else c
                    banco_c = c.split(" (")[1].replace(")", "") if " (" in c else ""
                    
                    df_c = df_h_ret_dash[(df_h_ret_dash["Nombre"] == nombre_c) & (df_h_ret_dash["Banco"] == banco_c)]
                    total_monto_prov = pd.to_numeric(df_c["Monto Total"], errors='coerce').fillna(0).sum()
                    total_dif_inside = pd.to_numeric(df_c["Diferencia"], errors='coerce').fillna(0).sum()
                    retorno_auto_bruto = total_monto_prov - total_dif_inside
                    
                    sum_pago_prov += total_monto_prov
                    sum_dif_inside += total_dif_inside
                    sum_ret_pagar_bruto += retorno_auto_bruto
                    
                    sem_ret = "🟢" if retorno_auto_bruto <= 0 else "🔴"
                    resumen_ret_dash.append({
                        "Nombre": nombre_c,
                        "Cuenta": banco_c,
                        "Pago Total a Proveedor": f"${total_monto_prov:,.2f}",
                        "Diferencia Inside": f"${total_dif_inside:,.2f}",
                        "Retorno por pagar": f"{sem_ret} ${retorno_auto_bruto:,.2f}"
                    })
                
                df_ret_final_dash = pd.DataFrame(resumen_ret_dash)
                st.markdown("##### 🔄 Resumen de Retornos por Cuenta")
                # st.dataframe(df_ret_final_dash.style.set_properties(**{'text-align': 'center'}), use_container_width=True, hide_index=True)
                st.markdown(generar_tabla_html(df_ret_final_dash, bg_header="#e0e7ff"), unsafe_allow_html=True)
                st.divider()
            else:
                st.info("No hay registros de retorno aún para procesar.")
            
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
                logo_banco = "👤" # Emoji unificado para todos los usuarios/cuentas por solicitud
                pct_str = f"({(total_abono/total_pago)*100:.0f}%)" if total_pago > 0 else "(0%)"
                estado_saldo = "🟢" if total_saldo <= 0 else ("🟡" if total_abono > 0 else "🔴")
                
                # He aumentado el padding a 60 y uso espacio normal para monospace.
                # Monospace + white-space: pre + font-size: 0.8rem = Alineación perfecta en una línea
                def pad_mono(text, length):
                    return str(text).ljust(length)
        
                nombre_raw = f"{logo_banco} {c}"
                nombre_col = pad_mono(nombre_raw, 48) # Ajuste final de ancho
                m_ing = f"Ing:${ingreso:,.0f}"
                m_pag = f"PAGO:${total_abono:,.0f}"
                m_sal = f"Sal:{estado_saldo}${total_saldo:,.0f}"
                
                # Refresco forzado de cadena: Nombre | Ing | PAGO | Sal
                titulo_expander = f"{nombre_col} | {m_ing} | {m_pag} | {m_sal}"
                
                with st.expander(titulo_expander, expanded=False):
                    df_disp = df_cuenta[["Proveedor", "Porcentaje", "Pagos a realizar_str", "Pagado a proveedores_str", "Saldo pendiente_str"]].copy()
                    df_disp.rename(columns={
                        "Pagos a realizar_str": "Pago a Realizar", 
                        "Pagado a proveedores_str": "Pagado a proveedores", 
                        "Saldo pendiente_str": "Saldo pendiente"
                    }, inplace=True)
                    st.markdown(generar_tabla_html(df_disp, bg_header=bg_color), unsafe_allow_html=True)

if is_editor:
    # 5. GESTIÓN DE PROVEEDORES
    with st.container(border=True):
        # Franjita rosa para gestión
        st.markdown('<div style="background-color: #e11d48; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: -0.5rem; color: #881337; font-weight: 800;'>⚙️ Gestión de Proveedores</h4>", unsafe_allow_html=True)
        
        with st.expander("Panel de Configuración de Proveedores"):
            if "provs_temp" not in st.session_state:
                st.session_state.provs_temp = st.session_state.proveedores_df.to_dict('records')
            
            # Estado para manejar la confirmación de eliminación y adición
            if "confirm_delete_idx" not in st.session_state:
                st.session_state.confirm_delete_idx = None
            if "confirm_add_prov" not in st.session_state:
                st.session_state.confirm_add_prov = False
            
            nombres_prov_actuales = sorted(list(set([p["Nombre"] for p in st.session_state.provs_temp if p["Nombre"].strip() != ""])))

            # Callbacks para "Seleccionar Todo"
            # Callbacks para Sincronización de Checkboxes (Cuentas y Proveedores)
            # --- DIÁLOGO PARA AÑADIR PROVEEDOR ---
            @st.dialog("➕ Añadir Nuevo Proveedor")
            def dialog_añadir_prov():
                st.write("Ingresa el nombre del nuevo proveedor que deseas registrar en la base de datos.")
                nuevo_n = st.text_input("Nombre del Proveedor", key="in_dialog_new_prov")
                
                if st.button("Registrar Proveedor", type="primary", use_container_width=True):
                    nombre_clean = nuevo_n.strip()
                    if not nombre_clean:
                        st.error("❌ El nombre no puede estar vacío.")
                    elif nombre_clean in nombres_prov_actuales:
                        st.error("❌ Este proveedor ya existe.")
                    else:
                        nuevo_p = {"Nombre": nombre_clean, "Visible": True}
                        for c in CUENTAS: nuevo_p[c] = 0.0
                        st.session_state.provs_temp.append(nuevo_p)
                        
                        df_prov_val = pd.DataFrame(st.session_state.provs_temp)
                        if guardar_config_db(df_prov_val):
                            st.session_state.proveedores_df = df_prov_val
                            st.toast(f"✅ {nombre_clean} registrado con éxito")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar en la base de datos.")

            # --- FILA DE SELECCIÓN ESTABLE (MULTISELECT NATAL) ---
            col_cfg_1, col_cfg_2 = st.columns(2)
            
            with col_cfg_1:
                st.markdown("**Cuentas a configurar**")
                # Inicializar selección de cuentas si no existe
                if "sel_cuentas_cfg" not in st.session_state:
                    st.session_state.sel_cuentas_cfg = []
                
                cuentas_seleccionadas = st.multiselect(
                    "Seleccionar Cuentas",
                    options=CUENTAS,
                    default=st.session_state.sel_cuentas_cfg,
                    key="ms_cuentas_cfg",
                    label_visibility="collapsed"
                )
                st.session_state.sel_cuentas_cfg = cuentas_seleccionadas
            
            with col_cfg_2:
                st.markdown("**Proveedores participantes**")
                nombres_v = [p["Nombre"] for p in st.session_state.provs_temp if str(p["Nombre"]).strip() != ""]
                
                # Inicializar selección de proveedores si no existe
                if "sel_provs_cfg" not in st.session_state:
                    st.session_state.sel_provs_cfg = []
                
                # Filtrar selección anterior por si se borraron proveedores
                st.session_state.sel_provs_cfg = [p for p in st.session_state.sel_provs_cfg if p in nombres_v]
                
                provs_seleccionados = st.multiselect(
                    "Seleccionar Proveedores",
                    options=nombres_v,
                    default=st.session_state.sel_provs_cfg,
                    key="ms_provs_cfg",
                    label_visibility="collapsed"
                )
                st.session_state.sel_provs_cfg = provs_seleccionados
            
            # --- ACCIONES DE GESTIÓN (BORRAR Y AÑADIR) ---
            st.markdown("<br>", unsafe_allow_html=True)
            m_col1, m_col2 = st.columns([2, 1])
            with m_col2:
                if st.button("➕ Añadir Nuevo Proveedor", use_container_width=True, type="secondary"):
                    dialog_añadir_prov()
            
            # Lógica de Borrado (Permanente en el expander para no cerrar menús)
            if provs_seleccionados:
                with st.expander("🗑️ Zona de Eliminación", expanded=False):
                    st.write("Selecciona un proveedor de los actuales para eliminarlo permanentemente.")
                    for p_sel_name in provs_seleccionados:
                        ecol1, ecol2 = st.columns([4, 1])
                        with ecol1: st.write(f"**{p_sel_name}**")
                        with ecol2:
                            if st.button("Eliminar", key=f"del_stable_{p_sel_name}", type="primary", use_container_width=True):
                                # Buscar índice en la lista maestra
                                idx = next((i for i, p in enumerate(st.session_state.provs_temp) if p["Nombre"] == p_sel_name), None)
                                if idx is not None:
                                    st.session_state.confirm_delete_idx = idx
                                    st.rerun()

            if st.session_state.confirm_delete_idx is not None:
                idx = st.session_state.confirm_delete_idx
                p_name_del = st.session_state.provs_temp[idx]["Nombre"]
                with st.container(border=True):
                    st.warning(f"¿Confirmas que deseas borrar a **{p_name_del}** de la base de datos?", icon="⚠️")
                    bcol1, bcol2 = st.columns(2)
                    with bcol1:
                        if st.button("❌ Cancelar", use_container_width=True):
                            st.session_state.confirm_delete_idx = None
                            st.rerun()
                    with bcol2:
                        if st.button("✅ Confirmar Borrado", type="primary", use_container_width=True):
                            st.session_state.provs_temp.pop(idx)
                            df_prov_val = pd.DataFrame(st.session_state.provs_temp)
                            if guardar_config_db(df_prov_val):
                                st.session_state.proveedores_df = df_prov_val
                                st.session_state.confirm_delete_idx = None
                                # Limpiar de la selección si estaba
                                if p_name_del in st.session_state.sel_provs_cfg:
                                    st.session_state.sel_provs_cfg.remove(p_name_del)
                                st.toast(f"🗑️ {p_name_del} eliminado")
                                st.rerun()
                
                if provs_seleccionados:
                    st.caption(f"✅ {len(provs_seleccionados)} proveedor(es) seleccionado(s)")
            
            st.divider()

            # --- SECCIÓN DE PORCENTAJES (DINÁMICA) ---
            if not cuentas_seleccionadas or not provs_seleccionados:
                st.info("💡 Selecciona cuentas y proveedores arriba para ajustar los repartos.")
            else:
                # Sincronización: Poner a 0% los no seleccionados
                for p_env in st.session_state.provs_temp:
                    if p_env["Nombre"] not in provs_seleccionados:
                        for c_sel in cuentas_seleccionadas:
                            p_env[c_sel] = 0.0

                st.write("**Configuración de Porcentajes** (Suma obligatoria: 100%)")
                
                valid_global = True
                for c_name in cuentas_seleccionadas:
                    with st.container(border=True):
                        # Encabezado de cuenta con Icono
                        st.markdown(f"🏦 **Distribución para {c_name}**")
                        
                        # Suma actual de esta cuenta
                        suma_cta = sum(float(p.get(c_name, 0.0)) for p in st.session_state.provs_temp if p["Nombre"] in provs_seleccionados)
                        
                        # Barra de progreso visual
                        progreso = min(suma_cta / 100.0, 1.0)
                        if abs(suma_cta - 100.0) <= 0.01:
                            st.progress(progreso, text=f"✅ Cuenta completa: {suma_cta}%")
                        else:
                            st.progress(progreso, text=f"⚠️ Distribución incompleta: {suma_cta}% (Falta {100 - suma_cta:.1f}%)" if suma_cta < 100 else f"🚨 Exceso: {suma_cta}% (Sobra {suma_cta - 100:.1f}%)")
                            valid_global = False

                        # Grid de inputs (máximo 4 por fila para limpieza)
                        cols_prov = st.columns(4)
                        for idx_p, p_name in enumerate(provs_seleccionados):
                            with cols_prov[idx_p % 4]:
                                p_obj = next((item for item in st.session_state.provs_temp if item["Nombre"] == p_name), None)
                                if p_obj:
                                    # Input numérico con etiqueta compacta
                                    val_act = float(p_obj.get(c_name, 0.0))
                                    p_obj[c_name] = st.number_input(f"% {p_name}", 
                                                                    value=val_act, step=1.0, 
                                                                    min_value=0.0, max_value=100.0, 
                                                                    key=f"pct_{c_name}_{p_name}")
                
                st.divider()
                # Botón de guardado con lógica de validación mejorada
                if st.button("💾 Guardar Cambios en Base de Datos", type="primary", use_container_width=True):
                    if not valid_global:
                        st.error("❌ **Error de Validación:** Todas las cuentas seleccionadas deben sumar exactamente **100%** para poder guardar. Por favor, revisa las barras rojas arriba.")
                    else:
                        df_prov_val = pd.DataFrame(st.session_state.provs_temp)
                        with st.spinner("Sincronizando con base de datos de Google Sheets..."):
                            if guardar_config_db(df_prov_val):
                                st.session_state.proveedores_df = df_prov_val
                                st.session_state.pop("provs_temp", None)
                                st.session_state.config_panel_open = False
                                st.toast("✅ Configuración guardada con éxito")
                                st.rerun()
                            else:
                                st.error("❌ Error de conexión al intentar guardar en la base de datos.")



