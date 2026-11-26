WITH sample_orders(order_id, customer_id, amount_wan, sample_status) AS (
  VALUES ('O-001', 'C-001', 1200, '已交付'),
         ('O-002', 'C-001', 800, '生产中'),
         ('O-003', 'C-002', 300, '已交付'),
         ('O-004', 'C-002', 250, '待生产'),
         ('O-005', 'C-003', 150, '已交付')
)
SELECT customer_id,
       SUM(amount_wan) AS signed_amount_wan,
       SUM(CASE WHEN sample_status = '已交付'
                THEN amount_wan ELSE 0 END) AS delivered_amount_wan
FROM sample_orders
GROUP BY customer_id
ORDER BY customer_id;
