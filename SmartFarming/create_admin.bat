@echo off
REM Smart Farming Admin Creation Script
REM This batch file will create the admin account in the database

cd /d "C:\Users\SANDEEP\OneDrive\Documents\Desktop\Smart Farming\SmartFarming\database"

echo.
echo ====================================================================
echo SMART FARMING - ADMIN ACCOUNT SETUP
echo ====================================================================
echo.
echo Attempting to query current admins in database...
echo.

"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root -pSandy@7981 SmartFarmingDB -e "SELECT 'Current admins count:' as INFO; SELECT COUNT(*) as admin_count FROM admins;"

echo.
echo Inserting new admin account...
echo.

"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root -pSandy@7981 SmartFarmingDB -e "INSERT INTO admins (email, password_hash, first_name, role, created_at, is_active) VALUES ('gundesandeep2005@gmail.com', 'scrypt:32768:8:1$bzv0gsJq4B6FTnbl$b3357d5a98cb833476c5e30cbe4c1196913c271b6f95ebd813beebcecf1047c102c78d3359c16f7c30122d956708f4cb23d75309ef8255bb715fefc22a2bbfbc', 'Sandeep Gunde', 'super_admin', NOW(), TRUE);"

echo.
echo Verifying admin was created...
echo.

"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root -pSandy@7981 SmartFarmingDB -e "SELECT admin_id, email, first_name, role, is_active FROM admins WHERE email = 'gundesandeep2005@gmail.com';"

echo.
echo ====================================================================
echo Setup complete!
echo ====================================================================
echo.
echo You can now login with:
echo   Email: gundesandeep2005@gmail.com
echo   Password: Sandy@7982
echo.
pause
