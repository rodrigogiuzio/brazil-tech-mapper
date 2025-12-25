import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.set_page_config(page_title="Brazil Tech Mapper", layout="wide")

# --- CONEXÃO CVM ---
@st.cache_data(ttl=86400)
def get_cvm():
    try:
        url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
        r = requests.get(url, timeout=20)
        df = pd.read_csv(StringIO(r.content.decode("latin1")), sep=";", dtype=str)
        df['cnpj_raiz'] = df['CNPJ_CIA'].str.replace(r'\D', '', regex=True).str[:8]
        return df[['cnpj_raiz']].drop_duplicates()
    except: return pd.DataFrame(columns=['cnpj_raiz'])

# --- LOGICA DE SUBSEGMENTOS ---
def classificar(cnae):
    c = str(cnae)
    if c.startswith('6201'): return "Software/Dev"
    if c.startswith('6202'): return "Consultoria TI"
    if c.startswith('631'): return "Cloud/Dados"
    return "Outros Tech"

st.title("🗺️ Brazil Tech Mapper Pro")
cvm_raiz = get_cvm()

# --- SIDEBAR ---
st.sidebar.header("Configurações")
uploaded_file = st.sidebar.file_uploader("Suba o CSV do BigQuery", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['subsegmento'] = df['cnae_fiscal_principal'].apply(classificar)
    df['Eh_Listada'] = df['cnpj'].astype(str).str[:8].isin(cvm_raiz['cnpj_raiz'])
    
    # Filtros
    ufs = st.sidebar.multiselect("Estados", sorted(df['sigla_uf'].unique()), default=df['sigla_uf'].unique()[:5])
    subs = st.sidebar.multiselect("Subsegmentos", df['subsegmento'].unique(), default=df['subsegmento'].unique())
    
    df_f = df[(df['sigla_uf'].isin(ufs)) & (df['subsegmento'].isin(subs))]
    
    # Exibição
    st.metric("Empresas Encontradas", len(df_f))
    
    # Se o CSV tiver latitude/longitude, mostra o mapa
    if 'latitude' in df_f.columns:
        st.map(df_f)
    
    st.dataframe(df_f[['cnpj', 'nome_fantasia', 'subsegmento', 'nome_municipio', 'sigla_uf', 'Eh_Listada']], use_container_width=True)
else:
    st.info("Aguardando o arquivo CSV do BigQuery para gerar o mapa e a lista.")

