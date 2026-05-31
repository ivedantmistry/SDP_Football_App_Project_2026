import os
import time
import requests
from dotenv import load_dotenv
import db_manager

load_dotenv()

API_KEY = os.getenv("API_SPORTS_KEY")
HEADERS = {"x-apisports-key": API_KEY}

def seed_league_info(league_id):
    """Fetches the details for the league itself (name, logo, country) and saves it."""
    url = "https://v3.football.api-sports.io/leagues"
    params = {"id": league_id}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("response"):
            league_data = data["response"][0]["league"]
            country_data = data["response"][0]["country"]
            
            db_manager.insert_league(
                league_id=league_data.get("id"),
                name=league_data.get("name"),
                country=country_data.get("name"),
                logo=league_data.get("logo"),
                league_type=league_data.get("type")
            )
            print(f"✅ Seeded league info for: {league_data.get('name')}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching league info for ID {league_id}: {e}")

def seed_league(league_id, season):
    """Fetches all teams and venues for a given league and saves them to SQLite."""
    url = "https://v3.football.api-sports.io/teams"
    params = {"league": league_id, "season": season}

    print(f"Fetching teams for League ID: {league_id}, Season: {season}...")

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("errors"):
            print(f"API Error: {data['errors']}")
            return

        results = data.get("response", [])

        for item in results:
            team = item.get("team", {})
            venue = item.get("venue", {})

            if venue and venue.get("id"):
                db_manager.insert_venue(
                    venue_id=venue.get("id"),
                    name=venue.get("name"),
                    city=venue.get("city"),
                    capacity=venue.get("capacity"),
                    surface=venue.get("surface"),
                )

            if team and team.get("id"):
                db_manager.insert_team(
                    team_id=team.get("id"),
                    name=team.get("name"),
                    logo=team.get("logo"),
                    venue_id=venue.get("id") if venue else None,
                )

        print(f"✅ Seeded {len(results)} teams for league {league_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    db_manager.init_db()

    leagues_to_seed = [
        39,  # Premier League/
        78,  # Bundesliga
        140, # La Liga
        135, # Serie A
        61,  # Ligue 1
        2,   # UEFA Champions League
        3,   # UEFA Europa League
    ]

    season_to_use = 2024

    for l_id in leagues_to_seed:
        seed_league_info(league_id=l_id)
        
        seed_league(league_id=l_id, season=season_to_use)
        
        time.sleep(1) 
        print("-" * 30)
        
    print("Database seeding complete!")