"""Create missing database tables"""
import MySQLdb

conn = MySQLdb.connect(host='localhost', user='root', password='sandeep@7981', db='SmartFarmingDB', charset='utf8mb4')
cursor = conn.cursor()

tables = [
    """CREATE TABLE IF NOT EXISTS conversations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        participant1_id INT NOT NULL,
        participant1_type ENUM('farmer','buyer','admin') NOT NULL,
        participant2_id INT NOT NULL,
        participant2_type ENUM('farmer','buyer','admin') NOT NULL,
        last_message TEXT,
        last_message_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY unique_conversation (participant1_id, participant1_type, participant2_id, participant2_type),
        INDEX idx_p1 (participant1_id, participant1_type),
        INDEX idx_p2 (participant2_id, participant2_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

    """CREATE TABLE IF NOT EXISTS messages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        conversation_id INT NOT NULL,
        sender_id INT NOT NULL,
        sender_type ENUM('farmer','buyer','admin') NOT NULL,
        content TEXT NOT NULL,
        message_type ENUM('text','image','file') DEFAULT 'text',
        is_read TINYINT(1) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
        INDEX idx_conversation (conversation_id),
        INDEX idx_sender (sender_id, sender_type),
        INDEX idx_read (is_read)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

    """CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        user_type ENUM('farmer','buyer','admin') NOT NULL,
        title VARCHAR(255) NOT NULL,
        message TEXT,
        type VARCHAR(50) DEFAULT 'info',
        is_read TINYINT(1) DEFAULT 0,
        data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user (user_id, user_type),
        INDEX idx_read (is_read),
        INDEX idx_type (type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

    # Fix buyers.buyer_id - update NULL values to match id
    """UPDATE buyers SET buyer_id = id WHERE buyer_id IS NULL"""
]

for sql in tables:
    try:
        cursor.execute(sql)
        conn.commit()
        action = sql.strip().split()[0:4]
        print(f"[OK] {' '.join(action)}...")
    except Exception as e:
        print(f"[SKIP] {e}")

# Verify all tables
cursor.execute("SHOW TABLES")
all_tables = [t[0] for t in cursor.fetchall()]
print(f"\nTotal tables: {len(all_tables)}")
for t in sorted(all_tables):
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cursor.fetchone()[0]
    print(f"  {t:35s} {cnt:>4} rows")

conn.close()
print("\nDatabase migration complete!")
