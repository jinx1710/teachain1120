
CREATE TABLE IF NOT EXISTS branches (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  city VARCHAR(80) NOT NULL,
  description TEXT DEFAULT '',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(60) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  role VARCHAR(20) NOT NULL
    CHECK (role IN ('owner','manager','staff')),
  branch_id INTEGER REFERENCES branches(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  description TEXT DEFAULT '',
  price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
  branch_id INTEGER REFERENCES branches(id),
  is_shared BOOLEAN NOT NULL DEFAULT TRUE,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  user_id INTEGER REFERENCES users(id),
  total NUMERIC(10,2) NOT NULL CHECK (total >= 0),
  status VARCHAR(20) NOT NULL DEFAULT 'completed',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
  id SERIAL PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES orders(id)
    ON DELETE CASCADE,
  product_id INTEGER NOT NULL REFERENCES products(id),
  product_name VARCHAR(120) NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price NUMERIC(10,2) NOT NULL,
  subtotal NUMERIC(10,2) NOT NULL
);

-- 6 chi nhánh
INSERT INTO branches (id,name,city,description) VALUES
(1,'桃園一店 - Chi nhánh Đào Viên 1','Taoyuan','Chi nhánh Đào Viên 1'),
(2,'台北店 - Chi nhánh Đài Bắc','Taipei','Chi nhánh Đài Bắc'),
(3,'台中店 - Chi nhánh Đài Trung','Taichung','Chi nhánh Đài Trung'),
(4,'台南店 - Chi nhánh Đài Nam','Tainan','Chi nhánh Đài Nam'),
(5,'桃園二店 - Chi nhánh Đào Viên 2','Taoyuan','Chi nhánh Đào Viên 2'),
(6,'桃園三店 - Chi nhánh Đào Viên 3','Taoyuan','Chi nhánh Đào Viên 3')
ON CONFLICT (id) DO NOTHING;

-- 5 món chung cho tất cả chi nhánh
INSERT INTO products (name,description,price,branch_id,is_shared) VALUES
('開心奶茶 - Trà sữa vui vẻ','傳統奶茶 - Trà sữa truyền thống',70,NULL,TRUE),
('快樂紅茶 - Hồng trà vui vẻ','紅茶 - Hồng trà',55,NULL,TRUE),
('烏龍綠茶 - Trà ô long xanh','烏龍綠茶 - Trà ô long xanh',60,NULL,TRUE),
('茉莉花茶 - Trà hoa nhài','茉莉花茶 - Trà hoa nhài',70,NULL,TRUE),
('甘蔗青茶 - Trà mía xanh','甘蔗青茶 - Trà mía xanh',65,NULL,TRUE)
ON CONFLICT DO NOTHING;

-- Món đặc biệt riêng của từng chi nhánh
INSERT INTO products (name,description,price,branch_id,is_shared) VALUES
('桃園特色飲品 - Đồ uống đặc biệt Đào Viên',
 '桃園限定水果茶 - Trà trái cây đặc biệt Đào Viên',85,1,FALSE),

('台北特色飲品 - Đồ uống đặc biệt Đài Bắc',
 '海鹽奶蓋奶茶 - Trà sữa kem muối biển',90,2,FALSE),

('台中特色飲品 - Đồ uống đặc biệt Đài Trung',
 '蜜桃烏龍茶 - Trà ô long đào',85,3,FALSE),

('台南特色飲品 - Đồ uống đặc biệt Đài Nam',
 '蜂蜜檸檬茶 - Trà chanh mật ong',80,4,FALSE),

('桃園二店特色飲品 - Đồ uống đặc biệt Đào Viên 2',
 '新鮮草莓茶 - Trà dâu tươi',90,5,FALSE),

('桃園三店特色飲品 - Đồ uống đặc biệt Đào Viên 3',
 '荔枝茉莉花茶 - Trà vải hoa nhài',85,6,FALSE)
ON CONFLICT DO NOTHING;
