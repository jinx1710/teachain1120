-- 門市
CREATE TABLE IF NOT EXISTS branches (
    branch_id   SERIAL PRIMARY KEY,
    branch_name VARCHAR(100) NOT NULL,
    city        VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO branches (branch_id, branch_name, city) VALUES
    (1, 'Taoyuan Branch',  'Taoyuan'),
    (2, 'Taipei Branch',   'Taipei'),
    (3, 'Taichung Branch', 'Taichung'),
    (4, 'Tainan Branch',   'Tainan')
ON CONFLICT (branch_id) DO NOTHING;

-- 讓 SERIAL 從 5 開始，避免之後新增門市時撞號
SELECT setval('branches_branch_id_seq', (SELECT MAX(branch_id) FROM branches));

-- 使用者（owner 不屬於任何門市，branch_id 為 NULL）
CREATE TABLE IF NOT EXISTS users (
    user_id       SERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100) NOT NULL,
    role          VARCHAR(20)  NOT NULL CHECK (role IN ('owner', 'manager')),
    branch_id     INTEGER REFERENCES branches(branch_id),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
