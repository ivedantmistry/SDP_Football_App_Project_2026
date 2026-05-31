import os

import requests
from dotenv import load_dotenv

import db_manager

load_dotenv()

API_KEY = os.getenv("API_SPORTS_KEY")
HEADERS = {"x-apisports-key": API_KEY}


def seed_league(league_id, season):
    """
    Fetch all teams and venues for a given league and season,
    then save them to the SQLite database.
    """
    db_manager.init_db()

    url = "https://v3.football.api-sports.io/teams"
    params = {
        "league": league_id,
        "season": season,
    }

    print(f"Fetching data for League ID: {league_id}, Season: {season}...")

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

            # Save venue
            if venue and venue.get("id"):
                db_manager.insert_venue(
                    venue_id=venue.get("id"),
                    name=venue.get("name"),
                    city=venue.get("city"),
                    capacity=venue.get("capacity"),
                    surface=venue.get("surface"),
                )

            # Save team
            if team and team.get("id"):
                db_manager.insert_team(
                    team_id=team.get("id"),
                    name=team.get("name"),
                    logo=team.get("logo"),
                    venue_id=venue.get("id") if venue else None,
                )

        print(
            f"Successfully seeded {len(results)} teams and venues "
            f"for league {league_id} into the database!"
        )

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")


if __name__ == "__main__":
    # Premier League
    seed_league(league_id=39, season=2024)

    # Bundesliga
    seed_league(league_id=78, season=2024)
