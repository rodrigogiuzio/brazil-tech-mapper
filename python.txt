import re
import pandas as pd
import streamlit as st
import requests
from io import StringIO

st.set_page_config(page_title="Brazil Tech Mapper", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
def digits_only(x: str) -> str:
    if x is None:
        return ""
    return re.sub(r"\D", "", str(x))

def to_cnpj_root_8(x: str) -> str:
    d = digits_only(x)
    if len(d) >= 8:
        return d[:8]
    return d.zfill(8) if d else ""

def norm_cnae(x: str) -> str:
    return digits_only(x)

def best_name(row: pd.Series) -> str:
    nf = str(row.get("nome_fantasia", "") or "").strip()
    rs = str(row.get("razao_social", "") or "").strip()
    return nf if nf and nf.lower() != "nan" else rs

def contains_any(text: str, keywords: list[str]) -> bool:
    t = (text or "").lower()
    return any(k in t for k in keywords)

# -----------------------------
# CVM download (Listed BR)
# -----------------------------
CVM_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"

@st.cache_data(ttl=24*3600, show_spinner=False) def load_cvm_cia_aberta() -> pd.DataFrame:
    r = requests.get(CVM_URL, timeout=60)
    r.raise_for_status()
    # CVM costuma vir com separador ';' e encoding latin1
    text = r.content.decode("latin1", errors="ignore")
    df = pd.read_csv(StringIO(text), sep=";", dtype=str)
    # tenta achar coluna de CNPJ
    cnpj_col = None
    for c in df.columns:
        if "CNPJ" in c.upper():
            cnpj_col = c
            break
    if cnpj_col is None:
        raise ValueError("Não achei coluna de CNPJ no arquivo da CVM.")
    df["cnpj_basico"] = df[cnpj_col].apply(to_cnpj_root_8)
    df = df[df["cnpj_basico"].str.len() == 8]
    return df[["cnpj_basico"]].drop_duplicates()

# -----------------------------
# Tech scope + Subsegment classifier
# -----------------------------
CORE_TECH_CNAE_PREFIXES = ("5820", "62", "63")

KEYWORDS = {
    "Fintech / Payments": ["pag", "payment", "pix", "wallet", "carteira", "adquir", "gateway", "bank", "banco", "cartao", "crédito", "credito", "fidc"],
    "Cybersecurity": ["cyber", "security", "segur", "iam", "siem", "soc", "antifraude", "fraud", "endpoint", "waf"],
    "Data / AI / Cloud": ["cloud", "nuvem", "data", "dados", "analytics", "bi ", "machine learning", "ml", "ai", "ia", "lake", "warehouse"],
    "Internet / Marketplace": ["marketplace", "e-commerce", "ecommerce", "delivery", "app", "plataforma", "classificados", "rides", "mobility", "logtech"],
    "Software Vertical — HCM": ["hcm", "rh", "folha", "ponto", "beneficios", "benefícios", "admiss", "onboarding", "offboarding"],
    "Software Vertical — Health": ["saude", "saúde", "clinic", "hospital", "med", "prontuario", "prontuário", "health"],
    "Software Vertical — EdTech": ["educ", "ead", "school", "lms", "edtech", "univers", "aluno", "curso"],
    "Software Vertical — Legal/RegTech": ["jurid", "juríd", "legal", "regtech", "compliance", "kya", "kyc", "pld", "aml"],
    "Software Vertical — Retail/Commerce": ["pdv", "varejo", "retail", "commerce", "erp", "fiscal", "nota", "checkout"],
    "Software Vertical — Agro": ["agro", "safra", "fazenda", "rural", "pecu", "pecuária", "grain", "crop"],
    "Software Horizontal": ["crm", "helpdesk", "ticket", "devops", "observability", "saas", "workflow", "low-code", "nocode", "hris", "api", "integration", "integracao", "integração"], }

def tech_in_scope(row: pd.Series) -> bool:
    cnae = norm_cnae(row.get("cnae_fiscal_principal", ""))
    name = best_name(row)
    if cnae.startswith(CORE_TECH_CNAE_PREFIXES):
        return True
    # fallback por keyword (quando CNAE faltar)
    tech_kw = ["software", "saas", "cloud", "dados", "data", "cyber", "security", "pag", "payment", "pix", "app", "plataforma"]
    return contains_any(name, tech_kw)

def classify_subsegment(row: pd.Series) -> str:
    cnae = norm_cnae(row.get("cnae_fiscal_principal", ""))
    name = best_name(row)

    # Heurística por CNAE primeiro (bem simples)
    if cnae.startswith(("64", "66", "6619")):
        return "Fintech / Payments"
    if cnae.startswith("63"):
        # pode ser dados/internet; decide por keyword
        if contains_any(name, KEYWORDS["Data / AI / Cloud"]):
            return "Data / AI / Cloud"
        if contains_any(name, KEYWORDS["Internet / Marketplace"]):
            return "Internet / Marketplace"
        return "Data / AI / Cloud"

    # Keyword matching (ordem importa)
    order = [
        "Fintech / Payments",
        "Cybersecurity",
        "Data / AI / Cloud",
        "Internet / Marketplace",
        "Software Vertical — HCM",
        "Software Vertical — Health",
        "Software Vertical — EdTech",
        "Software Vertical — Legal/RegTech",
        "Software Vertical — Retail/Commerce",
        "Software Vertical — Agro",
        "Software Horizontal",
    ]
    for label in order:
        if contains_any(name, KEYWORDS[label]):
            return label

    # Se for 58/62 e não pegou por keyword: assume software horizontal
    if cnae.startswith(("5820", "62")):
        return "Software Horizontal"

    return "Other Tech"

# -----------------------------
# Demo data
# -----------------------------
def demo_df() -> pd.DataFrame:
    data = [
        {"cnpj": "00000000000100", "razao_social": "Demo Payments S.A.", "nome_fantasia": "DemoPay", "uf": "SP", "municipio": "São Paulo", "situacao_cadastral": "ATIVA", "cnae_fiscal_principal": "6619302"},
        {"cnpj": "11111111000111", "razao_social": "Demo HCM Ltda", "nome_fantasia": "DemoRH", "uf": "MG", "municipio": "Belo Horizonte", "situacao_cadastral": "ATIVA", "cnae_fiscal_principal": "6201501"},
        {"cnpj": "22222222000122", "razao_social": "Demo Cyber Segurança", "nome_fantasia": "DemoCyber", "uf": "RJ", "municipio": "Rio de Janeiro", "situacao_cadastral": "ATIVA", "cnae_fiscal_principal": "6204000"},
        {"cnpj": "33333333000133", "razao_social": "Demo Data Cloud", "nome_fantasia": "DemoCloud", "uf": "SP", "municipio": "Campinas", "situacao_cadastral": "ATIVA", "cnae_fiscal_principal": "6311900"},
    ]
    return pd.DataFrame(data)

# -----------------------------
# UI
# -----------------------------
st.title("🇧🇷 Brazil Tech Mapper")

with st.sidebar:
    st.header("Dados")
    mode = st.radio("Fonte", ["Demo", "Upload CSV"], horizontal=False)
    use_cvm = st.toggle("Marcar listadas (CVM)", value=True)
    only_tech = st.toggle("Mostrar só tech_in_scope", value=True)

df = demo_df() if mode == "Demo" else None

if mode == "Upload CSV":
    up = st.file_uploader("Envie um CSV com CNPJ + (opcional) CNAE", type=["csv"])
    if up is not None:
        df = pd.read_csv(up, dtype=str)

if df is None:
    st.info("Selecione Demo ou envie um CSV para começar.")
    st.stop()

# Normaliza colunas possíveis
cols_lower = {c.lower(): c for c in df.columns} def get_col(*candidates):
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None

cnpj_col = get_col("cnpj_basico", "cnpj_raiz", "cnpj") razao_col = get_col("razao_social", "razao", "nome") fant_col = get_col("nome_fantasia", "fantasia") uf_col = get_col("uf", "estado") mun_col = get_col("municipio", "cidade") sit_col = get_col("situacao_cadastral", "situacao") cnae_col = get_col("cnae_fiscal_principal", "cnae")

# cria colunas padrão
if cnpj_col is None:
    st.error("Não encontrei coluna de CNPJ. Inclua 'cnpj' ou 'cnpj_basico'.")
    st.stop()

df["cnpj_basico"] = df[cnpj_col].apply(to_cnpj_root_8)
df["razao_social"] = df[razao_col] if razao_col else ""
df["nome_fantasia"] = df[fant_col] if fant_col else ""
df["uf"] = df[uf_col] if uf_col else ""
df["municipio"] = df[mun_col] if mun_col else ""
df["situacao_cadastral"] = df[sit_col] if sit_col else ""
df["cnae_fiscal_principal"] = df[cnae_col] if cnae_col else ""

# flags e classificação
df["tech_in_scope"] = df.apply(tech_in_scope, axis=1) df["subsegment"] = df.apply(classify_subsegment, axis=1)

# listed BR
df["listed_br"] = False
if use_cvm:
    try:
        cvm = load_cvm_cia_aberta()
        df["listed_br"] = df["cnpj_basico"].isin(set(cvm["cnpj_basico"]))
    except Exception as e:
        st.warning(f"Não consegui baixar/processar a base da CVM agora. Erro: {e}")

# filtros
work = df.copy()
if only_tech:
    work = work[work["tech_in_scope"] == True]

c1, c2, c3, c4 = st.columns(4)
with c1:
    listed_filter = st.selectbox("Listed (Brasil)", ["All", "Listed", "Not listed"]) with c2:
    subs = sorted(work["subsegment"].dropna().unique().tolist())
    sub_filter = st.multiselect("Subsegmento", subs, default=subs) with c3:
    ufs = sorted([x for x in work["uf"].dropna().unique().tolist() if str(x).strip()])
    uf_filter = st.multiselect("UF", ufs, default=ufs) with c4:
    sts = sorted([x for x in work["situacao_cadastral"].dropna().unique().tolist() if str(x).strip()])
    st_filter = st.multiselect("Status", sts, default=sts)

search = st.text_input("Buscar (nome/razão/fantasia)", "")

if listed_filter != "All":
    want = (listed_filter == "Listed")
    work = work[work["listed_br"] == want]

if sub_filter:
    work = work[work["subsegment"].isin(sub_filter)]

if uf_filter:
    work = work[work["uf"].isin(uf_filter)]

if st_filter:
    work = work[work["situacao_cadastral"].isin(st_filter)]

if search.strip():
    s = search.strip().lower()
    work = work[
        work["razao_social"].astype(str).str.lower().str.contains(s, na=False)
        | work["nome_fantasia"].astype(str).str.lower().str.contains(s, na=False)
    ]

# outputs
st.subheader("Resumo (contagem por subsegmento)") summary = work.groupby("subsegment", dropna=False).size().reset_index(name="count").sort_values("count", ascending=False) st.dataframe(summary, use_container_width=True, hide_index=True)

st.subheader("Empresas")
out_cols = ["cnpj_basico","razao_social","nome_fantasia","tech_in_scope","subsegment","uf","municipio","situacao_cadastral","listed_br","cnae_fiscal_principal"]
st.dataframe(work[out_cols], use_container_width=True, hide_index=True)

csv_bytes = work[out_cols].to_csv(index=False).encode("utf-8")
st.download_button("Download CSV (mapeado + filtrado)", data=csv_bytes, file_name="brazil_tech_mapped_filtered.csv", mime="text/csv")
