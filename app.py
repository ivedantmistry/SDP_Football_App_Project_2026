import re
import time
from flask import Flask, jsonify, render_template, request, redirect, url_for
from api_client import (
    fetch_squad_from_api,
    get_league_fixtures,
    get_team_coach,
    get_team_fixtures,
    get_top_scorers,
    search_teams_list,
    get_exact_team,
)
import db_manager

app = Flask(__name__)

# Initialize the SQLite database tables
db_manager.init_db()

# Prevents excessive API calls for Home Page dynamic data
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

    # Get league_id from query parameters, default to 39 (Premier League) if not provided or invalid
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

    # Check if cached data is available for the selected league
    cache_key_league = f"all_fixtures_{current_league_id}"
    if cache_key_league in CACHE["fixtures_by_league"] and (
        current_time - CACHE["fixtures_by_league"][cache_key_league]["timestamp"]
        < CACHE_DURATION
    ):
        all_matches = CACHE["fixtures_by_league"][cache_key_league]["data"]
    else:
        all_matches = get_league_fixtures(current_league_id)
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

    # Check if cached top scorers data is available for the selected league
    # Using league_id as the cache key for top scorers since they are typically league-specific
    cache_key_scorers = str(current_league_id)
    if cache_key_scorers in CACHE["scorers"] and (
        current_time - CACHE["scorers"][cache_key_scorers]["timestamp"] < CACHE_DURATION
    ):
        top_scorers = CACHE["scorers"][cache_key_scorers]["data"]
    else:
        top_scorers = get_top_scorers(current_league_id)
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


# 4. Stadium & Team Details View
@app.route("/stadiums")
def stadiums():
    """Displays team details, stadium information, and dynamically loads the squad."""
    team_query = request.args.get("team_name")
    if not team_query:
        return redirect(url_for("index"))

    # Attempt to fetch basic team profile from Local Seed DB first
    team_data = db_manager.get_team_profile(team_query)
    if not team_data:
        team_data = get_exact_team(team_query)

    if team_data:
        team_id = team_data["id"]
        fixtures_data = get_team_fixtures(team_id)

        # Coach Lazy Loading Logic
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
                )
                coach_data = db_manager.get_team_coach_local(team_id)

        # Squad Lazy Loading Logic
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

        # Group players by position for UI presentation
        grouped_squad = {
            "Goalkeepers": [],
            "Defenders": [],
            "Midfielders": [],
            "Attackers": [],
        }
        for p in players:
            # Handle tuple from SQLite vs dictionary from direct return
            pos = p.get("position") if isinstance(p, dict) else p[4]

            if pos == "Goalkeeper":
                grouped_squad["Goalkeepers"].append(p)
            elif pos == "Defender":
                grouped_squad["Defenders"].append(p)
            elif pos == "Midfielder":
                grouped_squad["Midfielders"].append(p)
            elif pos == "Attacker":
                grouped_squad["Attackers"].append(p)

        # Clean up empty groups
        final_squad = {k: v for k, v in grouped_squad.items() if len(v) > 0}

        return render_template(
            "team.html",
            team=team_data,
            fixtures=fixtures_data,
            squad=final_squad,
            coach=coach_data,
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
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
