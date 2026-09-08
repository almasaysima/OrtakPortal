BEGIN;

-- 1) İzin verilen üç departmanın var olduğundan emin ol.
INSERT INTO departments (name, parent_id)
VALUES
    ('Bilgi Teknolojileri', NULL),
    ('Finans', NULL),
    ('İnsan Kaynakları', NULL)
ON CONFLICT (name) DO NOTHING;

-- 2) Eski IT metinlerini standart ada çevir.
UPDATE users
SET department = 'Bilgi Teknolojileri'
WHERE LOWER(TRIM(COALESCE(department, ''))) = 'it';

-- 3) Bu üç departman dışında kalan mevcut kullanıcıları
--    geçici olarak Bilgi Teknolojileri departmanına taşı.
--    Böylece foreign key nedeniyle kullanıcı kaybı olmaz.
UPDATE users
SET
    department = 'Bilgi Teknolojileri',
    department_id = (
        SELECT id
        FROM departments
        WHERE name = 'Bilgi Teknolojileri'
        LIMIT 1
    )
WHERE
    department_id IS NULL
    OR department_id NOT IN (
        SELECT id
        FROM departments
        WHERE name IN (
            'Bilgi Teknolojileri',
            'Finans',
            'İnsan Kaynakları'
        )
    );

-- 4) Metin alanı ile department_id alanını yeniden eşle.
UPDATE users u
SET department_id = d.id
FROM departments d
WHERE
    d.name IN (
        'Bilgi Teknolojileri',
        'Finans',
        'İnsan Kaynakları'
    )
    AND LOWER(TRIM(u.department)) = LOWER(TRIM(d.name));

-- 5) Portalda kullanılmayacak eski departmanları kaldır.
--    users.department_id foreign key'i ON DELETE SET NULL olsa da
--    yukarıdaki adımlarda kullanıcılar önce güvenli departmana taşındı.
DELETE FROM departments
WHERE name NOT IN (
    'Bilgi Teknolojileri',
    'Finans',
    'İnsan Kaynakları'
);

COMMIT;
