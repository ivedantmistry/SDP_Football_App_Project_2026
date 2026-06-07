import sqlite3
import json
from datetime import datetime, timedelta

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
            number INTEGER,
            position TEXT,
            photo TEXT,
            nationality TEXT,
            flag_url TEXT,
            height TEXT,
            team_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coaches (
            coach_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            nationality TEXT,
            photo TEXT,
            team_id INTEGER UNIQUE,
            FOREIGN KEY (team_id) REFERENCES teams (team_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS endpoint_cache (
            endpoint_key TEXT PRIMARY KEY,
            json_data TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
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
    """Saves a team search entry."""
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
    """Gets the most recent search entries."""
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
    """Clears all search entries."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_history")
    conn.commit()
    conn.close()


def delete_search(team_name):
    """Deletes a specific search entry by team name."""
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


def insert_player(
    player_id,
    name,
    age,
    number,
    position,
    photo,
    nationality,
    flag_url,
    height,
    team_id,
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO players (player_id, name, age, number, position, photo, nationality, flag_url, height, team_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(player_id) DO UPDATE SET
        name=excluded.name, age=excluded.age, number=excluded.number, position=excluded.position, photo=excluded.photo, nationality=excluded.nationality, flag_url=excluded.flag_url, height=excluded.height, team_id=excluded.team_id
    """,
        (
            player_id,
            name,
            age,
            number,
            position,
            photo,
            nationality,
            flag_url,
            height,
            team_id,
        ),
    )
    conn.commit()
    conn.close()


def get_team_players(team_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT player_id, name, age, number, position, photo, nationality, flag_url, height 
        FROM players WHERE team_id = ? ORDER BY position, name
    """,
        (team_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "age": r[2],
            "number": r[3],
            "position": r[4],
            "photo": r[5],
            "nationality": r[6],
            "flag_url": r[7],
            "height": r[8],
        }
        for r in rows
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
            "description": f"{row[1]} plays home matches at {row[3]}.",
        }
    return None


def insert_coach(coach_id, name, age, nationality, photo, team_id):
    """Lưu thông tin HLV vào database cục bộ."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO coaches (coach_id, name, age, nationality, photo, team_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(coach_id) DO UPDATE SET
        name=excluded.name, age=excluded.age, nationality=excluded.nationality, photo=excluded.photo, team_id=excluded.team_id
    """,
        (coach_id, name, age, nationality, photo, team_id),
    )
    conn.commit()
    conn.close()


def get_team_coach_local(team_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name, age, nationality, photo 
        FROM coaches 
        WHERE team_id = ?
    """,
        (team_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "name": row[0],
            "age": row[1],
            "nationality": row[2],
            "photo": row[3],
        }
    return None


def get_all_leagues():
    """Lấy danh sách các giải đấu đã được lưu từ Seed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Sắp xếp theo tên cho gọn gàng
    cursor.execute("SELECT league_id, name, logo, country FROM leagues ORDER BY name")
    rows = cursor.fetchall()
    conn.close()

    return [{"id": r[0], "name": r[1], "logo": r[2], "country": r[3]} for r in rows]


def is_matches_cache_valid(league_name, hours_valid=24):
    """
    Checks if the local match data is fresh enough.
    Returns True if data is fresh, False if we need to call the API.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT last_updated FROM cached_matches 
        WHERE league_name = ? 
        ORDER BY last_updated DESC LIMIT 1
    """,
        (league_name,),
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    last_updated_string = row[0]
    last_updated = datetime.strptime(last_updated_string, "%Y-%m-%d %H:%M:%S")
    expiration_time = last_updated + timedelta(hours=hours_valid)

    return datetime.now() < expiration_time


def toggle_favorite(team_id, team_name, team_logo):
    """Toggles a team in the favorites table. Inserts team if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if it's already a favorite
    cursor.execute("SELECT id FROM favorites WHERE team_id = ?", (team_id,))
    row = cursor.fetchone()

    if row:
        # Remove from favorites
        cursor.execute("DELETE FROM favorites WHERE team_id = ?", (team_id,))
        is_fav = False
    else:
        # Ensure team exists in teams table first (minimal info)
        cursor.execute(
            """
            INSERT INTO teams (team_id, name, logo, venue_id) 
            VALUES (?, ?, ?, NULL)
            ON CONFLICT(team_id) DO UPDATE SET name=excluded.name, logo=excluded.logo
        """,
            (team_id, team_name, team_logo),
        )

        # Add to favorites
        cursor.execute("INSERT INTO favorites (team_id) VALUES (?)", (team_id,))
        is_fav = True

    conn.commit()
    conn.close()
    return is_fav


def is_favorite(team_id):
    """Checks if a specific team is marked as favorite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM favorites WHERE team_id = ?", (team_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row)


def get_all_favorites():
    """Retrieves all favorite teams to display on the dashboard."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.team_id, t.name, t.logo 
        FROM favorites f
        JOIN teams t ON f.team_id = t.team_id
        ORDER BY f.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "logo": r[2]} for r in rows]


def get_cached_api_data(endpoint_key, hours_valid=24):
    """Fetches JSON data from SQLite if it is less than 'hours_valid' old."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # We use a try-except here just in case the table hasn't been created yet
    try:
        cursor.execute(
            "SELECT json_data, last_updated FROM endpoint_cache WHERE endpoint_key = ?",
            (endpoint_key,),
        )
        row = cursor.fetchone()
    except sqlite3.OperationalError:
        conn.close()
        return None

    conn.close()

    if not row:
        return None

    last_updated = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
    if datetime.now() < last_updated + timedelta(hours=hours_valid):
        return json.loads(row[0])  # Data is fresh, return it

    return None  # Data is expired or missing


def save_cached_api_data(endpoint_key, data):
    """Saves fresh API JSON data into SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    json_string = json.dumps(data)
    cursor.execute(
        """
        INSERT INTO endpoint_cache (endpoint_key, json_data, last_updated)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(endpoint_key) DO UPDATE SET
        json_data=excluded.json_data, last_updated=CURRENT_TIMESTAMP
    """,
        (endpoint_key, json_string),
    )
    conn.commit()
    conn.close()
