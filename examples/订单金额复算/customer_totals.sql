WITH customers(customer_id) AS (
  VALUES ('C-001'), ('C-002'), ('C-003')
), states(state, delivered) AS (
  VALUES ('已交付', 1), ('生产中', 0), ('待生产', 0)
), tally AS (
  SELECT c.customer_id,
         COUNT(CASE WHEN s.delivered = 1 THEN 1 END) AS matched,
         COUNT(CASE WHEN s.delivered = 1 AND o.amount IS NULL
                    THEN 1 END) AS missing,
         COUNT(o.order_id) - COUNT(s.state) AS unknown,
         SUM(CASE WHEN s.delivered = 1
                  THEN o.amount ELSE 0 END) AS subtotal
  FROM customers AS c
  LEFT JOIN orders AS o ON o.customer_id = c.customer_id
  LEFT JOIN states AS s ON s.state = o.state
  GROUP BY c.customer_id
)
SELECT customer_id, matched, missing, unknown,
       CASE WHEN missing = 0 AND unknown = 0
            THEN subtotal END AS delivered_amount
FROM tally ORDER BY customer_id;
