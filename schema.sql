CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    login       TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL CHECK(role IN ('manager','employee')),
    employee_id INTEGER REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS employees (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    fname    TEXT NOT NULL,
    lname    TEXT NOT NULL,
    dept     TEXT NOT NULL,
    position TEXT NOT NULL,
    since    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    title       TEXT NOT NULL,
    description TEXT DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','done')),
    created_at  TEXT NOT NULL,
    done_at     TEXT
);

CREATE TABLE IF NOT EXISTS kpis (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    metric      TEXT NOT NULL,
    score       INTEGER NOT NULL CHECK(score BETWEEN 1 AND 100),
    comment     TEXT DEFAULT '',
    date        TEXT NOT NULL
);

-- Seed data
INSERT OR IGNORE INTO employees (id,fname,lname,dept,position,since) VALUES
(1,'Алексей','Петров','Онлайн работники','Маркетолог','2022-03'),
(2,'Мария','Сидорова','Онлайн работники','Бухгалтер','2021-07'),
(3,'Дмитрий','Козлов','Офлайн работники','Водитель','2023-01'),
(4,'Елена','Новикова','Онлайн работники','Системный администратор','2022-11'),
(5,'Игорь','Смирнов','Офлайн работники','Механик','2020-05');

-- admin123 => 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a
-- pass123  => 9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684716eb55f3b6c3a33b384d0c4
INSERT OR IGNORE INTO users (login,password,name,role,employee_id) VALUES
('admin',   '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9','Администратор','manager',NULL),
('employee1','9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684716eb55f3b6c3a33b384d0c4','Алексей Петров','employee',1),
('employee2','9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684716eb55f3b6c3a33b384d0c4','Мария Сидорова','employee',2);

INSERT OR IGNORE INTO kpis (employee_id,metric,score,comment,date) VALUES
(1,'Выполнение задач',92,'Отличная работа','2024-04-01'),
(1,'Качество работы',88,'','2024-04-05'),
(2,'Коммуникация',75,'Нужно улучшить','2024-04-03'),
(3,'Инициативность',60,'','2024-04-02'),
(4,'Дисциплина',95,'Пример для коллег','2024-04-06'),
(5,'Выполнение задач',82,'','2024-04-04'),
(2,'Выполнение задач',78,'','2024-04-07'),
(3,'Качество работы',55,'Есть замечания','2024-03-30');