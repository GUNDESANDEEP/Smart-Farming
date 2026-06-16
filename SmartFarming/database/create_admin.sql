-- Smart Farming Admin Creation Script
-- Run this SQL in your MySQL client to create the admin account
-- Database: SmartFarmingDB

-- Replace the password hash below with the hashed version of "Sandy@7982"
-- The password hash below is the bcrypt hash of "Sandy@7982"

INSERT INTO admins (email, password_hash, first_name, role, created_at) 
VALUES (
    'gundesandeep2005@gmail.com',
    '$2b$12$YourHashedPasswordHere',  -- This needs to be replaced with actual bcrypt hash
    'Sandeep Gunde',
    'super_admin',
    NOW()
);

-- ============================================================
-- To get the correct password hash, use this Python command:
-- ============================================================
-- python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Sandy@7982'))"
-- 
-- Then replace '$2b$12$YourHashedPasswordHere' with the output above

-- ============================================================
-- QUICK SETUP INSTRUCTIONS:
-- ============================================================
-- 1. Open MySQL Workbench or command line
-- 2. Run: mysql -u root -p SmartFarmingDB
-- 3. Enter password: Sandy@7981  
-- 4. Paste this SQL and execute

-- Verify admin was created:
-- SELECT * FROM admins WHERE email = 'gundesandeep2005@gmail.com';
