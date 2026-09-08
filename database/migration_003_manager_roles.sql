ALTER TYPE user_role
ADD VALUE IF NOT EXISTS 'it_admin';

ALTER TYPE user_role
ADD VALUE IF NOT EXISTS 'finance_admin';
