from datetime import datetime

import requests
import os
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_SPORTS_KEY")

HEADERS = {"x-apisports-key": API_KEY}


def search_teams_list(query):
    """Searches for teams matching the query and returns a list of results with dynamic descriptions."""
    url = "https://v3.football.api-sports.io/teams"
    querystring = {"search": query}

    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        response.raise_for_status()
        data = response.json()

        if data.get("errors"):
            print(f"API Error (Search): {data['errors']}")

        results = []

        if data.get("response"):
            for item in data["response"]:
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

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API-Football: {e}")
        return []


def get_exact_team(team_name):
    """
    Finds one specific team for the detail page.
    """
    search_term = team_name.split()[0]
    teams = search_teams_list(search_term)

    # Try to find an exact name match first
    for team in teams:
        if team["name"].lower() == team_name.lower():
            return team

    if teams:
        return teams[0]

    return None


def get_team_fixtures(team_id):
    """Fetches past and upcoming fixtures for a specific team, returning form and next match data."""
    if not API_KEY:
        return {"form": [], "next_match": None}

    base_url = "https://v3.football.api-sports.io/fixtures"

    current_season = 2024

    try:
        res = requests.get(
            base_url,
            headers=HEADERS,
            params={"team": team_id, "season": current_season},
        )
        res.raise_for_status()
        data = res.json()

        if data.get("errors"):
            return {"form": [], "next_match": None}

        fixtures_list = data.get("response", [])

        past_matches = []
        future_matches = []

        # Categorize matches into past and future
        for match in fixtures_list:
            status = match["fixture"]["status"]["short"]
            if status in ["FT", "AET", "PEN"]:  # Finished
                past_matches.append(match)
            elif status in ["NS", "TBD"]:
                future_matches.append(match)

        # Sort past matches (most recent first) and get the last 5
        past_matches.sort(key=lambda x: x["fixture"]["timestamp"], reverse=True)
        last_5 = past_matches[:5][::-1]

        # Sort future matches by timestamp ascending (soonest first)
        future_matches.sort(key=lambda x: x["fixture"]["timestamp"])
        next_1 = future_matches[0] if future_matches else None

        if not next_1 and len(past_matches) > 5:
            next_1 = past_matches[5]

        # Format Form Data for UI
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

        # Format Next Match Data for UI
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

            # 6. Format All Matches List
            all_fixtures_data = []
        for match in fixtures_list:
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
                    "home_goals": match["goals"]["home"],
                    "away_goals": match["goals"]["away"],
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

    except requests.exceptions.RequestException as e:
        print(f"Error fetching fixtures: {e}")
        return {"form": [], "next_match": None}


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
    if not API_KEY:
        return []

    url = "https://v3.football.api-sports.io/players"
    players_data = []

    try:
        res = requests.get(
            url, headers=HEADERS, params={"team": team_id, "season": 2024, "page": 1}
        )
        data = res.json()
        total_pages = data.get("paging", {}).get("total", 1)
        players_data.extend(data.get("response", []))

        # Fetch page 2 if squad is large (avoids N+1 query issue)
        if total_pages > 1:
            res2 = requests.get(
                url,
                headers=HEADERS,
                params={"team": team_id, "season": 2024, "page": 2},
            )
            players_data.extend(res2.json().get("response", []))

        grouped_squad = {
            "Goalkeepers": [],
            "Defenders": [],
            "Midfielders": [],
            "Attackers": [],
        }

        # Process and extract specific player attributes
        for item in players_data:
            p_info = item.get("player", {})

            # Extract number and position from statistics array
            pon = None
            pos = None
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

            # Group players based on their role
            if pos == "Goalkeeper":
                grouped_squad["Goalkeepers"].append(player_dict)
            elif pos == "Defender":
                grouped_squad["Defenders"].append(player_dict)
            elif pos == "Midfielder":
                grouped_squad["Midfielders"].append(player_dict)
            elif pos == "Attacker":
                grouped_squad["Attackers"].append(player_dict)

        # Remove empty position groups
        return {k: v for k, v in grouped_squad.items() if len(v) > 0}
    except Exception as e:
        print(f"Error fetching squad data: {e}")
        return {}


def get_team_coach(team_id):
    """Fetches the current active manager/coach for a team from API-Sports."""
    if not API_KEY:
        return None

    url = "https://v3.football.api-sports.io/coachs"
    try:
        response = requests.get(url, headers=HEADERS, params={"team": team_id})
        response.raise_for_status()
        data = response.json()

        if data.get("response"):
            coaches_list = data["response"]

            # Iterate through career history to find the active tenure (end date is None)
            for coach in coaches_list:
                career_history = coach.get("career", [])

                for job in career_history:
                    job_team_id = job.get("team", {}).get("id")

                    if job_team_id == team_id and job.get("end") is None:
                        return coach

            # Fallback to the first coach if no active tenure is strictly defined
            return coaches_list[0]

        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coach data: {e}")
        return None


def get_league_fixtures(league_id, season=2024):
    """Fetches ALL fixtures for a specific league and season for local pagination."""
    if not API_KEY:
        return []

    url = "https://v3.football.api-sports.io/fixtures"
    try:
        # Fetch all fixtures for the league and season
        res = requests.get(
            url, headers=HEADERS, params={"league": league_id, "season": season}
        )
        res.raise_for_status()
        data = res.json()

        if data.get("errors"):
            print(f"API Error (League Fixtures): {data['errors']}")
            return []

        return data.get("response", [])
    except Exception as e:
        print(f"Error fetching league fixtures: {e}")
        return []


def get_top_scorers(league_id, season=2024):
    """Fetches the top scorers for a given league and season."""
    if not API_KEY:
        return []
    url = "https://v3.football.api-sports.io/players/topscorers"
    try:
        res = requests.get(
            url, headers=HEADERS, params={"league": league_id, "season": season}
        )
        res.raise_for_status()
        data = res.json()

        # Slice the top 5 records
        scorers = data.get("response", [])[:5]
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
                }
            )
        return results
    except Exception as e:
        print(f"Error fetching top scorers: {e}")
        return []
