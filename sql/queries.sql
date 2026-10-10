SELECT vendedor,
       COUNT(*)                                        AS pedidos,
       ROUND(SUM(valor_pedido), 2)                     AS faturamento,
       ROUND(SUM(margem_lucro), 2)                     AS lucro,
       ROUND(100.0 * SUM(margem_lucro) / SUM(valor_pedido), 1) AS margem_pct
FROM vw_vendas
GROUP BY vendedor
ORDER BY faturamento DESC;

SELECT regiao, produto, faturamento,
       RANK() OVER (PARTITION BY regiao ORDER BY faturamento DESC) AS posicao
FROM (
    SELECT regiao, produto, ROUND(SUM(valor_pedido), 2) AS faturamento
    FROM vw_vendas
    GROUP BY regiao, produto
)
ORDER BY regiao, posicao;

WITH mensal AS (
    SELECT strftime('%Y-%m', data) AS mes,
           ROUND(SUM(valor_pedido), 2) AS faturamento
    FROM vw_vendas
    GROUP BY mes
)
SELECT mes, faturamento,
       ROUND(SUM(faturamento) OVER (ORDER BY mes), 2) AS acumulado
FROM mensal
ORDER BY mes;

SELECT cliente,
       ROUND(AVG(valor_pedido), 2) AS ticket_medio
FROM vw_vendas
GROUP BY cliente
HAVING AVG(valor_pedido) > (SELECT AVG(valor_pedido) FROM vw_vendas)
ORDER BY ticket_medio DESC;

WITH vendas_mes AS (
    SELECT strftime('%Y-%m', data) AS mes, vendedor,
           ROUND(SUM(valor_pedido), 2) AS faturamento
    FROM vw_vendas
    GROUP BY mes, vendedor
)
SELECT mes, vendedor, faturamento
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY mes ORDER BY faturamento DESC) AS rn
    FROM vendas_mes
)
WHERE rn = 1
ORDER BY mes;