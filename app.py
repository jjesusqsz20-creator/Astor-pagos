import streamlit as st
import streamlit.components.v1 as components
import gspread
import json
import time
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

    /* Tamaño optimizado para etiquetas para evitar saltos de línea */
    [data-testid="stNumberInput"] label p,
    [data-testid="stSelectbox"] label p {
        font-size: 1.08rem !important;
        font-weight: 800 !important;
        color: #1E3A8A !important;
    }
    /* Monospace for Tablero para alinear barras verticales */
    .stExpander details summary p {
        letter-spacing: -0.01rem !important;
    }

    /* Estilo para los botones de popover (Ticket IDs) en los historiales para que parezcan badges */
    div[data-testid="stExpander"] div[data-testid="stPopover"] > button {
        background-color: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        color: #1E3A8A !important;
        font-weight: 900 !important;
        border-radius: 8px !important;
        padding: 4px 6px !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
        justify-content: center !important; 
        white-space: nowrap !important; /* No permitir salto de línea */
        min-width: 0px !important;
        overflow: hidden !important;
    }
    div[data-testid="stExpander"] div[data-testid="stPopover"] > button:hover {
        background-color: #FFFFFF !important;
        border-color: #3B82F6 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stExpander"] div[data-testid="stPopover"] > button:active {
        transform: translateY(0px) !important;
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

# --- TELEGRAM NOTIFICACIONES ---
def enviar_notificacion_telegram(ticket, monto, accion="registro", detalle=""):
    """
    Envía notificaciones por Telegram a los Administradores según la lógica:
    - Colaborador → Notifica a TODOS los Administradores.
    - Administrador X → Notifica solo al OTRO Administrador (no a sí mismo).

    Configuración en .streamlit/secrets.toml:
      [telegram]
      token = "BOT_TOKEN_AQUI"

      [telegram.chat_ids]
      "admin1@correo.com" = "123456789"
      "admin2@correo.com" = "987654321"
    """
    if "usuario_logueado" not in st.session_state or not st.session_state.usuario_logueado:
        return

    user_actual = st.session_state.usuario_logueado
    rol_actual = user_actual.get("rol", "Administrador")
    email_actual = user_actual.get("email", "").lower().strip()
    nombre_actual = user_actual.get("nombre", "Usuario")

    # Obtener todos los usuarios con rol Administrador
    todos_usuarios = obtener_usuarios_db(client)
    todos_admins = [u for u in todos_usuarios if u.get("rol") == "Administrador"]

    # Lógica de destinatarios:
    # Ahora enviamos a TODOS los administradores siempre, 
    # incluyendo al que realiza la acción para que tenga su confirmación.
    destinatarios = todos_admins

    # 4. Leer token y configuraciones de Telegram
    try:
        token = st.secrets["telegram"]["token"]
        chat_ids_config = dict(st.secrets["telegram"].get("chat_ids", {}))
        silent_observers = dict(st.secrets["telegram"].get("silent_observers", {}))
    except Exception as e:
        print(f"[TELEGRAM] ERROR cargando secrets: {e}")
        return

    # 5. Consolidar lista final de Chat IDs a notificar
    chat_ids_finales = set()
    
    # Agregar IDs de administradores según la lógica de destinatarios
    for dest in destinatarios:
        email_dest = dest.get("email", "").lower().strip()
        cid = chat_ids_config.get(email_dest)
        if cid: chat_ids_finales.add(str(cid))
    
    # Agregar SIEMPRE los observadores silenciosos
    for _, obs_cid in silent_observers.items():
        chat_ids_finales.add(str(obs_cid))

    if not chat_ids_finales:
        return

    # 6. Construir y enviar el mensaje
    icono_accion = {
        "registro": "🆕", "registro de retorno": "📥", "registro de abono": "🆕",
        "edición": "✏️", "edición de retorno": "✏️",
        "eliminación de abono": "🗑️", "eliminación de retorno": "🗑️",
    }.get(accion, "🔔")

    monto_fmt = f"${float(monto):,.2f}" if float(monto) > 0 else "—"
    fecha_fmt = datetime.now().strftime("%d/%m/%Y %H:%M")

    mensaje = (
        f"🏢 *Inside — Rol de Pagos*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{icono_accion} *Acción:* {accion.capitalize()}\n"
        f"🎫 *Ticket:* `#{ticket}`\n"
        f"💰 *Monto:* {monto_fmt}\n"
        f"👤 *Realizado por:* {nombre_actual}\n"
    )
    if detalle:
        mensaje += f"📝 *Detalle:* {detalle}\n"
    mensaje += f"━━━━━━━━━━━━━━━\n📅 {fecha_fmt}"

    url_base = f"https://api.telegram.org/bot{token}/sendMessage"

    for cid in chat_ids_finales:
        try:
            requests.post(url_base, json={
                "chat_id": cid,
                "text": mensaje,
                "parse_mode": "Markdown"
            }, timeout=5)
        except Exception:
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

    # 6. Hoja de Configuración de Ingresos (V2 - Nueva estructura limpia con Fecha)
    if "Config_Ingresos_V2" in hojas_nombres:
        sheet_config_ingresos = spreadsheet.worksheet("Config_Ingresos_V2")
    else:
        sheet_config_ingresos = spreadsheet.add_worksheet(title="Config_Ingresos_V2", rows="100", cols="4")
        sheet_config_ingresos.append_row(["Mes", "Año", "Ingreso", "Fecha_Registro"])

    # 7. Hoja de Historial de Tablero de Control
    headers_hist = ["Mes", "Año", "Ingreso_Total", "Total_Pagado", "Retorno_Pagar", "Comision_Inside", "Retorno_Pagado", "Dif_Proveedor", "Tabla_Resumen", "Tabla_Detalle", "Fecha_Snapshot", "Usuario"]
    if "Tablero_Historial" in hojas_nombres:
        sheet_historial_tablero = spreadsheet.worksheet("Tablero_Historial")
        # Forzar actualización de encabezados si están incompletos (V3)
        try:
            first_row = sheet_historial_tablero.row_values(1)
            if len(first_row) < len(headers_hist):
                sheet_historial_tablero.update("A1:L1", [headers_hist])
        except: pass
    else:
        sheet_historial_tablero = spreadsheet.add_worksheet(title="Tablero_Historial", rows="100", cols="13")
        sheet_historial_tablero.append_row(headers_hist)

    return {
        "spreadsheet": spreadsheet,
        "config": sheet_config,
        "config_ingresos": sheet_config_ingresos,
        "retorno": sheet_retorno,
        "retorno_manual": sheet_retorno_manual,
        "abonos": sheet_abonos,
        "audit": sheet_audit,
        "historial_tablero": sheet_historial_tablero
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
    sheet_historial_tablero = db_sheets["historial_tablero"]
except Exception as e:
    st.error("❌ Error de Conexión: No se pudo conectar a Google Sheets.")
    st.error(f"Detalle: {e}")
    st.info("Asegúrate de haber compartido el archivo con el correo de servicio técnico y que el nombre sea 'Astor_Pagos_DB'.")
    st.stop()

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
            time.sleep(0.3) # Pequeña espera para sincronización en la nube
            st.rerun()
    except:
        # Fallback a reintento si get_all falla
        if st.session_state.cookie_retries < 5:
            st.session_state.cookie_retries += 1
            time.sleep(0.3)
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
                    # Guardar cookie por 7 días
                    expires = datetime.now() + timedelta(days=7)
                    cookie_manager.set('inside_session_email', email_log.lower().strip(), expires_at=expires)
                    st.success(f"✅ ¡Bienvenido, {valido['nombre']}!")
                    time.sleep(0.5) # Tiempo para que el navegador grabe la cookie
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

def obtener_historial_tablero():
    try:
        data = sheet_historial_tablero.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except: return pd.DataFrame()

def guardar_snapshot_tablero(mes, anio, ingreso, pagado, retorno, comision, ret_manual, dif_prov, tabla_json, detalle_json):
    fecha_cap = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
    try:
        sheet_historial_tablero.append_row([mes, anio, ingreso, pagado, retorno, comision, ret_manual, dif_prov, tabla_json, detalle_json, fecha_cap, usuario])
        return True
    except: return False

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
        return True
    except Exception as e:
        return False

@st.cache_data(ttl=600)
def obtener_todos_ingresos_periodo():
    try:
        # Leer como valores crudos para evitar errores de encabezados con caracteres especiales
        data = sheet_config_ingresos.get_all_values()
        if not data or len(data) < 2:
            return pd.DataFrame(columns=["Mes", "Año", "Ingreso", "Fecha_Registro"])
        
        # El primer renglón son encabezados, el resto datos
        headers = data[0]
        rows = data[1:]
        return pd.DataFrame(rows, columns=headers)
    except: return pd.DataFrame(columns=["Mes", "Año", "Ingreso"])

def obtener_ingreso_periodo(mes, anio):
    obtener_todos_ingresos_periodo.clear()
    df = obtener_todos_ingresos_periodo()
    if df.empty: return 0.0
    
    try:
        # Búsqueda simple para evitar errores de pandas
        m_target = str(mes).strip().lower()
        a_target = str(anio).strip()
        
        # Leemos de abajo hacia arriba (lo más nuevo primero)
        for i in range(len(df) - 1, -1, -1):
            row = df.iloc[i]
            m_row = str(row.iloc[0]).strip().lower()
            a_row = str(row.iloc[1]).strip()
            if m_row == m_target and a_row == a_target:
                raw_val = str(row.iloc[2]).replace("$","").replace(",","").replace(" ","").strip()
                return float(raw_val) if raw_val else 0.0
    except Exception as e:
        print(f"Error búsqueda simple: {e}")
        
    return 0.0

def guardar_ingreso_periodo(mes, anio, monto):
    try:
        # Intento de re-conexión proactiva si algo falla
        if 'sheet_config_ingresos' not in globals() or sheet_config_ingresos is None:
            db = get_db_sheets(client)
            globals()['sheet_config_ingresos'] = db["config_ingresos"]
            
        fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet_config_ingresos.append_row([str(mes), str(anio), float(monto), fecha_registro])
        obtener_todos_ingresos_periodo.clear()
        st.session_state.error_tecnico = None
        return True
    except Exception as e:
        print(f"Error crítico al guardar ingreso: {e}")
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

            # 6. Capturar columna Estado (si existe en el row o headers)
            if "Estado" in headers:
                idx_st = headers.index("Estado")
                row_dict["Estado"] = r[idx_st] if idx_st < n else "Activo"
            else:
                row_dict["Estado"] = "Activo"

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
                    elif col == "Estado":
                        df[col] = "Activo"
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
    df = obtener_datos_resiliente(sheet_retorno, ["Ticket", "Fecha", "Nombre", "Banco", "Proveedor", "Monto Total", "Diferencia", "Retorno a Pagar", "Registrado por", "Ref_Abono", "Estado"])
    
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
        # Calcular Ticket (Serie 30000) de forma eficiente usando el cache
        df_cache = obtener_datos_retorno()
        num_filas = len(df_cache) + 1 # +1 por el encabezado
        nuevo_ticket = 30000 + num_filas
        nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
        sheet_retorno.append_row([nuevo_ticket, fecha_actual, nombre, banco, proveedor, monto_total, diferencia, retorno_neto, nombre_usuario, ref_abono, "Activo"])
        obtener_datos_retorno.clear()
        # Notificar a administradores del nuevo retorno registrado
        enviar_notificacion_telegram(nuevo_ticket, monto_total, accion="registro de retorno")
        return True
    except Exception:
        return False

@st.cache_data(ttl=60)
def obtener_datos_retorno_manual():
    """Descarga los datos de retornos manuales desde la hoja 'Retorno_Manual'"""
    # Usar 'Monto Total' para consistencia con el rename_map y otras hojas
    return obtener_datos_resiliente(sheet_retorno_manual, ["Ticket", "Fecha", "Nombre", "Banco", "Proveedor", "Monto Total", "Registrado por", "Estado"])

def registrar_retorno_manual(monto):
    """Guarda un nuevo registro de retorno manual en Google Sheets con serie 20000"""
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        df_cache = obtener_datos_retorno_manual()
        num_filas = len(df_cache) + 1
        nuevo_ticket = 20000 + num_filas
        nombre_usuario = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Sistema"
        # Usamos nombre_usuario en la columna 'Nombre' para indicar quién registró el retorno (ahora global)
        sheet_retorno_manual.append_row([nuevo_ticket, fecha_actual, nombre_usuario, "---", "---", monto, nombre_usuario, "Activo"])
        obtener_datos_retorno_manual.clear()
        enviar_notificacion_telegram(nuevo_ticket, monto)
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
        
        # Actualizar la fila en Sheets (Columna 6 es Monto Total en Retorno_Manual)
        sheet_retorno_manual.update_cell(row_idx, 6, monto)
        
        # Registrar en Auditoria
        fecha_act = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet_audit.append_row([fecha_act, nombre_usuario, "---", ticket_id, "Edición Retorno", det_ant, det_new])
        obtener_datos_retorno_manual.clear()
        
        # Notificar a administradores sobre la edición
        enviar_notificacion_telegram(ticket_id, monto, accion="edición de retorno", detalle=f"{det_ant} → {det_new}")
        return True
    except:
        return False

# --- FUNCIONES DE INACTIVACIÓN (Soft Delete) ---

def inactivar_pago(ticket_id, usuario_nombre):
    """Marca un abono como Inactivo y devuelve (éxito, mensaje)"""
    try:
        data = sheet.get_all_values()
        if not data: return False, "La hoja está vacía."
        
        headers = data[0]
        header_map = {h.lower().strip(): i for i, h in enumerate(headers)}
        
        idx_t = -1
        for variant in ["ticket", "tiket", "id"]:
            if variant in header_map:
                idx_t = header_map[variant]
                break
        
        if idx_t == -1:
            return False, f"Columna 'Ticket' no encontrada. Encabezados detectados: {headers}"
            
        idx_status = -1
        for variant in ["estado", "estatus", "status", "true/false"]:
            if variant in header_map:
                idx_status = header_map[variant]
                break
        
        if idx_status == -1:
            sheet.update_cell(1, len(headers) + 1, "Estado")
            idx_status = len(headers)
        
        row_found = -1
        for i, row in enumerate(data[1:], 2):
            if len(row) > idx_t and str(row[idx_t]).strip() == str(ticket_id).strip():
                row_found = i; break
        
        if row_found == -1:
            return False, f"Ticket #{ticket_id} no encontrado en la hoja."
            
        sheet.update_cell(row_found, idx_status + 1, "Inactivo")
        
        fecha_act = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet_audit.append_row([fecha_act, usuario_nombre, ticket_id, "---", "Inactivación", "Activo", "Inactivo"])
        
        enviar_notificacion_telegram(ticket_id, 0, accion="eliminación de abono", detalle=f"Ticket #{ticket_id}")
        return True, "OK"
    except Exception as e:
        return False, f"Error técnico: {str(e)}"

def inactivar_retorno_manual(ticket_id, usuario_nombre):
    """Marca un retorno manual como Inactivo y devuelve (éxito, mensaje)"""
    try:
        data = sheet_retorno_manual.get_all_values()
        if not data: return False, "La hoja está vacía."
        
        headers = [h.strip() for h in data[0]]
        
        # Estandarizar búsqueda de encabezados
        header_map = {h.lower().strip(): i for i, h in enumerate(headers)}
        
        # Buscar índice de Ticket (flexible)
        idx_t = -1
        for variant in ["ticket", "tiket", "id"]:
            if variant in header_map:
                idx_t = header_map[variant]
                break
        
        if idx_t == -1: return False, f"Columna 'Ticket' no encontrada en Retorno Manual."
            
        # Buscar índice de Estado (flexible)
        idx_status = -1
        for variant in ["estado", "estatus", "status", "true/false"]:
            if variant in header_map:
                idx_status = header_map[variant]
                break
        
        if idx_status == -1:
            sheet_retorno_manual.update_cell(1, len(headers) + 1, "Estado")
            idx_status = len(headers)
        
        row_found = -1
        for i, row in enumerate(data[1:], 2):
            if len(row) > idx_t and str(row[idx_t]).strip() == str(ticket_id).strip():
                row_found = i; break
        
        if row_found == -1: return False, f"Ticket #{ticket_id} no encontrado."
            
        sheet_retorno_manual.update_cell(row_found, idx_status + 1, "Inactivo")
        
        fecha_act = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet_audit.append_row([fecha_act, usuario_nombre, "---", ticket_id, "Inactivación", "Activo", "Inactivo"])
        obtener_datos_retorno_manual.clear()
        
        # Notificar a administradores sobre la eliminación
        enviar_notificacion_telegram(ticket_id, 0, accion="eliminación de retorno", detalle=f"Ticket #{ticket_id}")
        return True, "OK"
    except Exception as e:
        return False, f"Error técnico en retorno manual: {str(e)}"



# Inicializar variables de configuración en sesión desde la Base de Datos
if "ingreso_mensual" not in st.session_state or "proveedores_df" not in st.session_state:
    config_data = obtener_config_db()
    ingreso_val = 0.0 # Eliminamos los 2.2M definitivamente
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
    # Garantizar que el DataFrame tenga columnas incluso si está vacío
    if prov_list:
        st.session_state.proveedores_df = pd.DataFrame(prov_list)
    else:
        st.session_state.proveedores_df = pd.DataFrame(columns=["Nombre", "Visible"] + CUENTAS)

@st.cache_data(ttl=600)  # Mantiene los datos en memoria para cargar la página al instante
def obtener_datos():
    """Descarga los datos actuales desde Google Sheets"""
    expected = ["Ticket", "Fecha", "Cuenta", "Proveedor", "Monto Total", "Registrado por", "Estado"]
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
    sheet.append_row([nuevo_ticket, fecha_actual, cuenta, proveedor, monto, nombre_usuario, "Activo"])
    obtener_datos.clear()  # Forzar refresco de datos
    enviar_notificacion_telegram(nuevo_ticket, monto)
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
        enviar_notificacion_telegram(ticket_id, nuevo_monto, accion="edición")
        
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
    st.session_state.manual_logout = True
    cookie_manager.delete('inside_session_email')
    time.sleep(0.5)
    st.rerun()

if st.sidebar.button("🔄 Refrescar Datos", use_container_width=True):
    st.cache_data.clear()
    # Borrar variables de sesión para forzar re-lectura total
    for key in ["ingreso_mensual", "ing_input", "pago_input", "ret_input_monto"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- INTERFAZ GRAFICA (UI) ---
if "sel_mes" not in st.session_state:
    st.session_state.sel_mes = MESES_MAP[datetime.now().month]
if "sel_anio" not in st.session_state:
    st.session_state.sel_anio = datetime.now().year

if "ing_input" not in st.session_state:
    val_db = obtener_ingreso_periodo(st.session_state.sel_mes, st.session_state.sel_anio)
    st.session_state.ingreso_mensual = val_db
    st.session_state.ing_input = val_db

if "pago_input" not in st.session_state:
    st.session_state.pago_input = 50000.0
if "monto_pago_val" not in st.session_state:
    st.session_state.monto_pago_val = 50000.0
if "ret_input_monto" not in st.session_state:
    st.session_state.ret_input_monto = 50000.0
if "monto_retorno_val" not in st.session_state:
    st.session_state.monto_retorno_val = 50000.0

# Inicialización de la selección de cuentas (Gestión de Proveedores)
if "master_ctas" not in st.session_state:
    st.session_state["master_ctas"] = False
for c in CUENTAS:
    key_cta = f"p_cta_cb_fin_{c}"
    if key_cta not in st.session_state:
        st.session_state[key_cta] = False

st.title("💸 Inside - Gestión de Rol de Pagos")

# Función para filtrar cualquier DataFrame por Mes y Año (Periodo)
def filtrar_por_periodo(df, mes_nombre, anio):
    if df.empty or "Fecha" not in df.columns: return df
    try:
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'], errors='coerce')
        mes_num = [k for k, v in MESES_MAP.items() if v == mes_nombre][0]
        return df[(df['Fecha_DT'].dt.month == mes_num) & (df['Fecha_DT'].dt.year == anio)].copy()
    except:
        return df

if is_editor or is_factura:
    m_sel = st.session_state.get('sel_mes', MESES_MAP[datetime.now().month])
    a_sel = st.session_state.get('sel_anio', datetime.now().year)
    
    df_gl_abono = filtrar_por_periodo(obtener_datos(), m_sel, a_sel)
    df_gl_retorno = filtrar_por_periodo(obtener_datos_retorno(), m_sel, a_sel)
    df_gl_manual = filtrar_por_periodo(obtener_datos_retorno_manual(), m_sel, a_sel)
else:
    df_gl_abono = pd.DataFrame()
    df_gl_retorno = pd.DataFrame()
    df_gl_manual = pd.DataFrame()

# Función para sumar solo montos que NO parecen tickets (fuera del rango 10,000-21,000)
def suma_valida(df, col):
    if df.empty or col not in df.columns: return 0.0
    vals = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return vals.sum()

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
    render_metric_card(col_r1_1, "Total pagado", t_abonado, "#3b82f6") # Azul
    render_metric_card(col_r1_2, "Retorno por pagar", max(0, t_ret_neto), "#f59e0b") # Naranja
    render_metric_card(col_r1_3, "Diferencia Inside (Comisión)", dif_ret, "#ef4444") # Rojo

# Fila 2: 2 cuadros centrados
st.write("<br>", unsafe_allow_html=True)
col_r2_space1, col_r2_1, col_r2_2, col_r2_space2 = st.columns([1, 2, 2, 1])
render_metric_card(col_r2_1, "Retorno pagado", t_manual, "#10b981") # Verde
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
        st.markdown("<h4 style='margin-top: -0.5rem; margin-bottom: 1.5rem; color: #1e3a8a; font-weight: 800;'>📈 Pronóstico de Ingreso</h4>", unsafe_allow_html=True)
        
        col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
        
        def reload_ingreso():
            m = st.session_state.get('sel_mes', MESES_MAP[datetime.now().month])
            a = st.session_state.get('sel_anio', datetime.now().year)
            valor_guardado = obtener_ingreso_periodo(m, a)
            st.session_state.ingreso_mensual = valor_guardado
            st.session_state.ing_input = valor_guardado

        with col_p2:
            meses_lista = list(MESES_MAP.values())
            st.selectbox("Mes", meses_lista, key="sel_mes", on_change=reload_ingreso)
        with col_p3:
            st.number_input("Año", min_value=2020, max_value=2100, key="sel_anio", on_change=reload_ingreso)

        with col_p1:
            # Usamos el valor actual de la memoria (para el paréntesis)
            val_p = st.session_state.get('ingreso_mensual', 0.0)
            st.number_input(f"💸 Ingreso Mensual (${val_p:,.2f} MXN)", 
                            step=1000.0, key="ing_input")
        
        # Botón a lo largo (fuera de las columnas)
        st.write("<br>", unsafe_allow_html=True)
        if st.button("💾 Guardar pronóstico de ingreso", type="primary", use_container_width=True):
            monto_final = st.session_state.ing_input
            if guardar_ingreso_periodo(st.session_state.sel_mes, st.session_state.sel_anio, monto_final):
                # En lugar de forzar el valor, borramos la memoria para que el bloque de arriba lo cargue fresco
                if "ingreso_mensual" in st.session_state: del st.session_state.ingreso_mensual
                if "ing_input" in st.session_state: del st.session_state.ing_input
                st.success(f"✅ ¡Pronóstico de ${monto_final:,.2f} guardado con éxito!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Error al guardar en la base de datos.")
    
    st.divider()

    # 2. REGISTRO DE PAGO A PROVEEDOR
    with st.container(border=True):
        # Franjita verde
        st.markdown('<div style="background-color: #10b981; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: -0.5rem; color: #065f46; font-weight: 800;'>📝 Registro de pago a proveedor</h4>", unsafe_allow_html=True)
        st.write("<small>Selecciona la cuenta, el proveedor al que se le paga y el monto del pago realizado.</small>", unsafe_allow_html=True)
        
        st.write("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.7, 0.7, 1.3])
        
        with c1:
            cuenta_seleccionada = st.selectbox("Nombre / Cuenta Bancaria", CUENTAS)
        with c2:
            prov_df = st.session_state.proveedores_df
            # Identificar columna del porcentaje para la cuenta seleccionada
            col_pct = cuenta_seleccionada
            
            # Filtro: Mostrar solo proveedores visibles Y que tengan porcentaje > 0 en esta cuenta
            # Añadimos protección contra DataFrame vacío
            if prov_df.empty:
                prov_validos = pd.DataFrame(columns=["Nombre", "Visible"] + CUENTAS)
                lista_prov_form = []
            else:
                try:
                    prov_validos = prov_df[(prov_df["Visible"] == True) & (prov_df[col_pct] > 0)]
                    lista_prov_form = prov_validos["Nombre"].unique().tolist()
                except KeyError:
                    prov_validos = pd.DataFrame(columns=["Nombre", "Visible"] + CUENTAS)
                    lista_prov_form = []
            
            if not lista_prov_form:
                st.warning(f"⚠️ No hay proveedores configurados para {cuenta_seleccionada}.")
                proveedor_seleccionado = None
            else:
                proveedor_seleccionado = st.selectbox("Proveedor Destino", lista_prov_form, key=f"abono_prov_{cuenta_seleccionada}")
                pct_actual = prov_validos[prov_validos["Nombre"] == proveedor_seleccionado][col_pct].iloc[0]

        with c3:
            def update_pago():
                st.session_state.monto_pago_val = st.session_state.get('pago_input', 50000.0)

            if st.session_state.get("reset_pago_input", False):
                if "pago_input" in st.session_state:
                    del st.session_state["pago_input"]
                st.session_state.reset_pago_input = False
            
            # Asegurar que el widget tenga el valor correcto antes de renderizar (evita reset a 0.01)
            if "pago_input" not in st.session_state:
                st.session_state["pago_input"] = st.session_state.get("monto_pago_val", 50000.0)
            
            # Usar etiqueta estática para el widget y mostrar el valor dinámico aparte (evita recreación del widget)
            st.markdown(f"""
                <p style="font-size: 1.08rem !important; font-weight: 900 !important; color: #1E3A8A !important; margin-bottom: 8px; margin-top: 0px;">
                    <b>💰 Monto Pago (${st.session_state.get('pago_input', 50000.0):,.2f} MXN)</b>
                </p>
            """, unsafe_allow_html=True)
            monto_ingresado = st.number_input("Monto del Pago", 
                            min_value=0.01, step=100.0, 
                            key="pago_input", on_change=update_pago,
                            label_visibility="collapsed")
        
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
                        # Usar una bandera para el refresco fuera del try
                        exito_guardado = False
                        try:
                            id_abono = registrar_pago(cuenta_seleccionada, proveedor_seleccionado, float(monto_ingresado))
                            nombre_tit = cuenta_seleccionada.split(" (")[0] if " (" in cuenta_seleccionada else cuenta_seleccionada
                            banco_tit = cuenta_seleccionada.split(" (")[1].replace(")", "") if " (" in cuenta_seleccionada else ""
                            dif_calculada = float(monto_ingresado) * 0.04
                            neto_retorno = float(monto_ingresado) - dif_calculada
                            registrar_retorno(nombre_tit, banco_tit, proveedor_seleccionado, float(monto_ingresado), float(dif_calculada), float(neto_retorno), ref_abono=id_abono)
                            exito_guardado = True
                        except Exception as e:
                            st.error(f"❌ Error al guardar en base de datos: {e}")
                        
                        if exito_guardado:
                            st.success(f"✅ ¡Pago y Retorno de ${monto_ingresado:,.2f} MXN registrados!")
                            st.session_state.reset_pago_input = True
                            st.session_state.monto_pago_val = 50000.0
                            st.rerun()

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
                COL_PESOS = [1.0, 1.0, 1.6, 1.1, 0.9, 1.2]
                
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
                        es_inactivo = row.get('Estado') == 'Inactivo'
                        
                        # Contenedor con borde para cada ticket
                        with st.container(border=True):
                            if es_inactivo:
                                st.markdown("""
                                    <style>
                                        div[data-testid="stVerticalBlock"] > div:has(div.stExpander) {
                                            opacity: 0.6;
                                            filter: grayscale(100%);
                                        }
                                    </style>
                                """, unsafe_allow_html=True)
                            
                            c_tk, c_f, c_c, c_p, c_m, c_u = st.columns(COL_PESOS)
                            with c_tk:
                                with st.popover(f"🎫 {t_id}", use_container_width=True):
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
                                    
                                    st.divider()
                                    if not es_inactivo:
                                        if st.button("🗑️", key=f"btn_inact_{t_id}", use_container_width=True, type="secondary"):
                                            with st.spinner("Inactivando..."):
                                                nombre_u = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Usuario"
                                                exito, msj = inactivar_pago(t_id, nombre_u)
                                                if exito:
                                                    st.success("✅ Registro inactivado correctamente.")
                                                    obtener_datos.clear()
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error(f"❌ {msj}")
                                    else:
                                        st.warning("⚠️ Este registro ya se encuentra INACTIVO.")

                            c_f.markdown(f"<p style='text-align: center; margin: 0; display: block;'>📅 {row['Fecha'].split(' ')[0]}</p>", unsafe_allow_html=True)
                            c_c.markdown(f"<p style='text-align: center; margin: 0; display: block;'>🏦 {row['Cuenta']}</p>", unsafe_allow_html=True)
                            c_p.markdown(f"<p style='text-align: center; margin: 0; display: block;'>👤 {row.get('Proveedor', '---')}</p>", unsafe_allow_html=True)
                            c_m.markdown(f"<p style='text-align: center; margin: 0; display: block;'>💰 <b>${float(row.get('Monto Total', 0)):,.2f}</b></p>", unsafe_allow_html=True)
                            c_u.markdown(f"<p style='text-align: center; margin: 0; display: block;'>👨‍💻 {row.get('Registrado por', '---')}</p>", unsafe_allow_html=True)

# 3. RETORNO PAGADO


if is_editor or is_factura:
    # 3. RETORNO PAGADO (GLOBAL)
    with st.container(border=True):
        # Franjita naranja
        st.markdown('<div style="background-color: #f59e0b; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
        st.markdown("<h5 style='margin-top: -0.5rem; color: #364350; font-weight: 800;'>🔄 Retorno pagado</h5>", unsafe_allow_html=True)
        st.write("<small>Registra el monto total de retorno pagado al proveedor de forma global.</small>", unsafe_allow_html=True)
        
        st.write("<br>", unsafe_allow_html=True)
        # Solo columna para el monto
        def update_retorno():
            st.session_state.monto_retorno_val = st.session_state.get('ret_input_monto', 50000.0)

        if st.session_state.get("reset_ret_monto", False):
            if "ret_input_monto" in st.session_state:
                del st.session_state["ret_input_monto"]
            st.session_state.reset_ret_monto = False
            
        # Asegurar que el widget tenga el valor correcto antes de renderizar
        if "ret_input_monto" not in st.session_state:
            st.session_state["ret_input_monto"] = st.session_state.get("monto_retorno_val", 50000.0)
            
        # Usar etiqueta estática para el widget y mostrar el valor dinámico aparte
        st.markdown(f"""
            <p style="font-size: 1.08rem !important; font-weight: 900 !important; color: #1E3A8A !important; margin-bottom: 8px; margin-top: 0px;">
                <b>🔄 Monto del Retorno Pagado Global (${st.session_state.get('ret_input_monto', 50000.0):,.2f} MXN)</b>
            </p>
        """, unsafe_allow_html=True)
        monto_r = st.number_input("Monto del Retorno", 
                                  min_value=0.0, step=100.0, 
                                  key="ret_input_monto", on_change=update_retorno,
                                  label_visibility="collapsed")
        
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Guardar Registro de Retorno", type="primary", use_container_width=True, key="ret_btn_manual"):
            if monto_r <= 0:
                st.warning("El monto debe ser mayor a 0.")
            else:
                exito_ret = False
                with st.spinner("Guardando Retorno Global..."):
                    try:
                        if registrar_retorno_manual(float(monto_r)):
                            exito_ret = True
                    except Exception as e:
                        st.error(f"❌ Error al guardar retorno: {e}")
                
                if exito_ret:
                    st.success(f"✅ ¡Retorno global de ${monto_r:,.2f} MXN registrado!")
                    st.session_state.reset_ret_monto = True
                    st.session_state.monto_retorno_val = 50000.0
                    st.rerun()
        
        # --- HISTORIAL DE RETORNO (DESPLEGABLE) ---
        st.markdown('<div id="historial-retornos"></div>', unsafe_allow_html=True)
        with st.expander("🕒 Ver historial de retorno pagado", expanded=False):
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
                CM_PESOS = [1.0, 1.2, 2.0, 1.3]
                
                cm_tk, cm_f, cm_p, cm_m = st.columns(CM_PESOS)
                cm_tk.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Ticket</b></p>", unsafe_allow_html=True)
                cm_f.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Fecha</b></p>", unsafe_allow_html=True)
                cm_p.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Registrado por</b></p>", unsafe_allow_html=True)
                cm_m.markdown("<p style='text-align: center; margin: 0; display: block;'><b>Monto</b></p>", unsafe_allow_html=True)
                st.divider()
                
                if df_m_filtrado.empty: st.info("No se encontraron registros.")
                else:
                    for idx, row in df_m_filtrado.iterrows():
                        tm_id = str(row.get('Ticket', '---'))
                        es_inactivo_m = row.get('Estado') == 'Inactivo'
                        
                        with st.container(border=True):
                            if es_inactivo_m:
                                # Aplicar filtro visual similar
                                pass 
                            
                            c_tk, c_f, c_p, c_m = st.columns(CM_PESOS)
                            with c_tk:
                                with st.popover(f"🎫 {tm_id}", use_container_width=True):
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
                                    
                                    st.divider()
                                    if not es_inactivo_m:
                                        if st.button("🗑️", key=f"btn_inact_m_{tm_id}", use_container_width=True, type="secondary"):
                                            with st.spinner("Inactivando..."):
                                                nombre_u = st.session_state.usuario_logueado['nombre'] if st.session_state.usuario_logueado else "Usuario"
                                                exito, msj = inactivar_retorno_manual(tm_id, nombre_u)
                                                if exito:
                                                    st.success("✅ Retorno inactivado correctamente.")
                                                    obtener_datos_retorno_manual.clear()
                                                    time.sleep(1)
                                                    st.rerun()
                                                else:
                                                    st.error(f"❌ {msj}")
                                    else:
                                        st.warning("⚠️ Este retorno ya se encuentra INACTIVO.")

                            c_f.markdown(f"<p style='text-align: center; margin: 0; display: block;'>📅 {str(row['Fecha']).split(' ')[0]}</p>", unsafe_allow_html=True)
                            c_p.markdown(f"<p style='text-align: center; margin: 0; display: block;'>👤 {row['Nombre']}</p>", unsafe_allow_html=True)
                            c_m.markdown(f"<p style='text-align: center; margin: 0; display: block;'>💰 ${pd.to_numeric(row.get('Monto Total', 0), errors='coerce'):,.2f}</p>", unsafe_allow_html=True)








if is_editor:
    # Lógica de preparación de datos para el Tablero (Validaciones)
    df_prov = st.session_state.proveedores_df
    
    # Protección total: Si no hay proveedores, no hay nada que validar
    if df_prov.empty:
        st.info("💡 No hay proveedores registrados. Dirígete a la sección de 'Gestión de Proveedores' abajo para añadir el primero.")
    else:
        try:
            prov_visibles = df_prov[df_prov["Visible"] == True]
            # Validar que al menos existan las columnas de cuentas antes de sumar
            cols_reparto = [c for c in CUENTAS if c in prov_visibles.columns]
            errores_porcentaje = [c for c in cols_reparto if abs(prov_visibles[c].sum() - 100.0) > 0.01]
            
            if errores_porcentaje:
                st.warning(f"⚠️ Atención: Los porcentajes no suman 100% para algunas cuentas. El tablero se habilitará cuando la configuración sea correcta.")
            else:
                # 4. TABLERO DE CONTROL 
                df_h_ret_dash = df_gl_retorno
                if not df_h_ret_dash.empty:
                    df_h_ret_dash = df_h_ret_dash[df_h_ret_dash["Estado"] != "Inactivo"]
                    
                df_h_manual_dash = df_gl_manual
                if not df_h_manual_dash.empty:
                    df_h_manual_dash = df_h_manual_dash[df_h_manual_dash["Estado"] != "Inactivo"]
                
                if not df_h_ret_dash.empty:
                    # AUDITORÍA: Ver todos los retornos que tengan impacto en saldos (independiente de la selección actual)
                    # (Lógica de tabla movida abajo para esperar cálculo de saldos)
                    pass
                else:
                    st.info("No hay retornos registrados en el periodo seleccionado.")
                
                # --- CARGA DE DATOS PARA TABLAS DE REPARTO ---
                df_historial = df_gl_abono
                if not df_historial.empty:
                    df_historial = df_historial[df_historial["Estado"] != "Inactivo"]
                    if "Cuenta" in df_historial.columns:
                        df_historial["Cuenta"] = df_historial["Cuenta"].replace(MAPEO_NOMBRES_ANTIGUOS)
        except Exception as e:
            st.error(f"Error procesando el tablero: {e}")
    
        # --- LAS 5 TABLAS DE REPARTO (RESTAURADAS) ---
        filas_resumen = []
        for c in CUENTAS:
            if " (" in c:
                nombre = c.split(" (")[0]
                banco = c.split(" (")[1].replace(")", "")
            else:
                nombre = c; banco = ""
                
            for idx, row_prov in df_prov.iterrows():
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
        
        # --- TABLA DE RESUMEN SINCRONIZADA ---
        resumen_ret_dash = []
        total_pagado_general = 0.0
        total_retorno_general = 0.0
        total_saldo_general = 0.0
        for i, c in enumerate(CUENTAS, 1):
            nombre_c = c.split(" (")[0] if " (" in c else c
            banco_c = c.split(" (")[1].replace(")", "") if " (" in c else ""
            
            # Datos de Auditoría (Ingresos brutos y Diferencias)
            df_c_audit = df_h_ret_dash[(df_h_ret_dash["Nombre"] == nombre_c) & (df_h_ret_dash["Banco"] == banco_c)]
            # Montos de Retorno
            total_monto_bruto = pd.to_numeric(df_c_audit["Monto Total"], errors='coerce').fillna(0).sum()
            total_dif_inside = pd.to_numeric(df_c_audit["Diferencia"], errors='coerce').fillna(0).sum()
            retorno_calc = total_monto_bruto - total_dif_inside
            
            # Acumular totales para los cuadros de abajo
            total_pagado_general += total_monto_bruto
            total_retorno_general += retorno_calc

            # Datos de Saldo (Monto total presupuestado y lo que resta por pagar)
            df_c_res = df_resumen[df_resumen["Clave_Original"] == c]
            total_budget = df_c_res["Pagos a realizar"].sum() if not df_c_res.empty else 0.0
            
            saldo_calc = total_budget - total_monto_bruto
            total_saldo_general += saldo_calc
            resumen_ret_dash.append({
                "# de cuenta": i,
                "Nombre": nombre_c,
                "Cuenta": banco_c,
                "Saldo por cubrir al proveedor": f"${total_budget:,.2f}",
                "Total pagado": f"${total_monto_bruto:,.2f}",
                "Saldo por cubrir": f"${saldo_calc:,.2f}",
                "Diferencia Inside (Comisión)": f"${total_dif_inside:,.2f}",
                "Retorno por pagar": f"${retorno_calc:,.2f}"
            })
        
        # --- TABLA DE RESUMEN SINCRONIZADA ---
        with st.container(border=True):
            st.markdown('<div style="background-color: #6366f1; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top: -0.5rem; color: #312e81; font-weight: 800;'>📊 Tablero de Control - Pagos por realizar</h4>", unsafe_allow_html=True)
            st.markdown("<h5 style='color: #4b5563; font-weight: 700; margin-bottom: 1rem;'>🔄 Resumen de Retornos por Cuenta</h5>", unsafe_allow_html=True)
            
            df_ret_final_dash = pd.DataFrame(resumen_ret_dash)
            st.markdown(generar_tabla_html(df_ret_final_dash, bg_header="#e0e7ff"), unsafe_allow_html=True)
            
            # --- CUADROS DE TOTALES (IGUAL QUE ARRIBA) ---
            col_inf1, col_inf2, col_inf3, col_inf4, col_inf5 = st.columns([1, 2, 2, 2, 1])
            render_metric_card(col_inf2, "Total pagado", t_abonado, "#3b82f6")
            render_metric_card(col_inf3, "Retorno por pagar", max(0, t_ret_neto), "#f59e0b")
            
            # Usar la misma lógica de color y semáforo que arriba para Diferencia Proveedor
            color_adeudo_res = "#10b981" if adeudo <= 0 else "#ef4444"
            semaforo_m_res = "🟢" if adeudo <= 0 else "🔴"
            render_metric_card(col_inf4, f"{semaforo_m_res} Diferencia Proveedor", adeudo, color_adeudo_res)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Botón para Guardar Snapshot (Solo Editores)
            if is_editor:
                if st.button("💾 Guardar Cierre de Mes en Historial", use_container_width=True):
                    # Preparar JSON de la tabla resumen y la detallada
                    json_resumen = df_ret_final_dash.to_json(orient="records")
                    json_detalle = df_resumen.to_json(orient="records")
                    if guardar_snapshot_tablero(m_sel, a_sel, st.session_state.get('ingreso_mensual', 0.0), 
                                                t_abonado, t_ret_auto_bruto, dif_ret, t_manual, adeudo, json_resumen, json_detalle):
                        st.success(f"✅ ¡Tablero completo de {m_sel} {a_sel} guardado con éxito!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar en la base de datos.")

            st.divider()
            
            # --- DESGLOSE INDIVIDUAL POR CUENTA ---
            for c in CUENTAS:
                df_cuenta = df_resumen[df_resumen["Clave_Original"] == c].copy()
                
                # CONSISTENCIA: Si la cuenta está vacía, calculamos el ingreso base y los demás a 0
                ingreso = st.session_state.ingreso_mensual / 5.0
                total_pago = df_cuenta["Pagos a realizar"].sum() if not df_cuenta.empty else 0.0
                total_abono = df_cuenta["Pagado a proveedores"].sum() if not df_cuenta.empty else 0.0
                total_saldo = df_cuenta["Saldo pendiente"].sum() if not df_cuenta.empty else 0.0
                
                bg_color = 'rgba(100, 149, 237, 0.15)' if "BBVA" in c else ('rgba(255, 105, 97, 0.15)' if "Santander" in c else ('rgba(173, 216, 230, 0.15)' if "Banamex" in c else 'rgba(240, 240, 240, 0.1)'))
                logo_banco = "👤" 
                
                def pad_mono(text, length):
                    return str(text).ljust(length)
        
                nombre_raw = f"{logo_banco} {c}"
                nombre_col = pad_mono(nombre_raw, 48) 
                m_ing = f"Ing:${ingreso:,.0f}"
                m_pag = f"PAGO:${total_abono:,.0f}"
                
                m_sal_icon = '🟢' if total_saldo <= 0 else ('🟡' if total_abono > 0 else '🔴')
                m_sal = f"Sal:{m_sal_icon}${total_saldo:,.0f}"
                
                titulo_expander = f"{nombre_col} | {m_ing} | {m_pag} | {m_sal}"
                
                with st.expander(titulo_expander, expanded=False):
                    if df_cuenta.empty:
                        st.info("💡 No hay proveedores asignados a esta cuenta aún.")
                    else:
                        df_disp = df_cuenta[["Proveedor", "Porcentaje", "Pagos a realizar_str", "Pagado a proveedores_str", "Saldo pendiente_str"]].copy()
                        df_disp.rename(columns={
                            "Pagos a realizar_str": "Pago a Realizar", 
                            "Pagado a proveedores_str": "Pagado a proveedores", 
                            "Saldo pendiente_str": "Saldo pendiente"
                        }, inplace=True)
                        st.markdown(generar_tabla_html(df_disp, bg_header=bg_color), unsafe_allow_html=True)
            
            # --- HISTORIAL DE TABLERO DE CONTROL (Opcion 2: Resumen + Detalle) ---
            st.write("<br>", unsafe_allow_html=True)
            with st.expander("🕒 Ver Historial de Tablero de Control (Meses Cerrados)", expanded=False):
                df_hist = obtener_historial_tablero()
                if df_hist.empty:
                    st.info("Aún no hay cierres mensuales registrados.")
                else:
                    # 1. Tabla Maestra de Resumen
                    df_hist = df_hist.sort_values(by=["Año", "Mes"], ascending=False)
                    st.markdown("##### 📝 Resumen Global de Cierres")
                    
                    df_res_view = df_hist[["Mes", "Año", "Ingreso_Total", "Total_Pagado", "Retorno_Pagado", "Dif_Proveedor", "Usuario"]].copy()
                    # Formatear números para estética premium
                    df_res_view["Año"] = df_res_view["Año"].astype(str)
                    for c_fmt in ["Ingreso_Total", "Total_Pagado", "Retorno_Pagado", "Dif_Proveedor"]:
                        df_res_view[c_fmt] = df_res_view[c_fmt].apply(lambda x: f"${pd.to_numeric(x, errors='coerce'):,.0f}")
                    
                    # Limpiar encabezados (quitar guiones bajos)
                    df_res_view.columns = [c.replace("_", " ") for c in df_res_view.columns]
                        
                    st.markdown(generar_tabla_html(df_res_view, bg_header="#e0e7ff"), unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # 2. Selector de Detalle Específico
                    df_hist["Tag_Detail"] = df_hist.apply(lambda r: f"📄 {r['Mes']} {r['Año']}", axis=1)
                    opciones_h = ["--- Seleccionar un mes para ver detalle ---"] + df_hist["Tag_Detail"].tolist()
                    sel_h = st.selectbox("🔍 Buscar desglose detallado", opciones_h)
                    
                    if sel_h != opciones_h[0]:
                        row = df_hist[df_hist["Tag_Detail"] == sel_h].iloc[0]
                        m_h = row["Mes"]; a_h = row["Año"]
                        
                        with st.container(border=True):
                            st.markdown(f"### 📑 Detalle Completo: {m_h} {a_h}")
                            fecha_txt = str(row.get('Fecha_Snapshot', '---'))
                            if "[" in fecha_txt or "{" in fecha_txt: fecha_txt = "Disponible en Sheets"
                            st.caption(f"Registro capturado el {fecha_txt} por {row['Usuario']}")
                            st.write("")
                            
                            # Renderizar métricas archivadas (Cards)
                            h_col1, h_col2, h_col3 = st.columns(3)
                            render_metric_card(h_col1, "Total pagado", row["Total_Pagado"], "#3b82f6")
                            render_metric_card(h_col2, "Retorno por pagar", row["Total_Pagado"] - row["Comision_Inside"] - row["Retorno_Pagado"], "#f59e0b")
                            
                            c_adeudo_h = "#10b981" if row["Dif_Proveedor"] <= 0 else "#ef4444"
                            s_m_h = "🟢" if row["Dif_Proveedor"] <= 0 else "🔴"
                            render_metric_card(h_col3, f"{s_m_h} Diferencia Proveedor", row["Dif_Proveedor"], c_adeudo_h)
                            
                            # Renderizar tablas archivadas
                            try:
                                # A. Resumen de Cuentas
                                tabla_archived = pd.read_json(row["Tabla_Resumen"])
                                st.markdown("##### 📊 Resumen de Cuentas del Período")
                                st.markdown(generar_tabla_html(tabla_archived, bg_header="#f1f5f9"), unsafe_allow_html=True)
                                
                                # B. Desglose detallado por Proveedor
                                if "Tabla_Detalle" in row:
                                    st.write("<br>", unsafe_allow_html=True)
                                    st.markdown("##### 👤 Desglose Individual de Proveedores (Archivado)")
                                    df_det_arch = pd.read_json(row["Tabla_Detalle"])
                                    
                                    # Agrupar por cuenta para mostrar expanders limpios (ahora que no están anidados en otro st.expander)
                                    for c_arch in CUENTAS:
                                        df_cta_arch = df_det_arch[df_det_arch["Clave_Original"] == c_arch].copy()
                                        if not df_cta_arch.empty:
                                            t_ab = df_cta_arch["Pagado a proveedores"].sum()
                                            t_sl = df_cta_arch["Saldo pendiente"].sum()
                                            s_ic = '🟢' if t_sl <= 0 else '🔴'
                                            
                                            # Podemos volver a usar st.expander aquí porque YA NO ESTÁ dentro de otro expander (el principal está cerrado para el detalle)
                                            # ACTUALIZACIÓN: Debido a que seguimos dentro de 'with st.expander("Ver Historial")', seguimos sin poder usar expanders internos.
                                            # Mantendremos st.container con diseño mejorado.
                                            with st.container(border=True):
                                                st.markdown(f"**🏦 {c_arch} | PAGO:${t_ab:,.0f} | Sal:{s_ic}${t_sl:,.0f}**")
                                                cols_sh = ["Proveedor", "Porcentaje", "Pagos a realizar_str", "Pagado a proveedores_str", "Saldo pendiente_str"]
                                                df_sh = df_cta_arch[cols_sh].rename(columns={
                                                    "Pagos a realizar_str": "Pago a Realizar",
                                                    "Pagado a proveedores_str": "Pagado a proveedores",
                                                    "Saldo pendiente_str": "Saldo pendiente"
                                                })
                                                st.markdown(generar_tabla_html(df_sh, bg_header="rgba(200, 200, 200, 0.1)"), unsafe_allow_html=True)
                            except Exception as e:
                                st.warning(f"No se pudo cargar el desglose detallado: {e}")
    # 5. GESTIÓN DE PROVEEDORES
    with st.container(border=True):
        # Franjita rosa para gestión
        st.markdown('<div style="background-color: #e11d48; height: 6px; margin: -1.0rem -1.0rem 1rem -1.0rem; border-radius: 10px 10px 0 0;"></div>', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: -0.5rem; color: #881337; font-weight: 800;'>⚙️ Gestión de Proveedores</h4>", unsafe_allow_html=True)
        
        with st.expander("Panel de Configuración de Proveedores"):
            # Sincronización proactiva: Si proveedores_df cambió fuera, actualizar provs_temp
            if "provs_temp" not in st.session_state or len(st.session_state.provs_temp) != len(st.session_state.proveedores_df):
                st.session_state.provs_temp = st.session_state.proveedores_df.to_dict('records')
                
            # Estados de flujo por pasos
            if "asignacion_confirmada" not in st.session_state:
                st.session_state.asignacion_confirmada = False
                
            # Estado para manejar el reseteo del campo de texto (debe estar fuera del fragmento para persistir)
            if "reset_prov_idx" not in st.session_state:
                st.session_state.reset_prov_idx = 0
                
            # Estado para manejar la confirmación de eliminación y adición
            if "confirm_delete_idx" not in st.session_state:
                st.session_state.confirm_delete_idx = None
            if "confirm_add_prov" not in st.session_state:
                st.session_state.confirm_add_prov = False
            
            nombres_prov_actuales = sorted(list(set([str(p.get("Nombre", "")).strip() for p in st.session_state.provs_temp if str(p.get("Nombre", "")).strip() != ""])))

            # --- LÓGICA DE SINCRONIZACIÓN DINÁMICA ---
            def prov_config_panel():
                @st.fragment
                def render_popover_cuentas():
                    with st.popover("📂 Seleccionar Cuentas", use_container_width=True):
                        def sync_all():
                            val = st.session_state.get("master_ctas", False)
                            for c in CUENTAS:
                                st.session_state[f"p_cta_cb_fin_{c}"] = val
                        
                        def sync_ind():
                            all_sel = all(st.session_state.get(f"p_cta_cb_fin_{c}", False) for c in CUENTAS)
                            st.session_state["master_ctas"] = all_sel

                        st.markdown("**Cuentas a configurar**")
                        st.checkbox("📍 Seleccionar todas", key="master_ctas", on_change=sync_all)
                        for c in CUENTAS:
                            st.checkbox(c, key=f"p_cta_cb_fin_{c}", on_change=sync_ind)
                        
                        st.session_state.cuentas_seleccionadas_final = [c for c in CUENTAS if st.session_state.get(f"p_cta_cb_fin_{c}", False)]

                @st.fragment
                def render_popover_proveedores():
                    with st.popover("👤 Seleccionar Proveedores", use_container_width=True):
                        # 1. LIMPIEZA Y DEDUPLICACIÓN (v9) - GARANTÍA ZERO ERRORS
                        # DEDUPLICACIÓN INTERNA: Cada vez que el menú se refresca, nos aseguramos de que no haya duplicados
                        temp_list = []
                        seen_names = set()
                        for p in st.session_state.provs_temp:
                            name = str(p.get("Nombre", "")).strip()
                            if name != "" and name not in seen_names:
                                temp_list.append(p)
                                seen_names.add(name)
                        st.session_state.provs_temp = temp_list

                        n_v = [p["Nombre"] for p in st.session_state.provs_temp]

                        # 2. SINCRONIZACIÓN REACTIVA (v9)
                        if n_v and "prev_master_provs" not in st.session_state:
                            st.session_state.prev_master_provs = st.session_state.get("master_provs", False)
                        
                        if n_v and st.session_state.get("master_provs", False) != st.session_state.get("prev_master_provs", False):
                            val_m = st.session_state.get("master_provs", False)
                            for n in n_v:
                                st.session_state[f"p_prov_v9_cb_{n}"] = val_m
                            st.session_state.prev_master_provs = val_m

                        def sync_ind_p():
                            all_s = all(st.session_state.get(f"p_prov_v9_cb_{n}", False) for n in n_v) if n_v else False
                            st.session_state.master_provs = all_s
                            st.session_state.prev_master_provs = all_s

                        # --- LISTADO DE PROVEEDORES ---
                        st.markdown("**Proveedores participantes**")
                        if not n_v:
                            st.info("📢 No hay proveedores registrados. ¡Añade uno nuevo abajo!")
                        else:
                            # Sin on_change para que la lógica reactiva de arriba tome el mando
                            st.checkbox("👥 Seleccionar todos", key="master_provs")
                        
                        for i, p_item in enumerate(st.session_state.provs_temp):
                            p_name = p_item["Nombre"]
                            if str(p_name).strip() == "": continue
                            
                            if st.session_state.confirm_delete_idx == i:
                                with st.container(border=True):
                                    st.warning(f"¿Borrar {p_name}?", icon="⚠️")
                                    c_d1, c_d2 = st.columns(2)
                                    with c_d1:
                                        if st.button("❌ No", key=f"c_del_v9_{i}"):
                                            st.session_state.confirm_delete_idx = None
                                    with c_d2:
                                        if st.button("✅ Sí", key=f"f_del_v9_{i}", type="primary"):
                                            p_name_del = st.session_state.provs_temp[i]["Nombre"]
                                            st.session_state.provs_temp.pop(i)
                                            df_new_v = pd.DataFrame(st.session_state.provs_temp, columns=["Nombre", "Visible"] + CUENTAS)
                                            if guardar_config_db(df_new_v):
                                                st.session_state.proveedores_df = df_new_v
                                                st.session_state.pop(f"p_prov_v9_cb_{p_name_del}", None) # Limpieza v9
                                                st.session_state.confirm_delete_idx = None
                                                st.toast(f"🗑️ {p_name_del} eliminado globalmente")
                                                st.rerun()
                            else:
                                r_c1, r_c2 = st.columns([5, 1])
                                with r_c1:
                                    # Usamos prefijo v9 para máxima seguridad reactiva
                                    st.checkbox(p_name, key=f"p_prov_v9_cb_{p_name}", on_change=sync_ind_p)
                                with r_c2:
                                    if st.button("🗑", key=f"b_del_v9_{i}"):
                                        st.session_state.confirm_add_prov = False
                                        st.session_state.confirm_delete_idx = i; st.rerun()
                        
                        st.divider()
                        st.write("<small>Añadir Nuevo:</small>", unsafe_allow_html=True)
                        f_col1, f_col2 = st.columns([4, 1])
                        
                        with f_col1:
                            # v9 asegura limpieza total tras cada éxito (Zero Errors)
                            nuevo_v9 = st.text_input("Nombre", key=f"in_new_v9_{st.session_state.reset_prov_idx}", label_visibility="collapsed")
                        with f_col2:
                            if st.button("➕", key="btn_add_v9_f"):
                                if nuevo_v9.strip() and nuevo_v9.strip() not in n_v:
                                    # EXCLUSIVIDAD: Si vamos a añadir, cancelamos el borrado
                                    st.session_state.confirm_delete_idx = None
                                    st.session_state.confirm_add_prov = True

                        if st.session_state.confirm_add_prov:
                            with st.container(border=True):
                                st.warning(f"¿Registrar '{nuevo_v9.strip()}'?", icon="ℹ️")
                                ca_col1, ca_col2 = st.columns(2)
                                with ca_col1:
                                    if st.button("❌ No", key="no_add_v9_f"):
                                        st.session_state.confirm_add_prov = False
                                        st.session_state.reset_prov_idx += 1; st.rerun()
                                with ca_col2:
                                    if st.button("✅ Sí", key="yes_add_v9_f", type="primary"):
                                        # LIMPIEZA INMEDIATA: Desactivamos la pregunta antes de procesar para evitar race conditions
                                        st.session_state.confirm_add_prov = False
                                        nom_ok = nuevo_v9.strip()
                                        if nom_ok not in n_v:
                                            new_p = {"Nombre": nom_ok, "Visible": True}
                                            for c in CUENTAS: new_p[c] = 0.0
                                            st.session_state.provs_temp.append(new_p)
                                            
                                        df_add = pd.DataFrame(st.session_state.provs_temp, columns=["Nombre", "Visible"] + CUENTAS)
                                        if guardar_config_db(df_add):
                                            st.session_state.proveedores_df = df_add
                                            st.session_state.reset_prov_idx += 1
                                            st.toast(f"✅ {nom_ok} registrado"); st.rerun()
                        
                        # Sincronización final usando IDs v6
                        st.session_state.provs_seleccionados_final = [p["Nombre"] for p in st.session_state.provs_temp if st.session_state.get(f"p_prov_v9_cb_{p['Nombre']}", False)]
                    
            
                # --- DISEÑO DEL PANEL ---
                lc1, lc2 = st.columns(2)
                n_sel_c = sum(1 for c in CUENTAS if st.session_state.get(f"p_cta_cb_fin_{c}", False))
                n_sel_p = sum(1 for p in st.session_state.provs_temp if st.session_state.get(f"p_prov_v9_cb_{p['Nombre']}", False))

                with lc1:
                    st.info(f"🏦 {n_sel_c} cuentas seleccionadas")
                    render_popover_cuentas()
                    
                with lc2:
                    st.info(f"👥 {n_sel_p} proveedores seleccionados")
                    render_popover_proveedores()
                
                # --- BOTÓN PASO 1 ---
                st.write("<br>", unsafe_allow_html=True)
                if st.button("💾 **Confirmar Asignación para Paso 2**", type="primary", use_container_width=True):
                    s_c = [c for c in CUENTAS if st.session_state.get(f"p_cta_cb_fin_{c}", False)]
                    s_p = [p["Nombre"] for p in st.session_state.provs_temp if st.session_state.get(f"p_prov_v9_cb_{p['Nombre']}", False)]
                    
                    if not s_c or not s_p:
                        st.warning("⚠️ Selecciona cuentas y proveedores antes de confirmar.")
                    else:
                        st.session_state.cuentas_seleccionadas_final = s_c
                        st.session_state.provs_seleccionados_final = s_p
                        st.session_state.asignacion_confirmada = True
                        
                        # LÓGICA INDIVIDUAL: Solo preparamos la visibilidad para el Paso 2
                        for p in st.session_state.provs_temp:
                            # Si se seleccionó en el Paso 1, lo hacemos visible para editar en el Paso 2
                            if p["Nombre"] in s_p:
                                p["Visible"] = True
                            
                            # LIMPIEZA SÓLO PARA LAS CUENTAS SELECCIONADAS ACTUALMENTE
                            for c in s_c:
                                if p["Nombre"] not in s_p:
                                    p[c] = 0.0
                        
                        # ¡IMPORTANTE!: Las cuentas que NO están en s_c no se tocan. Se quedan como están en el DB.

                        # MEMORIA INTERNA: Actualizamos la vista local sin tocar el Google Sheets (Paso 1 Pasivo)
                        df_v1 = pd.DataFrame(st.session_state.provs_temp, columns=["Nombre", "Visible"] + CUENTAS)
                        st.session_state.proveedores_df = df_v1
                        st.toast("✅ Selección preparada. Ajusta los montos abajo.") # Sin rerun para estabilidad

            prov_config_panel()

            st.divider()

            # --- SECCIÓN DE PORCENTAJES (PASO 2) ---
            if not st.session_state.asignacion_confirmada:
                st.info("💡 **Paso 1:** Selecciona cuentas y proveedores arriba y pulsa 'Confirmar Asignación'.")
            else:
                cuentas_seleccionadas = st.session_state.get("cuentas_seleccionadas_final", [])
                provs_seleccionados = st.session_state.get("provs_seleccionados_final", [])
                
                # Sincronizar: Poner a 0% los no seleccionados para las cuentas activas
                for p_env in st.session_state.provs_temp:
                    if p_env["Nombre"] not in provs_seleccionados:
                        for c_sel in cuentas_seleccionadas:
                            p_env[c_sel] = 0.0

                st.markdown("<h5 style='color: #334155;'>📊 Ajustar Reparto de Pagos</h5>", unsafe_allow_html=True)
                st.write("<small>Define cuánto le toca a cada uno (la suma debe dar 100%)</small>", unsafe_allow_html=True)
                
                valid_global = True
                for c_name in cuentas_seleccionadas:
                    with st.container(border=True):
                        st.markdown(f"🏦 **Distribución para {c_name}**")
                        
                        suma_cta = sum(float(p.get(c_name, 0.0)) for p in st.session_state.provs_temp if p["Nombre"] in provs_seleccionados)
                        
                        # Alerta visual intuitiva
                        diff = 100.0 - suma_cta
                        if abs(diff) < 0.01:
                            st.success(f"✅ ¡Reparto Completo! (Total: {suma_cta}%)")
                        elif diff > 0:
                            st.warning(f"⚠️ **Falta saldo:** Escribe {diff:.1f}% más para completar esta cuenta.")
                            valid_global = False
                        else:
                            st.error(f"🚨 **Saldo excedido:** Te pasaste por {abs(diff):.1f}%. Ajusta los valores.")
                            valid_global = False

                        # PROGRESS BAR PREMIUM
                        progreso = min(suma_cta / 100.0, 1.0)
                        st.progress(progreso)

                        # Lista de inputs en 2 columnas para limpieza (como solicitaste)
                        for p_name in provs_seleccionados:
                            p_obj = next((item for item in st.session_state.provs_temp if item["Nombre"] == p_name), None)
                            if p_obj:
                                i_col1, i_col2 = st.columns([3, 1])
                                with i_col1:
                                    st.write(f"📦 **{p_name}**")
                                with i_col2:
                                    val_act = float(p_obj.get(c_name, 0.0))
                                    p_obj[c_name] = st.number_input(f"%", value=val_act, step=1.0, min_value=0.0, max_value=100.0, key=f"pct_v2_{c_name}_{p_name}", label_visibility="collapsed")
                
                st.divider()
                # Botón FINAL Paso 2
                if st.button("💾 **Guardar Nueva Asignación de Pagos**", type="primary", use_container_width=True):
                    if not valid_global:
                        st.error("❌ **Error:** No podemos guardar si las cuentas no suman exactamente 100%. Revisa los mensajes de arriba.")
                    else:
                        df_step2 = pd.DataFrame(st.session_state.provs_temp)
                        with st.spinner("Guardando en Google Sheets..."):
                            if guardar_config_db(df_step2):
                                st.session_state.proveedores_df = df_step2
                                st.session_state.provs_temp = df_step2.to_dict('records') # ¡SINCRONIZACIÓN CRÍTICA!
                                st.session_state.asignacion_confirmada = False # Reset para la próxima
                                st.toast("✅ ¡Configuración guardada con éxito!")
                                st.rerun()
                            else:
                                st.error("Error de conexión al guardar.")



