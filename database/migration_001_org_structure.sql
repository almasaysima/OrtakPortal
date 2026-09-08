-- =========================================================
-- ORGANİZASYON YAPISI
-- =========================================================

CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_departments_name UNIQUE (name),

    CONSTRAINT fk_departments_parent
        FOREIGN KEY (parent_id)
        REFERENCES departments(id)
        ON DELETE SET NULL
);


-- =========================================================
-- TEMEL DEPARTMANLAR
-- =========================================================

INSERT INTO departments (name, parent_id)
VALUES
    ('Yönetim', NULL),
    ('Finans', NULL),
    ('İnsan Kaynakları', NULL),
    ('Bilgi Teknolojileri', NULL),
    ('Satış', NULL)
ON CONFLICT (name) DO NOTHING;


-- =========================================================
-- MUHASEBE → FİNANS
-- =========================================================

INSERT INTO departments (name, parent_id)
SELECT
    'Muhasebe',
    id
FROM departments
WHERE name = 'Finans'
ON CONFLICT (name) DO NOTHING;


-- =========================================================
-- USERS'A ORGANİZASYON ALANLARI
-- =========================================================

ALTER TABLE users
ADD COLUMN IF NOT EXISTS department_id INTEGER;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS manager_id INTEGER;


-- =========================================================
-- FOREIGN KEY'LER
-- =========================================================

DO $$
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_users_department'
    ) THEN

        ALTER TABLE users
        ADD CONSTRAINT fk_users_department
        FOREIGN KEY (department_id)
        REFERENCES departments(id)
        ON DELETE SET NULL;

    END IF;


    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_users_manager'
    ) THEN

        ALTER TABLE users
        ADD CONSTRAINT fk_users_manager
        FOREIGN KEY (manager_id)
        REFERENCES users(id)
        ON DELETE SET NULL;

    END IF;

END $$;


-- =========================================================
-- MEVCUT KULLANICILARIN DEPARTMANLARINI EŞLEŞTİR
-- =========================================================

UPDATE users u
SET department_id = d.id
FROM departments d
WHERE
    u.department IS NOT NULL
    AND LOWER(TRIM(u.department)) = LOWER(TRIM(d.name))
    AND u.department_id IS NULL;


-- =========================================================
-- İZİN SÜRECİ İÇİN EK ALANLAR
-- =========================================================

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS approval_stage VARCHAR(30)
DEFAULT 'manager_pending';

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS manager_reviewed_by INTEGER;

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS manager_reviewed_at TIMESTAMP;

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS manager_note TEXT;

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS hr_reviewed_by INTEGER;

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS hr_reviewed_at TIMESTAMP;

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS hr_note TEXT;

-- Mevcut kullanıcıların yeni departman ID'lerini dolduruyoruz.
UPDATE users u
SET department_id = d.id
FROM departments d
WHERE
    u.department_id IS NULL
    AND (
        LOWER(TRIM(u.department)) = LOWER(TRIM(d.name))
        OR (
            LOWER(TRIM(u.department)) = 'it'
            AND d.name = 'Bilgi Teknolojileri'
        )
    );

-- =========================================================
-- İZİN ONAYLAYAN KULLANICILAR
-- =========================================================

DO $$
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_leave_manager_reviewer'
    ) THEN

        ALTER TABLE leave_requests
        ADD CONSTRAINT fk_leave_manager_reviewer
        FOREIGN KEY (manager_reviewed_by)
        REFERENCES users(id)
        ON DELETE SET NULL;

    END IF;


    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_leave_hr_reviewer'
    ) THEN

        ALTER TABLE leave_requests
        ADD CONSTRAINT fk_leave_hr_reviewer
        FOREIGN KEY (hr_reviewed_by)
        REFERENCES users(id)
        ON DELETE SET NULL;

    END IF;

END $$;