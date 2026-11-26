CREATE TABLE orders (
  order_id TEXT NOT NULL PRIMARY KEY, customer_id TEXT NOT NULL,
  amount INTEGER, state TEXT
);
INSERT INTO orders VALUES
  ('O-001', 'C-001', 1200, '已交付'), ('O-002', 'C-001', 800, '生产中'),
  ('O-003', 'C-002', 300, '已交付'), ('O-004', 'C-002', 250, '待生产');
