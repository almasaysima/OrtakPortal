-- İzin taleplerinde dosya eki alanlarını ekler.
-- Mevcut verileri silmez; kolonlar nullable olduğu için eski kayıtlar korunur.

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS attachment_name VARCHAR(255);

ALTER TABLE leave_requests
ADD COLUMN IF NOT EXISTS attachment_object_name VARCHAR(500);
