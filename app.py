import re
import pandas as pd
import streamlit as st
import requests
from io import StringIO

st.set_page_config(page_title="Brazil Tech Mapper", layout="wide")

def digits_only(x):
    return re.sub(r"\D", "", str(x)) if x else ""

def to_cnpj_root_8(x):
    d = digits_only(x)
    return d[:8] if len(d) >= 8 else d.zfill(8) if d else ""

@st.cache_data(ttl=86400)
def load_cvm_cia_aberta():
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    r = requests.get(url, timeout=60)
    text = r.content.decode("latin1", errors="ignore")
    df = pd.read_csv(StringIO(text), sep=";", dtype=str)
    df["cnpj_basico"] = df["CNPJ_CIA"].apply(to_cnpj_root_8)
    return df[["cnpj_basico"]].drop_duplicates()

def contains_any(text, keywords):
    t = str(text or "").lower()
    return any(k in t for k in keywords)

# --- Classificação simplificada ---
def classify_tech(row):
    name = str(row.get("nome_fantasia", "") or row.get("razao_social", "")).lower()
    if contains_any(name, ["pay", "bank", "credito", "pagamento"]): return "Fintech"
    if contains_any(name, ["software", "cloud", "saas", "tech"]): return "Software"
    return "Outros Tech"

st.title("🇧🇷 Brazil Tech Mapper")

# Dados de exemplo para o site não abrir vazio data = [{"cnpj": "00000000000100", "razao_social": "Exemplo Tech S.A.", "uf": "SP", "situacao_cadastral": "ATIVA"}] df = pd.DataFrame(data)

st.write("Site carregado com sucesso! Use o menu lateral para subir seu CSV.")
st.dataframe(df)

try:
    cvm = load_cvm_cia_aberta()
    st.success("Base da CVM conectada!")
except:
    st.warning("Aguardando conexão com base CVM...")
