from datetime import datetime
import re
import time
from flask import Flask, jsonify, render_template, request, redirect, url_for
from api_client import (
    fetch_squad_from_api,
    get_team_coach,
    get_top_scorers,
    search_teams_list,
    get_exact_team,
    get_league_standings,
)
from football_api_manager import api_manager
import db_manager
import folium
from geopy.geocoders import Nominatim
from urllib.parse import quote

app = Flask(__name__)

db_manager.init_db()

CACHE = {
    "fixtures_by_league": {},
    "scorers": {},
}
CACHE_DURATION = 3600


@app.route("/")
def index():
    """Renders the Home Page with dynamic date picker and interactive leagues."""
    leagues = db_manager.get_all_leagues()
    current_time = time.time()

    league_id_str = request.args.get("league_id", "39")
    try:
        current_league_id = int(league_id_str)
    except ValueError:
        current_league_id = 39

    current_league_name = "Premier League"
    current_league_logo = ""
    for ls in leagues:
        if ls["id"] == current_league_id:
            current_league_name = ls["name"]
            current_league_logo = ls["logo"]
            break

    cache_key_league = f"all_fixtures_{current_league_id}"
    if cache_key_league in CACHE["fixtures_by_league"] and (
        current_time - CACHE["fixtures_by_league"][cache_key_league]["timestamp"]
        < CACHE_DURATION
    ):
        all_matches = CACHE["fixtures_by_league"][cache_key_league]["data"]
    # Sửa từ: all_matches = get_league_fixtures(current_league_id)
    # Thành thế này:
    else:
        all_matches = api_manager.get_league_fixtures(current_league_id)

        # all_matches = api_manager.get_league_fixtures(current_league_id)

        if all_matches:
            CACHE["fixtures_by_league"][cache_key_league] = {
                "data": all_matches,
                "timestamp": current_time,
            }

    # Extract unique rounds from the matches
    rounds = set()
    for m in all_matches:
        rounds.add(m["league"]["round"])

    # Helper function to extract numeric part of round for proper sorting
    def extract_round_num(r_str):
        if not r_str:
            return 0
        match = re.search(r"\d+", str(r_str))
        return int(match.group()) if match else 0

    sorted_rounds = sorted(list(rounds), key=extract_round_num)

    # Get the selected round from query parameters
    selected_round = request.args.get("round")

    # If no round is selected, choose the most recent finished round or the latest round
    if not selected_round and sorted_rounds:
        finished_rounds = [
            m["league"]["round"]
            for m in all_matches
            if m["fixture"]["status"]["short"] in ["FT", "AET", "PEN"]
        ]
        if finished_rounds:
            selected_round = sorted(list(set(finished_rounds)), key=extract_round_num)[
                -1
            ]
        else:
            selected_round = sorted_rounds[-1]

    # Determine previous and next rounds for navigation
    prev_round = None
    next_round = None
    if selected_round in sorted_rounds:
        current_idx = sorted_rounds.index(selected_round)
        if current_idx > 0:
            prev_round = sorted_rounds[current_idx - 1]
        if current_idx < len(sorted_rounds) - 1:
            next_round = sorted_rounds[current_idx + 1]

    # Filter matches for the selected round
    round_matches = [m for m in all_matches if m["league"]["round"] == selected_round]

    # If no matches found for the selected round, fallback to showing all matches for the league
    round_matches = [m for m in all_matches if m["league"]["round"] == selected_round]

    #   Display the round in a user-friendly format (e.g., "Matchday 1", "Round 2", etc.)
    if selected_round:
        round_num = extract_round_num(selected_round)
        display_round = f"Matchday {round_num}" if round_num > 0 else selected_round
    else:
        display_round = "No Matches"

    round_dates = ""
    if round_matches:
        dates = [
            m["fixture"]["date"] for m in round_matches if m["fixture"].get("date")
        ]
        if dates:
            start_date_str = min(dates)[:10]
            end_date_str = max(dates)[:10]
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").strftime(
                    "%b %d"
                )
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%b %d")
                round_dates = (
                    start_date
                    if start_date == end_date
                    else f"{start_date} - {end_date}"
                )
            except ValueError:
                pass

    # Check if cached top scorers data is available for the selected league
    # Using league_id as the cache key for top scorers since they are typically league-specific
    cache_key_scorers = str(current_league_id)
    if cache_key_scorers in CACHE["scorers"] and (
        current_time - CACHE["scorers"][cache_key_scorers]["timestamp"] < CACHE_DURATION
    ):
        top_scorers = CACHE["scorers"][cache_key_scorers]["data"]
    else:
        top_scorers = get_top_scorers(current_league_id)

        # top_scorers = api_manager.get_top_scorers(current_league_id)

        if top_scorers:
            CACHE["scorers"][cache_key_scorers] = {
                "data": top_scorers,
                "timestamp": current_time,
            }

    return render_template(
        "index.html",
        leagues=leagues,
        league_matches=round_matches,
        top_scorers=top_scorers,
        current_league_id=current_league_id,
        current_league_name=current_league_name,
        current_league_logo=current_league_logo,
        selected_round=selected_round,
        display_round=display_round,
        prev_round=prev_round,
        next_round=next_round,
        round_dates=round_dates,
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    """Handles user search input."""
    if request.method == "POST":
        query = request.form.get("search_query")
        return redirect(url_for("stadiums", team_name=query))

    return redirect(url_for("index"))


@app.route("/api/history", methods=["GET"])
def get_history():
    """Retrieves the user's recent search history from the local database."""
    recent_searches = db_manager.get_recent_searches()
    return jsonify(recent_searches)


@app.route("/api/history", methods=["POST"])
def save_history():
    """Saves a successfully searched team to the local search history."""
    data = request.json
    team_name = data.get("team_name")
    team_logo = data.get("team_logo")

    if team_name and team_logo:
        db_manager.save_search(team_name, team_logo)
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Missing data"}), 400


@app.route("/api/history", methods=["DELETE"])
def delete_history():
    """Deletes a specific entry or clears all recent searches."""
    data = request.json
    team_name = data.get("team_name")

    if team_name:
        db_manager.delete_search(team_name)
    else:
        db_manager.clear_all_searches()

    return jsonify({"status": "success"}), 200


@app.route("/matches")
def matches():
    """Displays match schedules and past results."""
    return render_template("base.html", content="Matches Page Placeholder")


@app.route("/stadiums")
def stadiums():
    """Displays team details, stadium information, and dynamically loads the squad."""
    team_query = request.args.get("team_name")
    if not team_query:
        return redirect(url_for("index"))

    team_data = db_manager.get_team_profile(team_query)
    if not team_data:
        team_data = get_exact_team(team_query)

    if team_data:
        team_id = team_data["id"]

        fixtures_data = api_manager.get_team_fixtures(team_id)

        team_league_id = 39
        if fixtures_data and fixtures_data.get("all_matches"):
            league_counts = {}
            for match in fixtures_data["all_matches"]:
                lid = match.get("league_id")
                if lid:
                    league_counts[lid] = league_counts.get(lid, 0) + 1

            if league_counts:
                team_league_id = max(league_counts, key=league_counts.get)

        coach_data = db_manager.get_team_coach_local(team_id)
        if not coach_data:
            api_coach = get_team_coach(team_id)

            if api_coach:
                db_manager.insert_coach(
                    coach_id=api_coach.get("id"),
                    name=api_coach.get("name"),
                    age=api_coach.get("age"),
                    nationality=api_coach.get("nationality"),
                    photo=api_coach.get("photo"),
                    team_id=team_id,
                    team_league_id=team_league_id,
                )
                coach_data = db_manager.get_team_coach_local(team_id)
        players = db_manager.get_team_players(team_id)
        if not players:
            print(f"Squad not in database. Fetching from API for Team ID: {team_id}...")
            api_players_dict = fetch_squad_from_api(team_id)

            if api_players_dict:
                for position_group, player_list in api_players_dict.items():
                    for p in player_list:
                        db_manager.insert_player(
                            player_id=p.get("id"),
                            name=p.get("name"),
                            age=p.get("age"),
                            number=p.get("number"),
                            position=p.get("position"),
                            photo=p.get("photo"),
                            nationality=p.get("nationality"),
                            flag_url=p.get("flag_url"),
                            height=p.get("height"),
                            team_id=team_id,
                        )
                players = db_manager.get_team_players(team_id)
        else:
            print(f"Loaded {len(players)} players directly from local database!")

        grouped_squad = {
            "Goalkeepers": [],
            "Defenders": [],
            "Midfielders": [],
            "Attackers": [],
        }
        for p in players:
            pos = p.get("position") if isinstance(p, dict) else p[4]

            if pos == "Goalkeeper":
                grouped_squad["Goalkeepers"].append(p)
            elif pos == "Defender":
                grouped_squad["Defenders"].append(p)
            elif pos == "Midfielder":
                grouped_squad["Midfielders"].append(p)
            elif pos == "Attacker":
                grouped_squad["Attackers"].append(p)

        final_squad = {k: v for k, v in grouped_squad.items() if len(v) > 0}

        is_fav = db_manager.is_favorite(team_id)

        cache_key_standings = f"standings_team_{team_id}"
        standings_data = db_manager.get_cached_api_data(
            cache_key_standings, hours_valid=24
        )

        if not standings_data:
            print(
                f"Standings not in cache. Fetching from API for Team ID: {team_id}..."
            )
            standings_data = get_league_standings(team_id)
            if standings_data:
                db_manager.save_cached_api_data(cache_key_standings, standings_data)
        stadium_map_html = get_stadium_map_html(
            team_data.get("stadium_name", ""), team_data.get("stadium_location", "")
        )

        stadium_name = team_data.get("stadium_name", "")
        stadium_location = team_data.get("stadium_location", "")
        destination_query = quote(f"{stadium_name}, {stadium_location}")
        directions_url = (
            f"https://www.google.com/maps/dir/?api=1&destination={destination_query}"
        )

        return render_template(
            "team.html",
            team=team_data,
            fixtures=fixtures_data,
            squad=final_squad,
            coach=coach_data,
            is_favorite=is_fav,
            standings=standings_data,
            stadium_map=stadium_map_html,
            directions_url=directions_url,
            team_league_id=team_league_id,
        )
    else:
        return f"<body style='background-color: #000; color: #fff; text-align: center;'><h1>Team '{team_query}' not found.</h1><a href='/' style='color: #fff;'>Try again</a></body>"


@app.route("/api/search")
def api_search():
    """Returns a JSON list of teams for the navbar dropdown."""
    query = request.args.get("q", "")
    if not query or len(query) < 3:
        return jsonify([])

    # Prioritize Local Seed Database
    results = db_manager.search_local_teams(query)

    # Fallback to Live API if not found locally
    if not results:
        teams_data = search_teams_list(query)

        # teams_data = api_manager.search_teams_list(query)

        results = []
        for team in teams_data:
            results.append(
                {
                    "name": team["name"],
                    "badge": team["badge_url"],
                    "stadium": team["stadium_name"],
                }
            )

    return jsonify(results)


@app.route("/dashboard")
def dashboard():
    """Displays saved favorites and search history."""
    favorites = db_manager.get_all_favorites()
    return render_template("dashboard.html", favorites=favorites)


@app.route("/compare")
def compare_teams():
    """
    Renders the Team vs Team comparison dashboard (FotMob style).
    Requires a primary team (team1) and an optional secondary team (team2).
    """
    # Retrieve query parameters
    team1_id = request.args.get("team1")
    league_id = request.args.get("league", "39")  # Default to Premier League
    season = 2024  # Current active season

    # Redirect to home if the primary team ID is missing
    if not team1_id:
        return redirect(url_for("index"))

    # Fetch statistics for the primary team
    stats1 = api_manager.get_team_statistics(league_id, season, team1_id)
    if not stats1:
        return "<body style='background-color: #000; color: #fff; text-align: center; margin-top: 50px;'><h1>Statistics not available for this team.</h1></body>"

    league_teams = api_manager.get_teams_in_league(league_id, season)

    if league_teams:
        league_teams.sort(key=lambda x: x["team"]["name"])

    # Fetch statistics for the secondary team if selected by the user
    team2_id = request.args.get("team2")
    stats2 = None
    if team2_id:
        stats2 = api_manager.get_team_statistics(league_id, season, team2_id)

    color1 = get_team_color(stats1["team"]["name"])
    color2 = "#10b981"

    if stats2:
        color2 = get_team_color(stats2["team"]["name"])

        if color1 == color2:
            color2 = "#ffffff"

    return render_template(
        "compare.html",
        stats1=stats1,
        stats2=stats2,
        league_id=league_id,
        league_teams=league_teams,
        color1=color1,
        color2=color2,
    )


def get_team_color(team_name):
    """Returns a hex color code based on the team name for consistent theming in the comparison dashboard."""
    name = team_name.lower()

    # Hardcoded colors for popular teams to ensure they stand out in the comparison dashboard
    if any(
        x in name
        for x in [
            "bayern",
            "arsenal",
            "liverpool",
            "manchester united",
            "roma",
            "milan",
        ]
    ):
        return "#ef4444"
    elif any(x in name for x in ["chelsea", "everton", "schalke", "leicester"]):
        return "#3b82f6"
    elif any(x in name for x in ["manchester city", "lazio", "napoli"]):
        return "#60a5fa"
    elif any(x in name for x in ["dortmund", "villareal", "norwich"]):
        return "#eab308"
    elif any(x in name for x in ["real madrid", "tottenham", "juventus", "newcastle"]):
        return "#f3f4f6"
    elif any(x in name for x in ["paris", "psg"]):
        return "#1e3a8a"

    # If the team is not in the hardcoded list, generate a consistent color based on its name
    colors = ["#10b981", "#8b5cf6", "#f59e0b", "#06b6d4", "#ec4899"]
    return colors[sum(ord(c) for c in name) % len(colors)]


@app.route("/api/favorites/toggle", methods=["POST"])
def api_toggle_favorite():
    """API endpoint to add/remove a team from favorites."""
    data = request.json
    team_id = data.get("team_id")
    team_name = data.get("team_name")
    team_logo = data.get("team_logo")

    if not team_id:
        return jsonify({"error": "Missing team_id"}), 400

    is_fav = db_manager.toggle_favorite(team_id, team_name, team_logo)
    return jsonify({"success": True, "is_favorite": is_fav})


def get_stadium_map_html(stadium_name, city):
    """Geocodes the stadium and returns a dark-mode Folium map as an HTML string."""
    geolocator = Nominatim(user_agent="fotmob_clone_app")

    try:
        # Try finding the exact stadium first
        location = geolocator.geocode(f"{stadium_name}, {city}")
        if not location:
            # Fallback to just the city if stadium isn't found
            location = geolocator.geocode(city)

        if location:
            lat, lon = location.latitude, location.longitude
        else:
            # Default to London if all geocoding fails
            lat, lon = 51.5074, -0.1278

        # Create Folium Map using a dark theme!
        m = folium.Map(
            location=[lat, lon],
            zoom_start=15,
            tiles="CartoDB dark_matter",
            control_scale=True,
        )

        # Add a sleek marker
        folium.Marker(
            [lat, lon],
            tooltip=stadium_name,
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

        return m._repr_html_()

    except Exception as e:
        print(f"Geocoding error: {e}")
        return "<div class='text-center text-muted p-4' style='height: 100%; display: flex; align-items: center; justify-content: center;'>Map currently unavailable</div>"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
