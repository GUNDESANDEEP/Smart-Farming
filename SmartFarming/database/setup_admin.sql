-- ====================================================================
-- Smart Farming Admin Account Setup
-- Email: gundesandeep2005@gmail.com
-- Password: Sandy@7982
-- ====================================================================

INSERT INTO admins (email, password_hash, first_name, role, created_at) 
VALUES (
    'gundesandeep2005@gmail.com',
    'scrypt:32768:8:1$bzv0gsJq4B6FTnbl$b3357d5a98cb833476c5e30cbe4c1196913c271b6f95ebd813beebcecf1047c102c78d3359c16f7c30122d956708f4cb23d75309ef8255bb715fefc22a2bbfbc',
    'Sandeep Gunde',
    'super_admin',
    NOW()
);

-- ====================================================================
-- HOW TO RUN THIS:
-- ====================================================================
-- Option 1: MySQL Command Line
-- =====================
-- mysql -u root -p SmartFarmingDB < database/setup_admin.sql
-- When prompted for password, enter: Sandy@7981

-- Option 2: MySQL Workbench
-- =======================
-- 1. Open MySQL Workbench
-- 2. Click "File" > "Open SQL Script"
-- 3. Select this file
-- 4. Click "Execute" or press Ctrl+Shift+Enter
-- 5. When prompted, enter credentials

-- Option 3: Direct Query
-- ====================
-- mysql -u root -p SmartFarmingDB -e "INSERT INTO admins (email, password_hash, first_name, role, created_at) VALUES ('gundesandeep2005@gmail.com', 'scrypt:32768:8:1$bzv0gsJq4B6FTnbl$b3357d5a98cb833476c5e30cbe4c1196913c271b6f95ebd813beebcecf1047c102c78d3359c16f7c30122d956708f4cb23d75309ef8255bb715fefc22a2bbfbc', 'Sandeep Gunde', 'super_admin', NOW());"
-- When prompted for password, enter: Sandy@7981

-- ====================================================================
-- VERIFY ADMIN WAS CREATED:
-- ====================================================================
-- SELECT * FROM admins WHERE email = 'gundesandeep2005@gmail.com';
-- SELECT COUNT(*) as admin_count FROM admins;
