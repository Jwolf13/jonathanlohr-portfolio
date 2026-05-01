ALTER TABLE profiles
ADD COLUMN display_order SMALLINT DEFAULT 0;

-- Update existing profiles to have sequential order
WITH ordered AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY created_at) AS rn
    FROM profiles
)
UPDATE profiles
SET display_order = ordered.rn
FROM ordered
WHERE profiles.id = ordered.id;