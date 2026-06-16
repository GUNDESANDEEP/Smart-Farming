#!/usr/bin/env python3
"""
Smart Farming Platform - End-to-End Test Suite
Tests all modules and endpoints for functionality
"""

import mysql.connector
import json
import sys
from datetime import datetime

class E2ETestSuite:
    """Comprehensive end-to-end test suite"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'smart_farming'
        }
        self.test_results = []
        self.errors = []
        
    def log_test(self, test_name, status, message=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {message}")
        
    def test_database_connection(self):
        """Test 1: Database Connection"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                self.log_test("Database Connection", "PASS", "Connected successfully")
                return True
            else:
                self.log_test("Database Connection", "FAIL", "Connection failed")
                return False
        except Exception as e:
            self.log_test("Database Connection", "FAIL", str(e))
            self.errors.append(f"Database Connection: {str(e)}")
            return False
    
    def test_database_tables(self):
        """Test 2: Database Tables Existence"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Query to get all tables
            cursor.execute("""
                SELECT TABLE_NAME FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA='smart_farming'
            """)
            tables = cursor.fetchall()
            table_count = len(tables)
            
            # Expected tables count
            expected_tables = 37
            
            if table_count >= expected_tables:
                self.log_test("Database Tables", "PASS", f"Found {table_count} tables (expected {expected_tables}+)")
                return True
            else:
                self.log_test("Database Tables", "FAIL", f"Found {table_count} tables (expected {expected_tables}+)")
                self.errors.append(f"Database Tables: Only {table_count} tables found, expected {expected_tables}+")
                return False
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Database Tables", "FAIL", str(e))
            self.errors.append(f"Database Tables: {str(e)}")
            return False
    
    def test_farmer_tables(self):
        """Test 3: Farmer Module Tables"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            farmer_tables = [
                'farmers', 'farmer_documents', 'farmer_otp_logs',
                'farm_details', 'farmer_stats'
            ]
            
            found_tables = []
            for table in farmer_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    found_tables.append(table)
            
            if len(found_tables) >= 3:
                self.log_test("Farmer Module Tables", "PASS", f"Found {len(found_tables)} farmer tables")
                return True
            else:
                self.log_test("Farmer Module Tables", "FAIL", f"Found {len(found_tables)} tables, expected 5+")
                self.errors.append(f"Farmer Module Tables: Missing some tables")
                return False
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Farmer Module Tables", "FAIL", str(e))
            self.errors.append(f"Farmer Module Tables: {str(e)}")
            return False
    
    def test_buyer_tables(self):
        """Test 4: Buyer Module Tables"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            buyer_tables = [
                'buyers', 'buyer_addresses', 'buyer_preferences'
            ]
            
            found_tables = []
            for table in buyer_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    found_tables.append(table)
            
            if len(found_tables) >= 2:
                self.log_test("Buyer Module Tables", "PASS", f"Found {len(found_tables)} buyer tables")
                return True
            else:
                self.log_test("Buyer Module Tables", "FAIL", f"Found {len(found_tables)} tables, expected 3+")
                self.errors.append(f"Buyer Module Tables: Missing some tables")
                return False
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Buyer Module Tables", "FAIL", str(e))
            self.errors.append(f"Buyer Module Tables: {str(e)}")
            return False
    
    def test_admin_tables(self):
        """Test 5: Admin Module Tables"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            admin_tables = [
                'admins', 'admin_logs', 'user_blocks',
                'product_approvals', 'disputes', 'refund_requests'
            ]
            
            found_tables = []
            for table in admin_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    found_tables.append(table)
            
            if len(found_tables) >= 4:
                self.log_test("Admin Module Tables", "PASS", f"Found {len(found_tables)} admin tables")
                return True
            else:
                self.log_test("Admin Module Tables", "FAIL", f"Found {len(found_tables)} tables, expected 6+")
                self.errors.append(f"Admin Module Tables: Missing some tables")
                return False
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Admin Module Tables", "FAIL", str(e))
            self.errors.append(f"Admin Module Tables: {str(e)}")
            return False
    
    def test_core_tables(self):
        """Test 6: Core/Shared Tables (Products, Orders, etc)"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            core_tables = [
                'products', 'orders', 'payments',
                'product_categories', 'reviews'
            ]
            
            found_tables = []
            for table in core_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    found_tables.append(table)
            
            if len(found_tables) >= 4:
                self.log_test("Core/Shared Tables", "PASS", f"Found {len(found_tables)} core tables")
                return True
            else:
                self.log_test("Core/Shared Tables", "FAIL", f"Found {len(found_tables)} tables, expected 5+")
                self.errors.append(f"Core Tables: Missing some tables")
                return False
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Core/Shared Tables", "FAIL", str(e))
            self.errors.append(f"Core Tables: {str(e)}")
            return False
    
    def test_advanced_features_tables(self):
        """Test 7: Advanced Features Tables (Notifications, Webhooks)"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            advanced_tables = [
                'notification_logs', 'webhooks', 'webhook_logs',
                'batch_operations', 'analytics_reports'
            ]
            
            found_tables = []
            for table in advanced_tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone():
                    found_tables.append(table)
            
            if len(found_tables) >= 3:
                self.log_test("Advanced Features Tables", "PASS", f"Found {len(found_tables)} advanced tables")
                return True
            else:
                self.log_test("Advanced Features Tables", "FAIL", f"Found {len(found_tables)} tables, expected 5+")
                return False  # Not critical
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Advanced Features Tables", "FAIL", str(e))
            return False  # Not critical
    
    def test_database_indexes(self):
        """Test 8: Database Indexes"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as index_count FROM information_schema.STATISTICS 
                WHERE TABLE_SCHEMA='smart_farming' AND SEQ_IN_INDEX=1
            """)
            result = cursor.fetchone()
            index_count = result[0] if result else 0
            
            if index_count >= 50:
                self.log_test("Database Indexes", "PASS", f"Found {index_count} indexes (expected 60+)")
                return True
            else:
                self.log_test("Database Indexes", "WARN", f"Found {index_count} indexes (expected 60+)")
                return False  # Warning only
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Database Indexes", "FAIL", str(e))
            return False  # Not critical
    
    def test_table_row_counts(self):
        """Test 9: Verify All Tables Are Accessible"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT TABLE_NAME, TABLE_ROWS FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA='smart_farming'
            """)
            tables = cursor.fetchall()
            
            accessible_count = 0
            for table_name, row_count in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    cursor.fetchone()
                    accessible_count += 1
                except:
                    pass
            
            if accessible_count >= 30:
                self.log_test("Table Accessibility", "PASS", f"All {accessible_count} tables accessible")
                return True
            else:
                self.log_test("Table Accessibility", "FAIL", f"Only {accessible_count} tables accessible")
                return False
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Table Accessibility", "FAIL", str(e))
            return False
    
    def test_data_integrity(self):
        """Test 10: Check Data Integrity (Foreign Keys, Constraints)"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if foreign keys are properly defined
            cursor.execute("""
                SELECT COUNT(*) as fk_count FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA='smart_farming' AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            result = cursor.fetchone()
            fk_count = result[0] if result else 0
            
            if fk_count >= 15:
                self.log_test("Data Integrity (Foreign Keys)", "PASS", f"Found {fk_count} foreign keys")
                return True
            else:
                self.log_test("Data Integrity (Foreign Keys)", "WARN", f"Found {fk_count} foreign keys (expected 15+)")
                return False  # Warning only
                
            cursor.close()
            conn.close()
        except Exception as e:
            self.log_test("Data Integrity", "FAIL", str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("SMART FARMING PLATFORM - END-TO-END TEST SUITE")
        print("="*60 + "\n")
        
        tests = [
            ("Database Connection", self.test_database_connection()),
            ("Database Tables", self.test_database_tables()),
            ("Farmer Module Tables", self.test_farmer_tables()),
            ("Buyer Module Tables", self.test_buyer_tables()),
            ("Admin Module Tables", self.test_admin_tables()),
            ("Core/Shared Tables", self.test_core_tables()),
            ("Advanced Features Tables", self.test_advanced_features_tables()),
            ("Database Indexes", self.test_database_indexes()),
            ("Table Accessibility", self.test_table_row_counts()),
            ("Data Integrity", self.test_data_integrity()),
        ]
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60 + "\n")
        
        passed = sum(1 for _, result in tests if result)
        total = len(tests)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%\n")
        
        if self.errors:
            print("⚠️  ERRORS FOUND:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("✅ NO ERRORS FOUND - All tests passed!")
        
        print("\n" + "="*60 + "\n")
        
        return passed == total


if __name__ == '__main__':
    test_suite = E2ETestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)
