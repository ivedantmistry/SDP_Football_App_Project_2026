from flask import Flask, render_template, request, redirect, url_for

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
    """Displays team details, badges, and stadium information."""

    return render_template("base.html", content="Stadiums Page Placeholder")


# 5. Dashboard / Control Panel
@app.route("/dashboard")
def dashboard():
    """Displays saved favorites and search history."""
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
