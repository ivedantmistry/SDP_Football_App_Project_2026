import sqlite3

DB_PATH = "fotmob.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. User Data (Dynamic/Personal)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT UNIQUE,
            team_logo TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Permanent Data: Venues (Stadiums)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venues (
            venue_id INTEGER PRIMARY KEY,
            name TEXT,
            city TEXT,
            capacity INTEGER,
            surface TEXT
        )
    """)

    # 3. Permanent Data: Teams
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY,
            name TEXT,
            logo TEXT,
            venue_id INTEGER,
            FOREIGN KEY (venue_id) REFERENCES venues (venue_id)
        )
    """)

    conn.commit()
    conn.close()


def insert_venue(venue_id, name, city, capacity, surface):
    """Inserts or updates a stadium/venue."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO venues (venue_id, name, city, capacity, surface) 
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(venue_id) DO UPDATE SET
        name=excluded.name, city=excluded.city, capacity=excluded.capacity, surface=excluded.surface
    """,
        (venue_id, name, city, capacity, surface),
    )
    conn.commit()
    conn.close()


def insert_team(team_id, name, logo, venue_id):
    """Inserts or updates a team."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO teams (team_id, name, logo, venue_id) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(team_id) DO UPDATE SET
        name=excluded.name, logo=excluded.logo, venue_id=excluded.venue_id
    """,
        (team_id, name, logo, venue_id),
    )
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
