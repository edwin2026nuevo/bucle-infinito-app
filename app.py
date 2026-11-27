import json
import os
import datetime
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

# --- ESTILOS VISUALES ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #d89b28 0%, #e07b22 50%, #c85219 100%);
        color: #16243e;
    }
    header[data-testid="stHeader"] {background: transparent;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1250px;}

    .user-badge {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
    }
    .user-label {
        font-weight: 800;
        color: #16243e;
        font-size: 14px;
    }
    .user-pill {
        background-color: #16243e;
        color: #ffffff;
        padding: 8px 20px;
        border-radius: 30px;
        font-weight: 600;
        font-size: 14px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.18);
    }

    .pocket-card {
        background-color: #ffffff;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 128px;
    }
    .pocket-title {
        font-size: 12px;
        font-weight: 800;
        color: #16243e;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .pocket-amount {
        font-size: 28px;
        font-weight: 800;
        color: #c88214;
        line-height: 1.1;
    }
    .pocket-amount-box {
        border: 2px solid #e09f24;
        border-radius: 10px;
        padding: 2px 10px;
        display: inline-block;
        font-size: 26px;
        font-weight: 800;
        color: #c88214;
        margin: 2px 0;
    }
    .pocket-sub {
        font-size: 12px;
        color: #5a6577;
        margin-top: 4px;
        font-weight: 500;
    }
    .pocket-icon {
        background: linear-gradient(135deg, #f3b136, #d98218);
        color: #16243e;
        width: 46px;
        height: 46px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        flex-shrink: 0;
    }

    div.stButton > button {
        background-color: #16243e !important;
        color: #ffffff !important;
        border: 2px solid #2b3d5c !important;
        border-radius: 25px !important;
        font-weight: 700 !important;
        padding: 8px 10px !important;
        width: 100% !important;
        font-size: 13px !important;
    }
    div.stButton > button:hover {
        border-color: #f3b136 !important;
        color: #f3b136 !important;
    }

    div[class*="st-key-btn_in_big"] button {
        background-color: #0d9c66 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 18px !important;
        height: 128px !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        box-shadow: 0 8px 18px rgba(13,156,102,0.35) !important;
    }
    div[class*="st-key-btn_in_big"] button:hover {
        background-color: #0b8557 !important;
        color: #ffffff !important;
    }

    div[class*="st-key-btn_out_big"] button {
        background-color: #ba3b3b !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 18px !important;
        height: 128px !important;
        font-size: 20px !important;
        font-weight: 800 !important;
        box-shadow: 0 8px 18px rgba(186,59,59,0.35) !important;
    }
    div[class*="st-key-btn_out_big"] button:hover {
        background-color: #9e2f2f !important;
        color: #ffffff !important;
    }

    div[data-testid="stForm"] {
        background-color: #ffffff;
        border-radius: 18px;
        padding: 20px 24px;
        border: none;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    div[data-testid="stForm"] label {
        color: #16243e !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    div[data-testid="stFormSubmitButton"] button {
        background-color: #16243e !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 10px 20px !important;
        margin-top: 26px !important;
        width: 100% !important;
    }

    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #ffffff;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        font-size: 14px;
    }
    .custom-table thead {
        background-color: #16243e;
        color: #ffffff;
    }
    .custom-table th {
        padding: 14px 16px;
        text-align: left;
        font-weight: 700;
    }
    .custom-table td {
        padding: 12px 16px;
        border-bottom: 1px solid #eef1f5;
        color: #16243e;
        font-weight: 600;
    }
    .txt-gold {color: #d98218 !important; font-weight: 700;}
    .txt-green {color: #0d9c66 !important; font-weight: 700;}
    .txt-red {color: #ba3b3b !important; font-weight: 700;}
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
COLUMNAS = ["Fecha", "Tipo", "Categoría", "Bruto", "Peaje_1", "Peaje_9", "Monto_Neto", "Bolsillo"]
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
    
    # Blindaje contra URLs recortadas al copiar/pegar en el navegador
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
        {"Fecha": "26/11/2026", "Tipo": "Egreso", "Categoría": "Gasolina", "Bruto": 0, "Peaje_1": 0, "Peaje_9": 0, "Monto_Neto": -5000, "Bolsillo": "Efectivo Libre"},
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

# --- CÁLCULOS DEL SISTEMA BUCLE INFINITO ---
boveda_1 = abs(df["Peaje_1"].sum())
ingresos_9 = abs(df["Peaje_9"].sum())
egresos_9 = df[(df["Tipo"] == "Egreso") & (df["Bolsillo"] == "Fondo 9%")]["Monto_Neto"].sum()
fondo_9 = ingresos_9 + egresos_9

movs_libre = df[df["Bolsillo"] == "Efectivo Libre"]["Monto_Neto"].sum()
capital_invertido = abs(df[(df["Tipo"] == "Egreso") & (df["Bolsillo"] == "Fondo 9%") & (df["Categoría"] == "Enviar a Inversión")]["Monto_Neto"].sum())
abonos_deuda = abs(df[df["Categoría"] == "Deuda"]["Monto_Neto"].sum())

# --- ENCABEZADO DE USUARIO ---
estado_nube = "☁️ Google Sheets Conectado" if usar_google_sheets() else "💻 Modo Local"
st.markdown(f"""
<div class="user-badge">
    <span class="user-label">{estado_nube} &nbsp;|&nbsp; USUARIO</span>
    <div class="user-pill">👤 Edwin Alexander</div>
</div>
""", unsafe_allow_html=True)

# --- ESTRUCTURA PRINCIPAL ---
col_izq, col_der = st.columns([4.2, 1], gap="medium")

with col_izq:
    b1, b2, b3 = st.columns(3, gap="medium")
    with b1:
        st.markdown(f'<div class="pocket-card"><div><div class="pocket-title">BÓVEDA VITALICIA 1%</div><div class="pocket-amount">${boveda_1:,.0f}</div><div class="pocket-sub">Intocable</div></div><div class="pocket-icon">🔒</div></div>', unsafe_allow_html=True)
    with b2:
        st.markdown(f'<div class="pocket-card"><div><div class="pocket-title">FONDO 9%</div><div class="pocket-amount">${fondo_9:,.0f}</div><div class="pocket-sub">Emergencia e Inversión</div></div><div class="pocket-icon">🛡️</div></div>', unsafe_allow_html=True)
    with b3:
        st.markdown(f'<div class="pocket-card"><div><div class="pocket-title">EFECTIVO LIBRE</div><div class="pocket-amount-box">${movs_libre:,.0f}</div><div class="pocket-sub">Disponible tras peajes</div></div><div class="pocket-icon">👛</div></div>', unsafe_allow_html=True)

    st.write("")

    nav_cols = st.columns(6, gap="small")
    secciones = [
        ("Tablero", "🎛️ Tablero"),
        ("Editar", "✏️ Editar / Borrar"),
        ("Inversiones", "📈 Inversiones"),
        ("Deudas", "💳 Deudas"),
        ("Metas", "🏆 Metas"),
        ("Exportar", "📥 Exportar")
    ]
    for idx, (clave, etiqueta) in enumerate(secciones):
        with nav_cols[idx]:
            if st.button(etiqueta, key=f"nav_{clave}"):
                st.session_state.seccion_activa = clave
                st.rerun()

    st.write("")

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
                    btn_guardar = st.form_submit_button("💾 Guardar Cambios")
                with e5:
                    btn_borrar = st.form_submit_button("🗑️ Eliminar Fila")

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

with col_der:
    if st.button("➕ INGRESO", key="btn_in_big"):
        st.session_state.modo_registro = "INGRESO"
        st.session_state.seccion_activa = "Tablero"
        st.rerun()

    st.write("")

    if st.button("➖ EGRESO", key="btn_out_big"):
        st.session_state.modo_registro = "EGRESO"
        st.session_state.seccion_activa = "Tablero"
        st.rerun()

st.write("")

# --- TABLA INFERIOR CON ID ---
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

tabla_completa = f'<table class="custom-table"><thead><tr><th>ID</th><th>Fecha</th><th>Tipo</th><th>Categoría</th><th>1% Peaje</th><th>9% Peaje</th><th>Monto Neto</th><th>Bolsillo</th></tr></thead><tbody>{filas_html}</tbody></table>'
st.markdown(tabla_completa, unsafe_allow_html=True)
