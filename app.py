import streamlit as st
import pandas as pd
import re
import requests
from io import StringIO

# Configuração da página sempre em primeiro st.set_page_config(page_title="Brazil Tech Mapper", layout="wide")

st.title("🇧🇷 Brazil Tech Mapper")

# 1. CRIAR O DF LOGO NO INÍCIO (Garante que st.dataframe(df) funcione) data = [{"cnpj": "00.000.000/0001-00", "razao_social": "Empresa Exemplo S.A.", "uf": "SP", "status": "ATIVA"}] df = pd.DataFrame(data)

st.write("### Painel de Controle")
st.write("O site carregou com sucesso! Use o menu lateral para gerenciar os dados.")

# Exibe o dataframe inicial
st.dataframe(df, use_container_width=True)

# 2. FUNÇÕES DE APOIO
def digits_only(x):
    return re.sub(r"\D", "", str(x)) if x else ""

@st.cache_data(ttl=3600)
def load_cvm():
    try:
        url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
        r = requests.get(url, timeout=10)
        df_cvm = pd.read_csv(StringIO(r.content.decode("latin1")), sep=";", dtype=str)
        return df_cvm
    except:
        return None

# 3. TENTAR CARREGAR CVM
cvm_data = load_cvm()
if cvm_data is not None:
    st.success(f"Conectado à base da CVM! {len(cvm_data)} empresas listadas encontradas.")
else:
    st.info("Aguardando conexão com servidor da CVM ou operando em modo offline.")

st.sidebar.header("Configurações")
st.sidebar.file_uploader("Upload de CSV", type=["csv"])
