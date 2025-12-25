import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="Brazil Tech Mapper 100M", layout="wide")

# --- BUSCA DADOS DA BOLSA (CVM) ---
@st.cache_data(ttl=86400)
def load_cvm():
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    r = requests.get(url, timeout=20)
    df = pd.read_csv(StringIO(r.content.decode("latin1")), sep=";", dtype=str)
    df['cnpj_raiz'] = df['CNPJ_CIA'].str.replace(r'\D', '', regex=True).str[:8]
    return df[['cnpj_raiz']].drop_duplicates()

st.title("🗺️ Brazil Tech Mapper: Corporações R$ 100M+")
cvm = load_cvm()

# --- UPLOAD DO ARQUIVO ---
uploaded_file = st.sidebar.file_uploader("Suba o CSV do BigQuery", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['cnpj_raiz'] = df['cnpj'].astype(str).str.zfill(14).str[:8]
    df['Eh_Listada'] = df['cnpj_raiz'].isin(cvm['cnpj_raiz'])
    
    # Filtros
    st.sidebar.header("Filtros")
    uf_sel = st.sidebar.multiselect("Estados", sorted(df['sigla_uf'].unique()), default=df['sigla_uf'].unique())
    df_f = df[df['sigla_uf'].isin(uf_sel)]
    
    # KPIs
    c1, c2 = st.columns(2)
    c1.metric("Empresas (+100M)", len(df_f))
    c2.metric("Na Bolsa (B3)", len(df_f[df_f['Eh_Listada'] == True]))

    # Mapa - Streamlit precisa de colunas 'latitude' e 'longitude'
    st.subheader("Mapa de Sedes Corporativas")
    st.map(df_f[['latitude', 'longitude']])
    
    # Tabela
    st.subheader("Lista de Empresas")
    st.dataframe(df_f.sort_values('capital_social', ascending=False), use_container_width=True)
else:
    st.info("Aguardando upload do CSV do BigQuery.")
