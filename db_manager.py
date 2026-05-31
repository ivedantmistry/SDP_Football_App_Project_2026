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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venues (
            venue_id INTEGER PRIMARY KEY,
            name TEXT,
            city TEXT,
            capacity INTEGER,
            surface TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY,
            name TEXT,
            logo TEXT,
            venue_id INTEGER,
            FOREIGN KEY (venue_id) REFERENCES venues (venue_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER UNIQUE,
            FOREIGN KEY (team_id) REFERENCES teams (team_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cached_matches (
            match_id INTEGER PRIMARY KEY,
            home_id INTEGER,
            away_id INTEGER,
            home_score INTEGER,
            away_score INTEGER,
            match_date TEXT,
            match_time TEXT,
            status TEXT,
            league_name TEXT,
            league_logo TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leagues (
            league_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT,
            logo TEXT,
            type TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            position TEXT,
            photo TEXT,
            team_id INTEGER,
            FOREIGN KEY (team_id) REFERENCES teams (team_id)
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


def search_local_teams(query_string):
    """Searches the permanent local cache for matching teams and joins stadium info."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.name, t.logo, v.name 
        FROM teams t
        LEFT JOIN venues v ON t.venue_id = v.venue_id
        WHERE t.name LIKE ?
    """,
        (f"%{query_string}%",),
    )

    rows = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "badge": row[1], "stadium": row[2]} for row in rows]


def insert_league(league_id, name, country, logo, league_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO leagues (league_id, name, country, logo, type)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(league_id) DO UPDATE SET
        name=excluded.name, country=excluded.country, logo=excluded.logo, type=excluded.type
    """,
        (league_id, name, country, logo, league_type),
    )
    conn.commit()
    conn.close()


def insert_player(player_id, name, age, position, photo, team_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO players (player_id, name, age, position, photo, team_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(player_id) DO UPDATE SET
        name=excluded.name, age=excluded.age, position=excluded.position, photo=excluded.photo, team_id=excluded.team_id
    """,
        (player_id, name, age, position, photo, team_id),
    )
    conn.commit()
    conn.close()


def get_team_players(team_id):
    """Retrieves the roster for a specific team from the local cache."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT player_id, name, age, position, photo 
        FROM players 
        WHERE team_id = ?
        ORDER BY position, name
    """, (team_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert SQLite rows into a clean list of dictionaries for HTML
    return [
        {"id": row[0], "name": row[1], "age": row[2], "position": row[3], "photo": row[4]} 
        for row in rows
    ]

def get_team_profile(team_name):
    """Fetches full team and stadium details from the local DB for the Team Page."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.team_id, t.name, t.logo, v.name, v.city, v.capacity, v.surface
        FROM teams t
        LEFT JOIN venues v ON t.venue_id = v.venue_id
        WHERE t.name = ?
    """,
        (team_name,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "name": row[1],
            "badge_url": row[2],
            "stadium_name": row[3] or "Unknown Stadium",
            "stadium_location": row[4] or "Unknown Location",
            "stadium_capacity": row[5] or "N/A",
            "description": f"{row[1]} plays home matches at {row[3]}."
        }
    return None