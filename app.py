from flask import Flask, jsonify, render_template, request, redirect, url_for
from api_client import get_team_fixtures, search_teams_list, get_exact_team

app = Flask(__name__)


# 1. Search Bar
@app.route("/")
def index():
    """Renders the main landing page."""
    return render_template("index.html")


# 2. Search Handler
@app.route("/search", methods=["GET", "POST"])
def search():
    """Handles user search input."""
    if request.method == "POST":
        query = request.form.get("search_query")
        return redirect(url_for("stadiums", team_name=query))

    return redirect(url_for("index"))


# 3. Matches View
@app.route("/matches")
def matches():
    """Displays match schedules and past results."""
    return render_template("base.html", content="Matches Page Placeholder")


# 4. Stadium & Team Details View
@app.route("/stadiums")
def stadiums():
    """Displays team details and stadium information."""
    team_query = request.args.get("team_name")
    if not team_query:
        return redirect(url_for("index"))

    team_data = get_exact_team(team_query)

    if team_data:
        fixtures_data = get_team_fixtures(team_data["id"])

        return render_template("team.html", team=team_data, fixtures=fixtures_data)
    else:
        return f"<body style='background-color: #000; color: #fff; text-align: center;'><h1>Team '{team_query}' not found.</h1><a href='/' style='color: #fff;'>Try again</a></body>"


@app.route("/api/search")
def api_search():
    """Returns a JSON list of teams for the navbar dropdown."""
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

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


# 5. Dashboard / Control Panel
@app.route("/dashboard")
def dashboard():
    """Displays saved favorites and search history."""
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
