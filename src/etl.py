import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "data" / "system_extraction.xlsx"
SCHEMA = ROOT / "sql" / "schema.sql"
DB = ROOT / "db" / "vendas.db"

COLUNAS = {
    "Data": "data", "Nº pedido": "numero_pedido", "Vendedor": "vendedor",
    "Produto vendido": "produto", "Quantidade": "quantidade", "Preço": "preco",
    "Região": "regiao", "Cliente": "cliente", "Margem Lucro": "margem_lucro",
}


def carregar_planilha() -> pd.DataFrame:
    df = pd.read_excel(XLSX, engine="openpyxl", sheet_name="salesreport")
    df = df.rename(columns=COLUNAS)[list(COLUNAS.values())]
    df["data"] = pd.to_datetime(df["data"]).dt.strftime("%Y-%m-%d")
    for col in ("vendedor", "produto", "regiao", "cliente"):
        df[col] = df[col].astype(str).str.strip()
    if df["numero_pedido"].duplicated().any():
        raise ValueError("Há números de pedido duplicados na planilha.")
    return df


def main() -> None:
    df = carregar_planilha()
    DB.parent.mkdir(exist_ok=True)
    DB.unlink(missing_ok=True)  # evita duplicar linhas

    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))

    ids = {}
    for dim in ("vendedor", "cliente", "produto", "regiao"):
        nomes = sorted(df[dim].unique())
        con.executemany(f"INSERT INTO {dim}(nome) VALUES (?)", [(n,) for n in nomes])
        ids[dim] = dict(con.execute(f"SELECT nome, id FROM {dim}"))

    linhas = [
        (int(r.numero_pedido), r.data,
         ids["vendedor"][r.vendedor], ids["cliente"][r.cliente],
         ids["produto"][r.produto], ids["regiao"][r.regiao],
         int(r.quantidade), float(r.preco), float(r.margem_lucro))
        for r in df.itertuples(index=False)
    ]
    con.executemany(
        """INSERT INTO pedido(numero_pedido, data, vendedor_id, cliente_id,
                              produto_id, regiao_id, quantidade, preco, margem_lucro)
           VALUES (?,?,?,?,?,?,?,?,?)""", linhas)
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM pedido").fetchone()[0]
    con.close()
    print(f"Banco criado em {DB} com {total} pedidos.")


if __name__ == "__main__":
    main()