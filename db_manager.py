import sqlite3

DB_PATH = "fotmob.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE,
            team_logo TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_search(team_name, team_logo):
    """Lưu đội bóng vào lịch sử (Nếu đã có thì cập nhật lại thời gian mới nhất)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO search_history (team_name, team_logo, timestamp) 
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(team_name) 
        DO UPDATE SET timestamp = CURRENT_TIMESTAMP
    """,
        (team_name, team_logo),
    )
    conn.commit()
    conn.close()


def get_recent_searches(limit=5):
    """Lấy 5 đội bóng tìm kiếm gần nhất"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT team_name, team_logo FROM search_history 
        ORDER BY timestamp DESC LIMIT ?
    """,
        (limit,),
    )
    results = [{"name": row[0], "badge": row[1]} for row in cursor.fetchall()]
    conn.close()
    return results


def clear_all_searches():
    """Xóa toàn bộ lịch sử tìm kiếm"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_history")
    conn.commit()
    conn.close()


def delete_search(team_name):
    """Xóa một đội bóng cụ thể khỏi lịch sử"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_history WHERE team_name = ?", (team_name,))
    conn.commit()
    conn.close()
