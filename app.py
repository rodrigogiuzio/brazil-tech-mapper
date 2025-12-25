import streamlit as st
import pandas as pd
import requests
from io import StringIO

# 1. CONFIGURAÇÃO INICIAL (Sempre no topo) st.set_page_config(page_title="Brazil Tech Mapper", layout="wide")

# 2. CRIAÇÃO DO DF (Garante que a variável 'df' sempre exista) # Criamos um dataframe vazio ou com um exemplo para o site não quebrar data_inicial = [{"CNPJ": "00.000.000/0001-00", "Razão Social": "Carregando...", "Status": "Ativo"}] df = pd.DataFrame(data_inicial)

# 3. INTERFACE DO SITE
st.title("🇧🇷 Brazil Tech Mapper")
st.write("### Painel de Controle")

# Agora o comando abaixo NUNCA vai dar NameError porque o 'df' foi definido na linha 12 st.dataframe(df, use_container_width=True)

# 4. FUNÇÃO PARA CARREGAR DADOS DA CVM
@st.cache_data(ttl=3600)
def carregar_cvm():
    try:
        url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
        response = requests.get(url, timeout=10)
        # Tenta ler os dados da CVM
        cvm = pd.read_csv(StringIO(response.content.decode("latin1")), sep=";", dtype=str)
        return cvm
    except Exception as e:
        return None

# 5. TENTAR ATUALIZAR OS DADOS
cvm_df = carregar_cvm()

if cvm_df is not None:
    st.success(f"Conectado à base da CVM! {len(cvm_df)} empresas encontradas.")
    # Se quiser mostrar os dados da CVM na tela:
    # st.dataframe(cvm_df.head(10))
else:
    st.warning("Aguardando conexão com a base da CVM...")

st.sidebar.header("Filtros e Upload")
st.sidebar.file_uploader("Subir seu arquivo CSV", type=["csv"])
