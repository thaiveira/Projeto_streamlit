import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
DB = ROOT / "db" / "vendas.db"
SQL_DIR = ROOT / "sql"

st.set_page_config(
    page_title="Dashboard de Vendas · Banco de Dados",
    page_icon="💲",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def conectar() -> sqlite3.Connection:
    if not DB.exists():  
        subprocess.run([sys.executable, str(ROOT / "src" / "etl.py")], check=True)
    return sqlite3.connect(f"{DB.as_uri()}?mode=ro", uri=True, check_same_thread=False)


@st.cache_data
def consulta(sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conectar(), params=list(params))


def montar_where(filtros: dict, ini: str, fim: str) -> tuple[str, tuple]:
    clausulas, params = ["data BETWEEN ? AND ?"], [ini, fim]
    for coluna, valores in filtros.items():
        clausulas.append(f"{coluna} IN ({','.join('?' * len(valores))})")
        params += valores
    return " AND ".join(clausulas), tuple(params)


limites = consulta("SELECT MIN(data) AS ini, MAX(data) AS fim FROM vw_vendas").iloc[0]
data_min, data_max = pd.to_datetime(limites["ini"]).date(), pd.to_datetime(limites["fim"]).date()


def opcoes(coluna: str) -> list[str]:
    return consulta(f"SELECT DISTINCT {coluna} AS v FROM vw_vendas ORDER BY 1")["v"].tolist()


with st.sidebar:
    st.subheader("Filtros")
    vendedores = st.multiselect("Vendedor", opcoes("vendedor"), default=opcoes("vendedor"))
    clientes = st.multiselect("Cliente", opcoes("cliente"), default=opcoes("cliente"))
    produtos = st.multiselect("Produto", opcoes("produto"), default=opcoes("produto"))
    regioes = st.multiselect("Região", opcoes("regiao"), default=opcoes("regiao"))
    periodo = st.date_input("Período", value=(data_min, data_max),
                            min_value=data_min, max_value=data_max)

if not isinstance(periodo, tuple) or len(periodo) != 2:
    st.info("Selecione a data inicial e a final no filtro de período.")
    st.stop()
if not all([vendedores, clientes, produtos, regioes]):
    st.warning("Selecione ao menos uma opção em cada filtro.")
    st.stop()

where, params = montar_where(
    {"vendedor": vendedores, "cliente": clientes, "produto": produtos, "regiao": regioes},
    periodo[0].isoformat(), periodo[1].isoformat(),
)

tab_dash, tab_sql, tab_modelo = st.tabs(["📊 Dashboard", "🧮 SQL ao vivo", "🗄️ Modelo do banco"])

with tab_dash:
    st.header(":bar_chart: Dashboard de Vendas")

    kpi = consulta(
        f"""SELECT COALESCE(SUM(valor_pedido), 0) AS vendas,
                   COALESCE(SUM(margem_lucro), 0) AS lucro,
                   COUNT(*) AS pedidos
            FROM vw_vendas WHERE {where}""", params).iloc[0]

    if kpi["pedidos"] == 0:
        st.warning("Nenhum pedido para os filtros escolhidos.")
        st.stop()

    margem = 100 * kpi["lucro"] / kpi["vendas"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Vendas totais", f"R$ {kpi['vendas']:,.2f}")
    k2.metric("Total de lucro", f"R$ {kpi['lucro']:,.2f}")
    k3.metric("Margem média", f"{margem:.1f} %")
    k4.metric("Pedidos", f"{int(kpi['pedidos']):,}")

    def agrupar(expressao: str, apelido: str) -> pd.DataFrame:
        return consulta(
            f"""SELECT {expressao} AS {apelido},
                       SUM(quantidade) AS quantidade,
                       ROUND(SUM(valor_pedido), 2) AS valor_pedido
                FROM vw_vendas WHERE {where}
                GROUP BY 1 ORDER BY 1""", params)

    por_produto = agrupar("produto", "produto")
    por_cliente = agrupar("cliente", "cliente")
    por_vendedor = agrupar("vendedor", "vendedor")
    por_regiao = agrupar("regiao", "regiao")
    por_mes = agrupar("strftime('%Y-%m', data)", "mes")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.altair_chart(
            alt.Chart(por_produto, title="Quantidade vendida por produto")
            .mark_bar(color="#9DD1F1")
            .encode(x="produto:N", y="quantidade:Q", tooltip=["produto", "quantidade"]),
            use_container_width=True)
        st.altair_chart(
            alt.Chart(por_produto, title="Valor total por produto")
            .mark_bar(color="#9DD1F1")
            .encode(x="produto:N", y="valor_pedido:Q", tooltip=["produto", "valor_pedido"]),
            use_container_width=True)
    with c2:
        st.altair_chart(
            alt.Chart(por_cliente, title="Valor vendido por cliente")
            .mark_bar(color="#666", cornerRadiusTopLeft=9, cornerRadiusBottomRight=9)
            .encode(x=alt.X("cliente:N", sort="-y"), y="valor_pedido:Q",
                    tooltip=["cliente", "quantidade", "valor_pedido"]),
            use_container_width=True)
        st.altair_chart(
            alt.Chart(por_mes, title="Vendas mensais")
            .mark_line(color="#666", point=True)
            .encode(x=alt.X("mes:O", title="Mês"), y="valor_pedido:Q",
                    tooltip=["mes", "valor_pedido"]),
            use_container_width=True)
    with c3:
        st.altair_chart(
            alt.Chart(por_vendedor, title="Valor de venda por vendedor")
            .mark_arc(innerRadius=70, outerRadius=120)
            .encode(theta="valor_pedido:Q", color="vendedor:N",
                    tooltip=["vendedor", "valor_pedido"]),
            use_container_width=True)
        st.altair_chart(
            alt.Chart(por_regiao, title="Valor de venda por região")
            .mark_bar(color="#9DD1F1")
            .encode(y=alt.Y("regiao:N", sort="-x"), x="valor_pedido:Q",
                    tooltip=["regiao", "valor_pedido"]),
            use_container_width=True)

with tab_sql:
    st.write("Consultas do arquivo `sql/queries.sql`. A conexão é **somente leitura**: "
             "você pode editar e executar à vontade.")
    texto = (SQL_DIR / "queries.sql").read_text(encoding="utf-8")
    partes = re.split(r"^-- name:\s*(.+)$", texto, flags=re.M)[1:]
    consultas = dict(zip(partes[::2], (p.strip() for p in partes[1::2])))

    nome = st.selectbox("Consulta", list(consultas))
    sql = st.text_area("SQL", consultas[nome], height=240)
    if st.button("Executar", type="primary"):
        try:
            st.dataframe(pd.read_sql_query(sql.strip().rstrip(";"), conectar()),
                         use_container_width=True, hide_index=True)
        except Exception as erro:
            st.error(f"Erro na consulta: {erro}")

with tab_modelo:
    st.subheader("Diagrama entidade-relacionamento")
    st.graphviz_chart("""
    digraph ER {
      rankdir=LR; node [shape=record, fontname="Helvetica"];
      pedido   [label="{pedido|numero_pedido (PK)\\ldata\\lquantidade\\lpreco\\lmargem_lucro\\lvendedor_id (FK)\\lcliente_id (FK)\\lproduto_id (FK)\\lregiao_id (FK)\\l}"];
      vendedor [label="{vendedor|id (PK)\\lnome\\l}"];
      cliente  [label="{cliente|id (PK)\\lnome\\l}"];
      produto  [label="{produto|id (PK)\\lnome\\l}"];
      regiao   [label="{regiao|id (PK)\\lnome\\l}"];
      vendedor -> pedido [label="1:N"]; cliente -> pedido [label="1:N"];
      produto  -> pedido [label="1:N"]; regiao  -> pedido [label="1:N"];
    }""")
    st.subheader("Script de criação (`sql/schema.sql`)")
    st.code((SQL_DIR / "schema.sql").read_text(encoding="utf-8"), language="sql")