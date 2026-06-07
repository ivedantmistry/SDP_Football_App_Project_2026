import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

from utils.country_flags import COUNTRY_FLAGS

# Load environment variables
load_dotenv()


class StandardResponse:
    """
    A unified response object to standardize returns from multiple APIs.
    Prevents the application from crashing by handling errors gracefully.
    """

    def __init__(self, success, data=None, error_message=None):
        self.success = success
        self.data = data
        self.error_message = error_message


class FootballAPIManager:
    """
    Manager class responsible for handling multiple Football APIs.
    Includes a primary API (API-Sports) and a fallback API (Football-Data.org).
    """

    def __init__(self):
        self.api_sports_key = os.getenv("API_SPORTS_KEY")
        self.football_data_key = os.getenv("FOOTBALL_DATA_KEY")

        self.sports_base_url = "https://v3.football.api-sports.io"
        self.fd_base_url = "https://api.football-data.org/v4"

        # Standardized headers
        self.headers_sports = {"x-apisports-key": self.api_sports_key}
        self.headers_fd = {"X-Auth-Token": self.football_data_key}

    def _make_request(self, url, headers, params=None):
        """Core wrapper for executing HTTP GET requests with error handling."""
        start_time = time.time()
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code in [429, 403]:
                return StandardResponse(
                    success=False,
                    error_message=f"AUTH_OR_RATE_LIMIT ({response.status_code})",
                )

            response.raise_for_status()
            json_data = response.json()

            # API-Sports specific error structure handling
            if isinstance(json_data, dict) and json_data.get("errors"):
                if len(json_data["errors"]) > 0:
                    return StandardResponse(
                        success=False, error_message=str(json_data["errors"])
                    )

            print(f"[API Monitor] GET {url} | Time: {time.time() - start_time:.3f}s")
            return StandardResponse(success=True, data=json_data)

        except requests.exceptions.Timeout:
            return StandardResponse(success=False, error_message="TIMEOUT")
        except Exception as e:
            return StandardResponse(success=False, error_message=f"ERROR: {str(e)}")

    # ---------------------------------------------------------
    # Mapping & Adapters (For Fallback Architecture)
    # ---------------------------------------------------------
    def _get_fd_league_code(self, sports_league_id):
        """Maps API-Sports League IDs to Football-Data.org League Codes."""
        mapping = {39: "PL", 140: "PD", 78: "BL1", 135: "SA", 61: "FL1", 2: "CL"}
        return mapping.get(sports_league_id)

    def _adapt_fd_fixtures_to_sports_format(self, fd_matches):
        """Adapter Pattern: Converts Football-Data JSON to match API-Sports JSON structure."""
        adapted = []
        for match in fd_matches:
            status_map = {
                "FINISHED": "FT",
                "IN_PLAY": "Live",
                "PAUSED": "HT",
                "TIMED": "NS",
                "SCHEDULED": "NS",
            }
            short_status = status_map.get(match.get("status"), match.get("status"))

            adapted.append(
                {
                    "fixture": {
                        "id": match.get("id"),
                        "date": match.get("utcDate"),
                        "status": {"short": short_status},
                    },
                    "league": {"round": f"Matchday {match.get('matchday')}"},
                    "teams": {
                        "home": {
                            "name": match["homeTeam"].get("shortName")
                            or match["homeTeam"]["name"],
                            "logo": match["homeTeam"].get("crest"),
                        },
                        "away": {
                            "name": match["awayTeam"].get("shortName")
                            or match["awayTeam"]["name"],
                            "logo": match["awayTeam"].get("crest"),
                        },
                    },
                    "goals": {
                        "home": match["score"]["fullTime"]["home"]
                        if match.get("score")
                        else None,
                        "away": match["score"]["fullTime"]["away"]
                        if match.get("score")
                        else None,
                    },
                }
            )
        return adapted

    # ---------------------------------------------------------
    # Core Feature Methods (Used by app.py)
    # ---------------------------------------------------------

    def get_league_fixtures(self, league_id, season=2024):
        """Fetches ALL fixtures for a specific league with Fallback Architecture."""
        url = f"{self.sports_base_url}/fixtures"
        params = {"league": league_id, "season": season}

        response = self._make_request(url, self.headers_sports, params)
        if response.success and response.data:
            return response.data.get("response", [])

        # Fallback to Football-Data
        fd_code = self._get_fd_league_code(league_id)
        if fd_code:
            fd_url = (
                f"{self.fd_base_url}/competitions/{fd_code}/matches?season={season}"
            )
            fd_response = self._make_request(fd_url, self.headers_fd)
            if fd_response.success and fd_response.data.get("matches"):
                print("[Fallback] Data loaded from Football-Data API.")
                return self._adapt_fd_fixtures_to_sports_format(
                    fd_response.data["matches"]
                )
        return []

    def get_top_scorers(self, league_id, season=2024):
        """Fetches the top 5 scorers for a given league and season."""
        url = f"{self.sports_base_url}/players/topscorers"
        response = self._make_request(
            url, self.headers_sports, {"league": league_id, "season": season}
        )

        if not response.success or not response.data:
            return []

        scorers = response.data.get("response", [])[:5]
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

    def search_teams_list(self, query):
        """Searches for teams matching the query."""
        url = f"{self.sports_base_url}/teams"
        response = self._make_request(url, self.headers_sports, {"search": query})

        if not response.success or not response.data:
            return []

        response_data = response.data.get("response", [])
        results = []
        for item in response_data:
            team = item.get("team", {})
            venue = item.get("venue", {})

            founded = team.get("founded") or "an unknown year"
            country = team.get("country", "Unknown")
            city = venue.get("city", country)
            surface = venue.get("surface", "grass")

            dynamic_desc = (
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
                    "description": dynamic_desc,
                }
            )
        return results

    def get_exact_team(self, team_name):
        """Finds one specific team for the detail page."""
        search_term = team_name.split()[0]
        teams = self.search_teams_list(search_term)
        for team in teams:
            if team["name"].lower() == team_name.lower():
                return team
        return teams[0] if teams else None

    def get_team_fixtures(self, team_id):
        """Fetches past and upcoming fixtures for a specific team."""
        url = f"{self.sports_base_url}/fixtures"
        response = self._make_request(
            url, self.headers_sports, {"team": team_id, "season": 2024}
        )

        if not response.success or not response.data:
            return {"form": [], "next_match": None, "all_matches": []}

        response_data = response.data.get("response", [])

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
                result, score_display = "D", "? - ?"
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
                formatted_date, time_12hr = raw_date_str[:10], raw_date_str[11:16]

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
                    "fixture_id": match["fixture"]["id"],
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
                    "league_id": match["league"]["id"],
                    "result": result,
                }
            )

        return {
            "form": form_data,
            "next_match": next_match_data,
            "all_matches": all_fixtures_data,
        }

    def fetch_squad_from_api(self, team_id):
        """Fetches the current full roster for a team from API-Sports and groups them by position."""
        url = f"{self.sports_base_url}/players"
        response = self._make_request(
            url, self.headers_sports, {"team": team_id, "season": 2024, "page": 1}
        )

        if not response.success or not response.data:
            return {}

        players_data = list(response.data.get("response", []))

        # Check for page 2 (Optional but good for full squads)
        page2_response = self._make_request(
            url, self.headers_sports, {"team": team_id, "season": 2024, "page": 2}
        )
        if page2_response.success and page2_response.data:
            players_data.extend(page2_response.data.get("response", []))

        grouped_squad = {
            "Goalkeepers": [],
            "Defenders": [],
            "Midfielders": [],
            "Attackers": [],
        }

        for item in players_data:
            p_info = item.get("player", {})
            stats = item.get("statistics", [])

            # 1. Lấy thông tin cơ bản
            number = None
            pos = None

            # 2. Lấy dữ liệu từ block statistics nếu tồn tại
            if stats and len(stats) > 0:
                games = stats[0].get("games", {})
                pos = games.get("position")
                number = games.get("number")

            # 3. Fallback: Nếu không tìm thấy số áo trong stats, tìm trong p_info
            if not number:
                number = p_info.get("number")  # Một số API-Sports version để ở đây

            player_dict = {
                "id": p_info.get("id"),
                "name": p_info.get("name"),
                "age": p_info.get("age"),
                "number": number,
                "position": pos,
                "photo": p_info.get("photo"),
                "nationality": p_info.get("nationality"),
                "flag_url": self.get_flag_url(p_info.get("nationality")),
                "height": p_info.get("height"),
            }

            # 4. Gom nhóm an toàn
            if pos in ["Goalkeeper", "Defender", "Midfielder", "Attacker"]:
                grouped_squad[f"{pos}s"].append(player_dict)

        return {k: v for k, v in grouped_squad.items() if len(v) > 0}

    def get_team_coach(self, team_id):
        """Fetches the current active manager/coach for a team."""
        url = f"{self.sports_base_url}/coachs"
        response = self._make_request(url, self.headers_sports, {"team": team_id})

        if response.success and response.data:
            response_data = response.data.get("response", [])
            for coach in response_data:
                for job in coach.get("career", []):
                    if (
                        job.get("team", {}).get("id") == team_id
                        and job.get("end") is None
                    ):
                        return coach
            return response_data[0] if response_data else None
        return None

    @staticmethod
    def get_flag_url(country_name):
        """Returns the URL of the flag image for a given country name."""
        # Use the COUNTRY_FLAGS mapping to get the code, then construct the URL
        code = COUNTRY_FLAGS.get(country_name)
        return f"https://flagcdn.com/w20/{code}.png" if code else None

    def get_team_statistics(self, league_id, season, team_id):
        """
        Fetches detailed statistics for a team within a specific league and season.
        Used for the Team vs Team comparison feature.
        """
        url = f"{self.sports_base_url}/teams/statistics"
        params = {"league": league_id, "season": season, "team": team_id}

        # Execute the request using the centralized robust wrapper
        response = self._make_request(url, self.headers_sports, params)

        if response.success and response.data:
            return response.data.get("response")

        # Note: Fallback API (Football-Data) often lacks detailed statistics in free tiers.
        # Returning None allows the frontend to handle the empty state gracefully.
        print(
            f"[API Manager] Warning: Could not fetch statistics for Team ID {team_id}."
        )
        return None

    def get_teams_in_league(self, league_id, season=2024):
        """
        Fetches all teams participating in a specific league for a given season.
        Used to populate the opponent selection dropdown/modal.
        """
        url = f"{self.sports_base_url}/teams"
        params = {"league": league_id, "season": season}

        response = self._make_request(url, self.headers_sports, params)
        if response.success and response.data:
            # Returns a list of dictionaries: [{"team": {...}, "venue": {...}}, ...]
            return response.data.get("response", [])
        return []

    def get_fixture_details(self, fixture_id):
        """Fetches comprehensive details for a single match (score, events, stats)."""
        url = f"{self.sports_base_url}/fixtures"
        params = {"id": fixture_id}

        # Using the centralized robust wrapper to handle this critical request
        response = self._make_request(url, self.headers_sports, params)

        if response.success and response.data and response.data.get("response"):
            # Returns a single fixture dictionary with all details (events, lineups, stats)
            return response.data["response"][0]

        print(
            f"[API Manager] Warning: Could not fetch details for Fixture ID {fixture_id}."
        )
        return None

    def get_league_standings(self, team_id, season=2024):
        """Fetches the complete league standings table for the league the team plays in."""
        url = f"{self.sports_base_url}/standings"
        response = self._make_request(
            url, self.headers_sports, {"team": team_id, "season": season}
        )

        if not response.success or not response.data:
            return []

        initial_data = response.data.get("response", [])
        if not initial_data or len(initial_data) == 0:
            return []

        try:
            league_id = initial_data[0].get("league", {}).get("id")
            if not league_id:
                return []

            full_league_response = self._make_request(
                url, self.headers_sports, {"league": league_id, "season": season}
            )
            if not full_league_response.success or not full_league_response.data:
                return []

            full_league_data = full_league_response.data.get("response", [])
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


# Initialize a global instance to be imported by app.py
api_manager = FootballAPIManager()
