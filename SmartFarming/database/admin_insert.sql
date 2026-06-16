-- ====================================================================
-- SMART FARMING - ADMIN ACCOUNT CREATION
-- ====================================================================
-- Database: SmartFarmingDB
-- User Credentials:
--   Email: gundesandeep2005@gmail.com
--   Password: Sandy@7982
--   Role: super_admin
-- ====================================================================

-- First, verify the database and tables exist
USE SmartFarmingDB;

-- Show current admins
SELECT 'Current admins in database:' as INFO;
SELECT * FROM admins;

-- Insert the new admin account
INSERT INTO admins (email, password_hash, first_name, role, created_at, is_active) 
VALUES (
    'gundesandeep2005@gmail.com',
    'scrypt:32768:8:1$bzv0gsJq4B6FTnbl$b3357d5a98cb833476c5e30cbe4c1196913c271b6f95ebd813beebcecf1047c102c78d3359c16f7c30122d956708f4cb23d75309ef8255bb715fefc22a2bbfbc',
    'Sandeep Gunde',
    'super_admin',
    NOW(),
    TRUE
);

-- Verify the admin was created
SELECT 'Newly created admin:' as INFO;
SELECT admin_id, email, first_name, role, is_active FROM admins WHERE email = 'gundesandeep2005@gmail.com';

-- ====================================================================
-- HOW TO RUN THIS SCRIPT:
-- ====================================================================

-- OPTION 1: MySQL Command Line (Recommended)
-- ==========================================
-- Open Command Prompt (cmd) or PowerShell and run:
-- 
-- mysql -u root -p SmartFarmingDB < "C:\path\to\this\file.sql"
-- 
-- When prompted for password, enter: Sandy@7981
-- 
-- Full example:
-- mysql -u root -p SmartFarmingDB < "C:\Users\SANDEEP\OneDrive\Documents\Desktop\Smart Farming\SmartFarming\database\admin_insert.sql"

-- OPTION 2: MySQL Workbench
-- =========================
-- 1. Open MySQL Workbench
-- 2. Click "File" → "Open SQL Script"
-- 3. Select this file
-- 4. Click "Execute" button or press Ctrl+Shift+Enter
-- 5. When prompted, enter MySQL password: Sandy@7981

-- OPTION 3: Direct MySQL Shell
-- =============================
-- 1. Open Command Prompt
-- 2. Run: mysql -u root -p
-- 3. When prompted, enter password: Sandy@7981
-- 4. Type: USE SmartFarmingDB;
-- 5. Copy-paste the INSERT statement above

-- OPTION 4: From PowerShell
-- ==========================
-- $mysql_cmd = @"
-- USE SmartFarmingDB;
-- INSERT INTO admins VALUES ('gundesandeep2005@gmail.com', 'scrypt:32768:8:1\$bzv0gsJq4B6FTnbl\$b3357d5a98cb833476c5e30cbe4c1196913c271b6f95ebd813beebcecf1047c102c78d3359c16f7c30122d956708f4cb23d75309ef8255bb715fefc22a2bbfbc', 'Sandeep Gunde', 'super_admin', NOW(), TRUE);
-- "@
-- mysql -u root -p SmartFarmingDB -e $mysql_cmd

-- ====================================================================
-- VERIFICATION
-- ====================================================================
-- After running the script, verify the admin was created:
-- 
-- SELECT * FROM admins WHERE email = 'gundesandeep2005@gmail.com';
-- 
-- If successful, you should see:
-- admin_id | email | password_hash | first_name | role | ...
-- 
-- Then you can login using:
-- Email: gundesandeep2005@gmail.com
-- Password: Sandy@7982

-- ====================================================================
-- TROUBLESHOOTING
-- ====================================================================
-- 
-- If you get "ERROR 1045 (28000): Access denied for user 'root'@'localhost'"
-- - Check that MySQL service is running
-- - Verify MySQL password is: Sandy@7981
-- - Try using: mysql -h 127.0.0.1 instead of localhost
-- 
-- If you get "ERROR 1146 (42S02): Table 'smartfarmingdb.admins' doesn't exist"
-- - The database schema hasn't been loaded
-- - Run all schema files first: admin_schema.sql, schema.sql, buyer_schema.sql
-- 
-- If you get "ERROR 1062 (23000): Duplicate entry"
-- - Admin with this email already exists
-- - Delete the old record first: DELETE FROM admins WHERE email = 'gundesandeep2005@gmail.com';

