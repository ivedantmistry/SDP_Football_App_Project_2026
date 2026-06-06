import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_SPORTS_KEY")
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"


def _make_api_request(endpoint, params=None, timeout_seconds=10):
    """
    Central wrapper for all API calls.
    Handles URLs, headers, timeouts, and basic monitoring.
    """
    if not API_KEY:
        print("[System] API Key is missing.")
        return None

    url = f"{BASE_URL}/{endpoint}"
    start_time = time.time()

    try:
        response = requests.get(
            url, headers=HEADERS, params=params, timeout=timeout_seconds
        )
        response.raise_for_status()

        # Monitoring: Track execution time
        execution_time = time.time() - start_time
        print(
            f"[API Monitor] GET /{endpoint} | Status: {response.status_code} | Time: {execution_time:.3f}s"
        )

        data = response.json()

        # Centralized API error checking
        if data.get("errors"):
            print(f"[API Error] /{endpoint}: {data['errors']}")
            return None

        return data.get("response")

    except requests.exceptions.Timeout:
        print(f"[API Timeout] Request to /{endpoint} exceeded {timeout_seconds}s.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[API Exception] Failed to reach /{endpoint}: {e}")
        return None


# ---------------------------------------------------------
# Specific API Functions
# ---------------------------------------------------------


def search_teams_list(query):
    """Searches for teams matching the query and returns a list of results with dynamic descriptions."""
    response_data = _make_api_request("teams", {"search": query})
    results = []

    if response_data:
        for item in response_data:
            team = item.get("team", {})
            venue = item.get("venue", {})

            founded = team.get("founded") or "an unknown year"
            country = team.get("country", "Unknown")
            city = venue.get("city", country)
            surface = venue.get("surface", "grass")

            dynamic_description = (
                f"{team.get('name')} is a professional football club based in {city}, {country}. "
                f"Founded in {founded}, the team plays their home matches at {venue.get('name')}. "
                f"The stadium features a {surface} surface and can hold up to {venue.get('capacity')} fans."
            )

            results.append(
                {
                    "id": team.get("id"),
                    "name": team.get("name"),
                    "badge_url": team.get("logo"),
                    "stadium_name": venue.get("name") or "Unknown Stadium",
                    "stadium_location": venue.get("city") or "Unknown Location",
                    "stadium_capacity": venue.get("capacity") or "N/A",
                    "description": dynamic_description,
                }
            )
    return results


def get_exact_team(team_name):
    """Finds one specific team for the detail page."""
    search_term = team_name.split()[0]
    teams = search_teams_list(search_term)

    for team in teams:
        if team["name"].lower() == team_name.lower():
            return team
    return teams[0] if teams else None


def get_team_fixtures(team_id):
    """Fetches past and upcoming fixtures for a specific team, returning form and next match data."""
    response_data = _make_api_request("fixtures", {"team": team_id, "season": 2024})

    if not response_data:
        return {"form": [], "next_match": None, "all_matches": []}

    past_matches = []
    future_matches = []

    for match in response_data:
        status = match["fixture"]["status"]["short"]
        if status in ["FT", "AET", "PEN"]:
            past_matches.append(match)
        elif status in ["NS", "TBD"]:
            future_matches.append(match)

    past_matches.sort(key=lambda x: x["fixture"]["timestamp"], reverse=True)
    last_5 = past_matches[:5][::-1]

    future_matches.sort(key=lambda x: x["fixture"]["timestamp"])
    next_1 = (
        future_matches[0]
        if future_matches
        else (past_matches[5] if len(past_matches) > 5 else None)
    )

    form_data = []
    for match in last_5:
        home_team = match["teams"]["home"]
        away_team = match["teams"]["away"]
        goals_home = match["goals"]["home"]
        goals_away = match["goals"]["away"]

        is_home = home_team["id"] == team_id
        opponent = away_team if is_home else home_team

        if goals_home is None or goals_away is None:
            result = "D"
            score_display = "? - ?"
        else:
            score_display = f"{goals_home} - {goals_away}"
            if goals_home == goals_away:
                result = "D"
            elif (is_home and goals_home > goals_away) or (
                not is_home and goals_away > goals_home
            ):
                result = "W"
            else:
                result = "L"

        form_data.append(
            {
                "opponent_logo": opponent["logo"],
                "score": score_display,
                "result": result,
            }
        )

    next_match_data = None
    if next_1:
        raw_date = next_1["fixture"]["date"]
        next_match_data = {
            "league": next_1["league"]["name"],
            "league_logo": next_1["league"]["logo"],
            "date": raw_date[:10],
            "time": raw_date[11:16],
            "home_team": next_1["teams"]["home"]["name"],
            "home_logo": next_1["teams"]["home"]["logo"],
            "away_team": next_1["teams"]["away"]["name"],
            "away_logo": next_1["teams"]["away"]["logo"],
        }

    all_fixtures_data = []
    for match in response_data:
        home_team = match["teams"]["home"]
        away_team = match["teams"]["away"]
        raw_date_str = match["fixture"]["date"]

        try:
            dt_obj = datetime.fromisoformat(raw_date_str.replace("+00:00", ""))
            formatted_date = dt_obj.strftime("%a, %b %d")
            time_12hr = dt_obj.strftime("%I:%M %p")
        except ValueError:
            formatted_date = raw_date_str[:10]
            time_12hr = raw_date_str[11:16]

        status = match["fixture"]["status"]["short"]
        home_goals = match["goals"]["home"]
        away_goals = match["goals"]["away"]

        result = "N/A"
        if (
            status in ["FT", "AET", "PEN"]
            and home_goals is not None
            and away_goals is not None
        ):
            is_home = home_team["id"] == team_id
            if home_goals == away_goals:
                result = "D"
            elif (is_home and home_goals > away_goals) or (
                not is_home and away_goals > home_goals
            ):
                result = "W"
            else:
                result = "L"

        all_fixtures_data.append(
            {
                "date": formatted_date,
                "time": time_12hr,
                "status": status,
                "home_team": home_team["name"],
                "home_logo": home_team["logo"],
                "away_team": away_team["name"],
                "away_logo": away_team["logo"],
                "home_goals": home_goals,
                "away_goals": away_goals,
                "league_name": match["league"]["name"],
                "league_logo": match["league"]["logo"],
                "result": result,
            }
        )

    return {
        "form": form_data,
        "next_match": next_match_data,
        "all_matches": all_fixtures_data,
    }


def get_flag_url(country_name):
    """Returns the URL of the flag image for a given country name."""
    flags = {
        "England": "gb-eng",
        "France": "fr",
        "Spain": "es",
        "Germany": "de",
        "Italy": "it",
        "Brazil": "br",
        "Argentina": "ar",
        "Portugal": "pt",
        "Netherlands": "nl",
        "Belgium": "be",
        "Denmark": "dk",
        "United States": "us",
        "Senegal": "sn",
        "Uruguay": "uy",
        "Colombia": "co",
        "Switzerland": "ch",
        "Croatia": "hr",
        "Ukraine": "ua",
        "Ecuador": "ec",
        "Japan": "jp",
        "Scotland": "gb-sct",
        "Wales": "gb-wls",
        "Norway": "no",
        "Sweden": "se",
        "Poland": "pl",
        "Morocco": "ma",
        "Ivory Coast": "ci",
        "Ghana": "gh",
    }
    code = flags.get(country_name)
    return f"https://flagcdn.com/w20/{code}.png" if code else None


def fetch_squad_from_api(team_id):
    """Fetches the current full roster for a team from API-Sports and groups them by position."""
    response_data = _make_api_request(
        "players", {"team": team_id, "season": 2024, "page": 1}
    )
    if not response_data:
        return {}

    players_data = list(response_data)

    # Check for page 2 (Optional but good for full squads)
    page2_data = _make_api_request(
        "players", {"team": team_id, "season": 2024, "page": 2}
    )
    if page2_data:
        players_data.extend(page2_data)

    grouped_squad = {
        "Goalkeepers": [],
        "Defenders": [],
        "Midfielders": [],
        "Attackers": [],
    }

    for item in players_data:
        p_info = item.get("player", {})
        pon = pos = None

        for stat in item.get("statistics", []):
            games = stat.get("games", {})
            if games.get("number"):
                pon = games.get("number")
            if games.get("position"):
                pos = games.get("position")

        player_dict = {
            "id": p_info.get("id"),
            "name": p_info.get("name"),
            "age": p_info.get("age"),
            "number": pon,
            "position": pos,
            "photo": p_info.get("photo"),
            "nationality": p_info.get("nationality"),
            "flag_url": get_flag_url(p_info.get("nationality")),
            "height": p_info.get("height"),
        }

        if pos == "Goalkeeper":
            grouped_squad["Goalkeepers"].append(player_dict)
        elif pos == "Defender":
            grouped_squad["Defenders"].append(player_dict)
        elif pos == "Midfielder":
            grouped_squad["Midfielders"].append(player_dict)
        elif pos == "Attacker":
            grouped_squad["Attackers"].append(player_dict)

    return {k: v for k, v in grouped_squad.items() if len(v) > 0}


def get_team_coach(team_id):
    """Fetches the current active manager/coach for a team from API-Sports."""
    response_data = _make_api_request("coachs", {"team": team_id})
    if response_data:
        for coach in response_data:
            for job in coach.get("career", []):
                if job.get("team", {}).get("id") == team_id and job.get("end") is None:
                    return coach
        return response_data[0]
    return None


def get_league_fixtures(league_id, season=2024):
    """Fetches ALL fixtures for a specific league and season for local pagination."""
    response_data = _make_api_request(
        "fixtures", {"league": league_id, "season": season}
    )
    return response_data if response_data else []


def get_top_scorers(league_id, season=2024):
    """Fetches the top scorers for a given league and season."""
    response_data = _make_api_request(
        "players/topscorers", {"league": league_id, "season": season}
    )

    if not response_data:
        return []

    # Slice the top 5 records
    scorers = response_data[:5]
    results = []

    for s in scorers:
        player = s.get("player", {})
        stats = s.get("statistics", [{}])[0]
        results.append(
            {
                "name": player.get("name"),
                "photo": player.get("photo"),
                "goals": stats.get("goals", {}).get("total", 0),
                "team_logo": stats.get("team", {}).get("logo"),
                "team_name": stats.get("team", {}).get("name", "Unknown"),
            }
        )
    return results


def get_league_standings(team_id, season=2024):
    """Fetches the complete league standings table for the league the team plays in."""
    initial_data = _make_api_request("standings", {"team": team_id, "season": season})

    if not initial_data or not isinstance(initial_data, list) or len(initial_data) == 0:
        return []

    try:
        league_id = initial_data[0].get("league", {}).get("id")
        if not league_id:
            return []

        full_league_data = _make_api_request(
            "standings", {"league": league_id, "season": season}
        )
        if not full_league_data:
            return []

        standings = full_league_data[0]["league"]["standings"][0]

        formatted_standings = []
        for row in standings:
            formatted_standings.append(
                {
                    "rank": row.get("rank"),
                    "team_id": row["team"]["id"],
                    "team_name": row["team"]["name"],
                    "team_logo": row["team"]["logo"],
                    "played": row["all"]["played"],
                    "win": row["all"]["win"],
                    "draw": row["all"]["draw"],
                    "lose": row["all"]["lose"],
                    "goals_for": row["all"]["goals"]["for"],
                    "goals_against": row["all"]["goals"]["against"],
                    "goals_diff": row["goalsDiff"],
                    "points": row["points"],
                    "form": list(row.get("form", "")),
                }
            )
        return formatted_standings
    except (IndexError, KeyError) as e:
        print(f"[API Error] Error parsing full standings data: {e}")
        return []
