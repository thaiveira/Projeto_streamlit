PRAGMA foreign_keys = ON;

CREATE TABLE vendedor (
    id   INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE cliente (
    id   INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE produto (
    id   INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE regiao (
    id   INTEGER PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE pedido (
    numero_pedido INTEGER PRIMARY KEY,
    data          TEXT    NOT NULL,     -- AAAA-MM-DD
    vendedor_id   INTEGER NOT NULL REFERENCES vendedor(id),
    cliente_id    INTEGER NOT NULL REFERENCES cliente(id),
    produto_id    INTEGER NOT NULL REFERENCES produto(id),
    regiao_id     INTEGER NOT NULL REFERENCES regiao(id),
    quantidade    INTEGER NOT NULL CHECK (quantidade > 0),
    preco         REAL    NOT NULL CHECK (preco > 0),
    margem_lucro  REAL    NOT NULL
);

CREATE INDEX idx_pedido_data     ON pedido(data);
CREATE INDEX idx_pedido_vendedor ON pedido(vendedor_id);
CREATE INDEX idx_pedido_cliente  ON pedido(cliente_id);
CREATE INDEX idx_pedido_produto  ON pedido(produto_id);

-- Valor do pedido fica na view
CREATE VIEW vw_vendas AS
SELECT p.numero_pedido,
       p.data,
       v.nome AS vendedor,
       c.nome AS cliente,
       pr.nome AS produto,
       r.nome AS regiao,
       p.quantidade,
       p.preco,
       ROUND(p.quantidade * p.preco, 2) AS valor_pedido,
       p.margem_lucro
FROM pedido p
JOIN vendedor v ON v.id = p.vendedor_id
JOIN cliente  c ON c.id = p.cliente_id
JOIN produto pr ON pr.id = p.produto_id
JOIN regiao   r ON r.id = p.regiao_id;