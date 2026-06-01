from flask import Flask, jsonify, render_template, request, redirect, url_for
from api_client import (
    fetch_squad_from_api,
    get_team_coach,
    get_team_fixtures,
    search_teams_list,
    get_exact_team,
    get_league_standings
)
import db_manager

app = Flask(__name__)

db_manager.init_db()


@app.route("/")
def index():
    """Renders the main landing page."""
    return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    """Handles user search input."""
    if request.method == "POST":
        query = request.form.get("search_query")
        return redirect(url_for("stadiums", team_name=query))

    return redirect(url_for("index"))


@app.route("/api/history", methods=["GET"])
def get_history():
    recent_searches = db_manager.get_recent_searches()
    return jsonify(recent_searches)


@app.route("/api/history", methods=["POST"])
def save_history():
    data = request.json
    team_name = data.get("team_name")
    team_logo = data.get("team_logo")

    if team_name and team_logo:
        db_manager.save_search(team_name, team_logo)
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Missing data"}), 400


@app.route("/api/history", methods=["DELETE"])
def delete_history():
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

    team_data = db_manager.get_team_profile(team_query)
    if not team_data:
        team_data = get_exact_team(team_query)

    if team_data:
        team_id = team_data["id"]
        fixtures_data = get_team_fixtures(team_id)
        standings_data = get_league_standings(team_id)

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

        return render_template(
            "team.html",
            team=team_data,
            fixtures=fixtures_data,
            squad=final_squad,
            coach=coach_data,
            standings=standings_data
        )
    else:
        return f"<body style='background-color: #000; color: #fff; text-align: center;'><h1>Team '{team_query}' not found.</h1><a href='/' style='color: #fff;'>Try again</a></body>"


@app.route("/api/search")
def api_search():
    """Returns a JSON list of teams for the navbar dropdown."""
    query = request.args.get("q", "")
    if not query or len(query) < 3:
        return jsonify([])

    results = db_manager.search_local_teams(query)

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
