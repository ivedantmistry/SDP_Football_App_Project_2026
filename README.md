# Football Match, Team & Stadium Explorer

**Course:** Software Development Practice - Final Project  
**Term:** SoSe 2026 - Stuttgart Campus

---

## Team Members

- **Vedant Mistry** - (100008344)
- **Phong Dinh** - (100008610)

---

# 1. Project Scope

We built a Flask web application inspired by FotMob that allows users to explore football leagues, teams, and matches. Users can view match schedules, team statistics and squads, stadium locations and compare two teams head-to-head.

## Core Features

- **Fixtures & Top Scorers:** Matches across top leagues with top scorers of each league.
- **Search:** Search for teams.
- **Match Data:** Display schedules and past results.
- **Team Details:** Detailed team profiles including current manager, stadium details, full player roster grouped by position, and league standings.
- **Team Comparison Dashboard:** A head-to-head statistical comparison tool between teams within the same league.
- **Interactive Map:** Plot stadium locations using Folium.
- **Favorites:** Save favorite teams to your own tab.

---

# 2. Initial Project Structure

```text
football-explorer/
│
├── app.py                      # Main Flask application and routing logic
├── football_api_manager.py     # Centralized API Manager (Primary & Fallback Logic)
├── db_manager.py               # SQLite database connection, caching, and queries
├── utils/
│   └── country_flags.py        # Static mapping for FlagCDN integration
├── database.db                 # Local SQLite database (Generated on run)
├── requirements.txt            # Project dependencies
├── static/
│   └── css/style.css           # Custom UI styling and overrides
│
└── templates/
    ├── base.html               # Master Bootstrap layout template
    ├── index.html              # Home page (Leagues, Matches, Top Scorers)
    ├── team.html               # Team profile, squad list, and stadium map
    ├── compare.html            # Team vs Team statistical comparison dashboard
    ├── favourites.html         # Saved favorites and search history
    └── match_details.html      # Simplified match details view
```

---

# 3. Task Distribution

Work is distributed evenly across the stack to ensure both members contribute to API integration, database management, and UI development.

## Vedant Mistry Tasks

- Database Architecture: Developed db_manager.py, designed the SQLite schema for users, favorites, and search history.
- Seed Logic: Implemented seed_script for initial database population.
- Mapping & Visualization: Developed Folium map generation and stadium geocoding logic.
- User Features: Built the Favorites system (favourites.html logic/template) and League Standings tables.

## Phong Dinh Tasks

- Core API Architecture: Built football_api_manager.py, including the dual-API Fallback mechanism and JSON data adapter patterns.
- Backend Routing: Developed all primary Flask routes in app.py.
- Frontend & UI: Designed and developed core interfaces:
  - Home Page (index.html) with dynamic league, matchday and top scorers.
  - Team Overview and Squad pages (team.html).
  - Comparison Dashboard (compare.html).
- Data Integration: Implemented data-flattening logic to bridge API response structures with frontend template requirements.

---

# 4. API & Backend Architecture

## External APIs

### Primary API: API-Sports (v3)

Used for:

- League fixtures from the top leagues
- Full squad rosters and player details (height, age, jersey number)
- League standings and tables

### 2. Fallback API: Football-Data.org (v4)

Used for:

- A custom \_adapt_fd_fixtures_to_sports_format method translates the Football-Data JSON structure into the API-Sports format, allowing the frontend to render seamlessly without knowing which API provided the data.

### 3. Supplementary APIs:

- Nominatim (Geopy): Converts stadium names and cities into GPS coordinates.
- FlagCDN: Dynamically fetches country flags for player nationalities.

---

# Technologies Used

- **Backend: Python 3, Flask, SQLite3**
- **Frontend: HTML5, CSS3, Bootstrap 5, Jinja2 Templating**
- **Mapping & Geo: Folium, Geopy**
- **HTTP & Utilities: requests, python-dotenv, re, datetime**

---

# Planned Features for Final Submission

- Team comparison dashboard
- Match statistics visualizations
- Show search history
- Responsive mobile-friendly UI

---

# Week 6 Submission Checklist

- [x] Confirmed project scope
- [x] Initial project structure created
- [x] Task distribution finalized
- [x] API and backend plan documented
- [x] Empty project files committed
- [x] Professor invited as collaborator

---

This project is developed as part of the Software Development Practice course. The application focuses on API integration, backend development, database management, and interactive visualization techniques using Flask and Python.
