import json
import os
import datetime
import urllib.parse
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Bucle Infinito - Control Financiero",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SVG DE FONDO POTENTE ESTILO FINTECH ---
bg_svg = '''
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <defs>
    <linearGradient id="baseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f2ba2c"/>
      <stop offset="45%" stop-color="#eb8e15"/>
      <stop offset="100%" stop-color="#d65a10"/>
    </linearGradient>
    <radialGradient id="sunGlow" cx="72%" cy="48%" r="48%">
      <stop offset="0%" stop-color="#ffe066" stop-opacity="0.55"/>
      <stop offset="60%" stop-color="#f59e0b" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#d65a10" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="coinFace" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffd54f" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#d97706" stop-opacity="0.18"/>
    </linearGradient>
  </defs>
  <rect width="1600" height="900" fill="url(#baseGrad)"/>
  <rect width="1600" height="900" fill="url(#sunGlow)"/>
  <circle cx="150" cy="780" r="460" fill="none" stroke="#ffffff" stroke-opacity="0.11" stroke-width="55"/>
  <circle cx="150" cy="780" r="320" fill="#ffffff" fill-opacity="0.05"/>
  <path d="M 980 0 L 1600 0 L 1600 900 L 760 900 Z" fill="#ffffff" fill-opacity="0.05"/>
  <g transform="translate(1330, 290) rotate(8)">
    <polygon points="0,-165 143,-82 143,82 0,165 -143,82 -143,-82" fill="url(#coinFace)" stroke="#fff3b0" stroke-opacity="0.42" stroke-width="8"/>
    <polygon points="0,-130 112,-65 112,65 0,130 -112,65 -112,-65" fill="none" stroke="#fff3b0" stroke-opacity="0.30" stroke-width="4"/>
    <text x="0" y="34" text-anchor="middle" font-family="Arial, sans-serif" font-weight="900" font-size="115" fill="#fff8d6" fill-opacity="0.34">₿</text>
  </g>
  <g transform="translate(1330, 675) rotate(-6)">
    <polygon points="0,-165 143,-82 143,82 0,165 -143,82 -143,-82" fill="url(#coinFace)" stroke="#fff3b0" stroke-opacity="0.42" stroke-width="8"/>
    <polygon points="0,-130 112,-65 112,65 0,130 -112,65 -112,-65" fill="none" stroke="#fff3b0" stroke-opacity="0.30" stroke-width="4"/>
    <text x="0" y="36" text-anchor="middle" font-family="Arial, sans-serif" font-weight="900" font-size="115" fill="#fff8d6" fill-opacity="0.34">$</text>
  </g>
</svg>
'''.strip().replace("\n", "")

bg_encoded = urllib.parse.quote(bg_svg)

st.markdown(f'''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}

    .stApp {{
        background-color: #e88914;
        background-image: url("data:image/svg+xml;utf8,{bg_encoded}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #16243e;
    }}
    header[data-testid="stHeader"] {{background: transparent;}}
    .block-container {{padding-top: 1.4rem; padding-bottom: 2.5rem; max-width: 1260px;}}

    /* NAVBAR SUPERIOR */
    .top-navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 22px;
        flex-wrap: wrap;
        gap: 12px;
    }}
    .brand-logo {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .brand-icon {{
        background: #16243e;
        color: #f3b136;
        width: 44px;
        height: 44px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 6px 14px rgba(22,36,62,0.25);
        flex-shrink: 0;
    }}
    .brand-text {{
        font-size: 22px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.8px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.18);
    }}
    .brand-text span {{
        font-weight: 500;
        opacity: 0.92;
    }}
    .user-area {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .cloud-badge {{
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(8px);
        color: #ffffff;
        padding: 7px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid rgba(255,255,255,0.38);
    }}
    .user-pill {{
        background-color: #16243e;
        color: #ffffff;
        padding: 8px 18px;
        border-radius: 30px;
        font-weight: 600;
        font-size: 13px;
        box-shadow: 0 6px 15px rgba(22,36,62,0.28);
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    /* GRID HTML NATIVO PARA LOS 3 BOLSILLOS */
    .pockets-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        width: 100%;
    }}
    .pocket-card {{
        background-color: #ffffff;
        border-radius: 16px;
        padding: 18px 20px 15px 20px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.13);
        border-bottom: 5px solid #e5e9f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        min-height: 118px;
        width: 100%;
        box-sizing: border-box;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .pocket-card:hover {{
        transform: translateY(-2px);
        border-bottom: 5px solid #16243e;
    }}
    .pocket-card-gold {{
        border-bottom: 5px solid #f0a518 !important;
    }}
    .pocket-info {{
        min-width: 0;
        flex: 1;
        padding-right: 10px;
    }}
    .pocket-title {{
        font-size: 12.5px;
        font-weight: 700;
        color: #2c3a4f;
        margin-bottom: 6px;
    }}
    .pocket-value-row {{
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .coin-dot {{
        background: linear-gradient(135deg, #f6bd41, #e08b1b);
        color: #ffffff;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 800;
        flex-shrink: 0;
    }}
    .pocket-amount {{
        font-size: 27px;
        font-weight: 800;
        color: #d48817;
        line-height: 1.1;
    }}
    .pocket-sub {{
        font-size: 11.5px;
        color: #7a869a;
        margin-top: 6px;
        font-weight: 500;
    }}
    .pocket-line-icon {{
        width: 44px;
        height: 44px;
        border-radius: 12px;
        background-color: #f4f7fb;
        border: 1.5px solid #dde5f0;
        color: #16243e;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        flex-shrink: 0;
    }}

    /* BOTONES DE NAVEGACIÓN TIPO APP */
    .app-nav-card {{
        background: #ffffff;
        border-radius: 16px;
        width: 64px;
        height: 64px;
        margin: 0 auto 2px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.14);
        border: 3px solid transparent;
    }}
    .app-nav-card-active {{
        background: #ffffff;
        border-radius: 16px;
        width: 64px;
        height: 64px;
        margin: 0 auto 2px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        box-shadow: 0 8px 18px rgba(22,36,62,0.30);
        border: 3px solid #16243e;
    }}

    div[class*="st-key-nav_"] {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }}
    div[class*="st-key-nav_"] button {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 2px 0px !important;
        margin: 0 auto !important;
        width: 100% !important;
        min-height: 26px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    div[class*="st-key-nav_"] button > div {{
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }}
    div[class*="st-key-nav_"] button p {{
        font-size: 12.5px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin: 0 auto !important;
        width: 100% !important;
        text-align: center !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.28);
        white-space: nowrap !important;
    }}

    /* BOTONES GIGANTES INGRESO Y EGRESO */
    div[class*="st-key-btn_in_big"] button {{
        background: linear-gradient(145deg, #10b376, #0a8758) !important;
        color: #ffffff !important;
        border: 2px solid rgba(255,255,255,0.35) !important;
        border-radius: 18px !important;
        height: 118px !important;
        width: 100% !important;
        box-shadow: 0 10px 22px rgba(10,135,88,0.35) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    div[class*="st-key-btn_in_big"] button > div {{
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }}
    div[class*="st-key-btn_in_big"] button p {{
        font-size: 19px !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: 0.6px !important;
        text-align: center !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }}
    div[class*="st-key-btn_in_big"] button:hover {{
        background: linear-gradient(145deg, #12c482, #0c9662) !important;
        transform: translateY(-2px);
    }}

    div[class*="st-key-btn_out_big"] button {{
        background: linear-gradient(145deg, #cf4646, #a62c2c) !important;
        color: #ffffff !important;
        border: 2px solid rgba(255,255,255,0.35) !important;
        border-radius: 18px !important;
        height: 118px !important;
        width: 100% !important;
        box-shadow: 0 10px 22px rgba(166,44,44,0.35) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    div[class*="st-key-btn_out_big"] button > div {{
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }}
    div[class*="st-key-btn_out_big"] button p {{
        font-size: 19px !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: 0.6px !important;
        text-align: center !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }}
    div[class*="st-key-btn_out_big"] button:hover {{
        background: linear-gradient(145deg, #dc4f4f, #b53232) !important;
        transform: translateY(-2px);
    }}

    /* FORMULARIO */
    div[data-testid="stForm"] {{
        background-color: #ffffff;
        border-radius: 18px;
        padding: 20px 24px;
        border: none;
        border-bottom: 5px solid #e5e9f0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
    }}
    div[data-testid="stForm"] label {{
        color: #16243e !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
    }}
    div[data-testid="stFormSubmitButton"] button {{
        background-color: #16243e !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 10px 20px !important;
        margin-top: 26px !important;
        width: 100% !important;
        border: none !important;
    }}
    div[data-testid="stFormSubmitButton"] button:hover {{
        background-color: #24385c !important;
    }}

    /* TABLA CON SCROLL HORIZONTAL EN MÓVIL */
    .table-responsive-wrapper {{
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        border-radius: 18px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
        border-bottom: 5px solid #e5e9f0;
        background-color: #ffffff;
    }}
    .custom-table {{
        width: 100%;
        border-collapse: collapse;
        background-color: #ffffff;
        font-size: 13.5px;
    }}
    .custom-table thead {{
        background-color: #16243e;
        color: #ffffff;
    }}
    .custom-table th {{
        padding: 14px 14px;
        text-align: left;
        font-weight: 700;
        font-size: 12.5px;
        letter-spacing: 0.3px;
        white-space: nowrap;
    }}
    .custom-table td {{
        padding: 12px 14px;
        border-bottom: 1px solid #f0f3f8;
        color: #16243e;
        font-weight: 600;
        white-space: nowrap;
    }}
    .custom-table tbody tr:hover {{
        background-color: #fafbfd;
    }}
    .txt-gold {{color: #d48817 !important; font-weight: 700;}}
    .txt-green {{color: #0d9c66 !important; font-weight: 700;}}
    .txt-red {{color: #ba3b3b !important; font-weight: 700;}}

    /* =====================================================================
       ANULACIÓN TOTAL DE ANCHOS INLINE DE STREAMLIT EN CELULAR (<= 820px)
       ===================================================================== */
    @media (max-width: 820px) {{
        .block-container {{
            padding-top: 0.8rem !important;
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
            padding-bottom: 2.2rem !important;
        }}
        .top-navbar {{
            margin-bottom: 14px;
            gap: 8px;
        }}
        .brand-icon {{
            width: 36px;
            height: 36px;
            font-size: 18px;
            border-radius: 10px;
        }}
        .brand-text {{
            font-size: 18px;
        }}

        /* 1. Forzar 100% de ancho anulando style="width: calc(...)" de Streamlit */
        div[data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 12px !important;
        }}
        div[data-testid="stHorizontalBlock"] > div {{
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }}

        /* 2. Los 3 bolsillos en 1 columna al 100% de ancho */
        .pockets-grid {{
            grid-template-columns: 1fr !important;
            gap: 10px !important;
        }}
        .pocket-card {{
            min-height: 92px;
            padding: 15px 18px;
        }}
        .pocket-amount {{
            font-size: 25px;
        }}

        /* 3. Cuadrícula 3x2 para los 6 botones de navegación */
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-nav_"]) {{
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: 12px 6px !important;
            width: 100% !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-nav_"]) > div {{
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }}
        .app-nav-card, .app-nav-card-active {{
            width: 56px;
            height: 56px;
            font-size: 23px;
            border-radius: 14px;
        }}

        /* 4. Botones + INGRESO y − EGRESO abajo en fila completa 50% / 50% */
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-btn_in_big"]) {{
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 12px !important;
            width: 100% !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-btn_in_big"]) > div {{
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }}
        div[class*="st-key-btn_in_big"] button,
        div[class*="st-key-btn_out_big"] button {{
            height: 58px !important;
            border-radius: 14px !important;
            width: 100% !important;
        }}
        div[class*="st-key-btn_in_big"] button p,
        div[class*="st-key-btn_out_big"] button p {{
            font-size: 16px !important;
        }}

        /* 5. Formulario al 100% de ancho */
        div[data-testid="stForm"] {{
            padding: 16px !important;
            width: 100% !important;
        }}
        div[data-testid="stFormSubmitButton"] button {{
            margin-top: 10px !important;
            height: 46px !important;
            width: 100% !important;
        }}
        div[data-testid="stFormSubmitButton"] button p {{
            white-space: nowrap !important;
        }}
    }}
</style>
''', unsafe_allow_html=True)

ARCHIVO_LOCAL = "bucle_infinito_datos.csv"

def usar_google_sheets():
    return ("gcp_json" in st.secrets or "gcp_service_account" in st.secrets) and "sheet_url" in st.secrets

@st.cache_resource
def conectar_google_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    if "gcp_json" in st.secrets:
        info = json.loads(st.secrets["gcp_json"])
    else:
        info = dict(st.secrets["gcp_service_account"])
    
    info["auth_uri"] = "https://accounts.google.com/o/oauth2/auth"
    info["token_uri"] = "https://oauth2.googleapis.com/token"
    info["auth_provider_x509_cert_url"] = "https://www.googleapis.com/oauth2/v1/certs"
    if "@" not in str(info.get("client_email", "")) or "://" in str(info.get("client_email", "")):
        info["client_email"] = "bot-finanzas@finanzas-bucle.iam.gserviceaccount.com"

    creds = Credentials.from_service_account_info(info, scopes=scopes)
    cliente = gspread.authorize(creds)
    url_sheet = st.secrets["sheet_url"].strip()
    return cliente.open_by_url(url_sheet).sheet1

def datos_iniciales_df():
    return pd.DataFrame([
        {"Fecha": "26/11/2026", "Tipo": "Ingreso", "Categoría": "Moto", "Bruto": 10000, "Peaje_1": -100, "Peaje_9": -900, "Monto_Neto": 9000, "Bolsillo": "Efectivo Libre"},
    ])

def guardar_historial(df):
    if usar_google_sheets():
        hoja = conectar_google_sheet()
        hoja.clear()
        datos_lista = [df.columns.values.tolist()] + df.fillna("").values.tolist()
        hoja.update(datos_lista)
    else:
        df.to_csv(ARCHIVO_LOCAL, index=False)

def cargar_historial():
    if usar_google_sheets():
        hoja = conectar_google_sheet()
        registros = hoja.get_all_records()
        if not registros:
            df = datos_iniciales_df()
            guardar_historial(df)
            return df
        df = pd.DataFrame(registros)
        for col in ["Bruto", "Peaje_1", "Peaje_9", "Monto_Neto"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
    else:
        if not os.path.exists(ARCHIVO_LOCAL):
            df = datos_iniciales_df()
            df.to_csv(ARCHIVO_LOCAL, index=False)
            return df
        return pd.read_csv(ARCHIVO_LOCAL)

if "modo_registro" not in st.session_state:
    st.session_state.modo_registro = "INGRESO"
if "seccion_activa" not in st.session_state:
    st.session_state.seccion_activa = "Tablero"

df = cargar_historial()

boveda_1 = abs(df["Peaje_1"].sum())
ingresos_9 = abs(df["Peaje_9"].sum())
egresos_9 = df[(df["Tipo"] == "Egreso") & (df["Bolsillo"] == "Fondo 9%")]["Monto_Neto"].sum()
fondo_9 = ingresos_9 + egresos_9

movs_libre = df[df["Bolsillo"] == "Efectivo Libre"]["Monto_Neto"].sum()
capital_invertido = abs(df[(df["Tipo"] == "Egreso") & (df["Bolsillo"] == "Fondo 9%") & (df["Categoría"] == "Enviar a Inversión")]["Monto_Neto"].sum())
abonos_deuda = abs(df[df["Categoría"] == "Deuda"]["Monto_Neto"].sum())

# --- NAVBAR SUPERIOR ---
estado_nube = "☁️ Sincronizado" if usar_google_sheets() else "💻 Local"
st.markdown(f'<div class="top-navbar"><div class="brand-logo"><div class="brand-icon">🔄</div><div class="brand-text">BUCLE<span>INFINITO</span></div></div><div class="user-area"><div class="cloud-badge">{estado_nube}</div><div class="user-pill">🇨🇴 Edwin Alexander</div></div></div>', unsafe_allow_html=True)

# --- ESTRUCTURA PRINCIPAL ---
col_izq, col_der = st.columns([4.3, 1], gap="medium")

with col_izq:
    # LOS 3 BOLSILLOS EN BLOQUE HTML GRID
    pockets_html = f'''
    <div class="pockets-grid">
        <div class="pocket-card">
            <div class="pocket-info">
                <div class="pocket-title">Bóveda Vitalicia (1%)</div>
                <div class="pocket-value-row"><span class="coin-dot">$</span><span class="pocket-amount">{boveda_1:,.0f}</span></div>
                <div class="pocket-sub">Capital intocable de por vida</div>
            </div>
            <div class="pocket-line-icon">🔒</div>
        </div>
        <div class="pocket-card">
            <div class="pocket-info">
                <div class="pocket-title">Fondo Emergencia / Inv. (9%)</div>
                <div class="pocket-value-row"><span class="coin-dot">$</span><span class="pocket-amount">{fondo_9:,.0f}</span></div>
                <div class="pocket-sub">Colchón y capital de inversión</div>
            </div>
            <div class="pocket-line-icon">🛡️</div>
        </div>
        <div class="pocket-card pocket-card-gold">
            <div class="pocket-info">
                <div class="pocket-title">Efectivo Libre</div>
                <div class="pocket-value-row"><span class="coin-dot">$</span><span class="pocket-amount">{movs_libre:,.0f}</span></div>
                <div class="pocket-sub">Disponible tras peajes</div>
            </div>
            <div class="pocket-line-icon">👛</div>
        </div>
    </div>
    '''
    st.markdown(pockets_html, unsafe_allow_html=True)

    st.write("")

    # BOTONES DE NAVEGACIÓN TIPO APP
    nav_cols = st.columns(6, gap="small")
    secciones = [
        ("Tablero", "🎛️", "Tablero"),
        ("Editar", "✏️", "Editar"),
        ("Inversiones", "📈", "Inversiones"),
        ("Deudas", "💳", "Deudas"),
        ("Metas", "🏆", "Metas"),
        ("Exportar", "📥", "Exportar")
    ]
    for idx, (clave, icono, etiqueta) in enumerate(secciones):
        with nav_cols[idx]:
            clase_card = "app-nav-card-active" if st.session_state.seccion_activa == clave else "app-nav-card"
            st.markdown(f'<div class="{clase_card}">{icono}</div>', unsafe_allow_html=True)
            if st.button(etiqueta, key=f"nav_{clave}"):
                st.session_state.seccion_activa = clave
                st.rerun()

    st.write("")

    # PANEL DE REGISTRO O SUB-SECCIÓN ACTIVA
    if st.session_state.seccion_activa == "Tablero":
        if st.session_state.modo_registro == "INGRESO":
            with st.form("form_ingreso", clear_on_submit=True):
                f1, f2, f3, f4 = st.columns([1.2, 1.3, 1.2, 1.2])
                fecha_in = f1.date_input("Fecha:", value=datetime.date.today())
                cat_in = f2.selectbox("Fuente de Ingreso:", ["Moto", "Trading (Ganancias)", "Salario / Extra"])
                monto_in = f3.number_input("Monto Bruto ($):", min_value=0, step=1000, value=10000)
                with f4:
                    submit_in = st.form_submit_button("Registrar Ingreso")

                if submit_in and monto_in > 0:
                    p1 = -round(monto_in * 0.01)
                    p9 = -round(monto_in * 0.09)
                    neto = monto_in + p1 + p9
                    nueva_fila = pd.DataFrame([{
                        "Fecha": fecha_in.strftime("%d/%m/%Y"),
                        "Tipo": "Ingreso",
                        "Categoría": cat_in,
                        "Bruto": monto_in,
                        "Peaje_1": p1,
                        "Peaje_9": p9,
                        "Monto_Neto": neto,
                        "Bolsillo": "Efectivo Libre"
                    }])
                    df = pd.concat([nueva_fila, df], ignore_index=True)
                    guardar_historial(df)
                    st.rerun()

        else:
            with st.form("form_egreso", clear_on_submit=True):
                f1, f2, f3, f4 = st.columns([1.3, 1.3, 1.1, 1.2])
                bolsillo_out = f1.selectbox("Descontar de:", ["Efectivo Libre", "Fondo 9%"])
                opciones_cat = (
                    ["Gasolina", "Deuda", "Comida / Gustos", "Otro Gasto"]
                    if bolsillo_out == "Efectivo Libre"
                    else ["Enviar a Inversión", "Emergencia Médica / Hogar"]
                )
                cat_out = f2.selectbox("Categoría:", opciones_cat)
                monto_out = f3.number_input("Monto ($):", min_value=0, step=500, value=5000)
                with f4:
                    submit_out = st.form_submit_button("Registrar Egreso")

                if submit_out and monto_out > 0:
                    nueva_fila = pd.DataFrame([{
                        "Fecha": datetime.date.today().strftime("%d/%m/%Y"),
                        "Tipo": "Egreso",
                        "Categoría": cat_out,
                        "Bruto": 0,
                        "Peaje_1": 0,
                        "Peaje_9": 0,
                        "Monto_Neto": -abs(monto_out),
                        "Bolsillo": bolsillo_out
                    }])
                    df = pd.concat([nueva_fila, df], ignore_index=True)
                    guardar_historial(df)
                    st.rerun()

    elif st.session_state.seccion_activa == "Editar":
        if len(df) == 0:
            st.warning("No hay registros para editar o eliminar.")
        else:
            opciones_filas = [
                f"#{i} | {row['Fecha']} | {row['Tipo']} - {row['Categoría']} (${abs(row['Monto_Neto']):,.0f})"
                for i, row in df.iterrows()
            ]
            seleccion = st.selectbox("Selecciona el registro a modificar o eliminar:", opciones_filas)
            idx_sel = int(seleccion.split(" | ")[0].replace("#", ""))
            fila_actual = df.loc[idx_sel]

            with st.form("form_editar"):
                e1, e2, e3, e4, e5 = st.columns([1.1, 1.2, 1.1, 1.1, 1.1])
                nueva_fecha = e1.text_input("Fecha:", value=str(fila_actual["Fecha"]))
                nueva_cat = e2.text_input("Categoría:", value=str(fila_actual["Categoría"]))
                valor_actual = float(fila_actual["Bruto"]) if fila_actual["Tipo"] == "Ingreso" else abs(float(fila_actual["Monto_Neto"]))
                nuevo_monto = e3.number_input("Monto ($):", min_value=0.0, step=500.0, value=valor_actual)
                with e4:
                    btn_guardar = st.form_submit_button("💾 Guardar")
                with e5:
                    btn_borrar = st.form_submit_button("🗑️ Eliminar")

                if btn_guardar and nuevo_monto > 0:
                    df.at[idx_sel, "Fecha"] = nueva_fecha
                    df.at[idx_sel, "Categoría"] = nueva_cat
                    if fila_actual["Tipo"] == "Ingreso":
                        p1 = -round(nuevo_monto * 0.01)
                        p9 = -round(nuevo_monto * 0.09)
                        df.at[idx_sel, "Bruto"] = nuevo_monto
                        df.at[idx_sel, "Peaje_1"] = p1
                        df.at[idx_sel, "Peaje_9"] = p9
                        df.at[idx_sel, "Monto_Neto"] = nuevo_monto + p1 + p9
                    else:
                        df.at[idx_sel, "Monto_Neto"] = -abs(nuevo_monto)
                    guardar_historial(df)
                    st.rerun()

                if btn_borrar:
                    df = df.drop(index=idx_sel).reset_index(drop=True)
                    guardar_historial(df)
                    st.rerun()

    elif st.session_state.seccion_activa == "Inversiones":
        st.info(f"📈 **Capital enviado desde el Fondo 9% hacia Inversiones:** **${capital_invertido:,.0f}**  |  *Cuando retires ganancias, regístralas con **INGRESO -> Trading (Ganancias)** para que pasen por los peajes del 1% y 9%.*")
    elif st.session_state.seccion_activa == "Deudas":
        st.info(f"💳 **Total abonado a Deudas desde Efectivo Libre:** **${abonos_deuda:,.0f}**")
    elif st.session_state.seccion_activa == "Metas":
        meta_9 = 100000
        progreso = min(fondo_9 / meta_9, 1.0) if meta_9 > 0 else 0
        st.progress(progreso, text=f"🏆 Meta Colchón Fondo 9%: ${fondo_9:,.0f} / ${meta_9:,.0f} ({progreso*100:.0f}%)")
    elif st.session_state.seccion_activa == "Exportar":
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar Historial Completo en CSV / Excel",
            data=csv_bytes,
            file_name="historial_bucle_infinito.csv",
            mime="text/csv"
        )

    st.write("")

    # TABLA ENVUELTA EN CONTENEDOR RESPONSIVE
    filas_html = ""
    for idx, row in df.head(25).iterrows():
        p1_txt = f"-${abs(row['Peaje_1']):,.0f}" if row["Peaje_1"] != 0 else "$0"
        p9_txt = f"-${abs(row['Peaje_9']):,.0f}" if row["Peaje_9"] != 0 else "$0"
        p1_cls = "txt-gold" if row["Peaje_1"] != 0 else ""
        p9_cls = "txt-gold" if row["Peaje_9"] != 0 else ""

        if row["Monto_Neto"] >= 0:
            neto_txt = f"+${row['Monto_Neto']:,.0f}"
            neto_cls = "txt-green"
        else:
            neto_txt = f"-${abs(row['Monto_Neto']):,.0f}"
            neto_cls = "txt-red"

        filas_html += f'<tr><td><strong>#{idx}</strong></td><td>{row["Fecha"]}</td><td>{row["Tipo"]}</td><td>{row["Categoría"]}</td><td class="{p1_cls}">{p1_txt}</td><td class="{p9_cls}">{p9_txt}</td><td class="{neto_cls}">{neto_txt}</td><td>{row["Bolsillo"]}</td></tr>'

    tabla_completa = f'<div class="table-responsive-wrapper"><table class="custom-table"><thead><tr><th>ID</th><th>Fecha</th><th>Tipo</th><th>Categoría</th><th>1% Peaje</th><th>9% Peaje</th><th>Monto Neto</th><th>Bolsillo</th></tr></thead><tbody>{filas_html}</tbody></table></div>'
    st.markdown(tabla_completa, unsafe_allow_html=True)

with col_der:
    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        if st.button("+ INGRESO", key="btn_in_big"):
            st.session_state.modo_registro = "INGRESO"
            st.session_state.seccion_activa = "Tablero"
            st.rerun()
    with btn_c2:
        if st.button("− EGRESO", key="btn_out_big"):
            st.session_state.modo_registro = "EGRESO"
            st.session_state.seccion_activa = "Tablero"
            st.rerun()
