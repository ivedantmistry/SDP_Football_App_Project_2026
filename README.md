# Football Match, Team & Stadium Explorer

**Course:** Software Development Practice - Final Project  
**Term:** SoSe 2026 - Stuttgart Campus  

---

## Team Members

* **Vedant Mistry** - (100008344)
* **Phong Dinh** - (100008610)

---

# 1. Project Scope

We are building a Flask web application that allows users to search for football leagues, teams, or cities. Users can explore upcoming and previous match results, view rich team details and visualize stadium locations on a map.

## Core Features

- **Search:** Search for teams and leagues.
- **Match Data:** Display schedules and past results.
- **Team Details:** Show badges and stadium information.
- **Interactive Map:** Plot stadium locations using Folium.
- **Saving Favorites**: Save favorite teams and previous searches using SQLite.

---

# 2. Initial Project Structure

```text
football-explorer/
│
├── app.py                 # Main Flask application and routes
├── api_client.py          # Handles requests to OpenLigaDB, TheSportsDB, Overpass
├── db_manager.py          # SQLite database connection and queries
├── visuals.py             # Folium map generation and Matplotlib/Plotly charts
├── database.db            # Local SQLite database (Generated on run)
├── requirements.txt       # Project dependencies (Flask, requests, folium, etc.)
├── static/
│   ├── css/style.css      # Custom styling
│   └── js/main.js         # Frontend logic (Search autocomplete)
│
└── templates/
    ├── base.html          # Bootstrap layout template
    ├── index.html         # Landing page and search bar
    ├── dashboard.html     # Control panel for saved favorites and history
    └── map.html           # Map visualization page
```

---

# 3. Task Distribution

Work is distributed evenly across the stack to ensure both members contribute to API integration, database management, and UI development.

## Vedant Mistry Tasks

- Implements `api_client.py` for:
  - OpenLigaDB (match schedules)
  - Overpass API (GPS coordinates)
- Implements `visuals.py` for:
  - Folium maps
  - Statistical charts 
- Manages:
  - `favorites`
- Develops HTML/Bootstrap/Javascript UI for maps, charts and overall design approach
- Designs the SQLite schema and implements `db_manager.py`

## Phong Dinh Tasks

- Implements `api_client.py` for:
  - TheSportsDB (team details and stadiums)
- Creates and manages:
  - `search_history`
  - `matches`
  - `stadiums`
- Manages:
  - `teams`
- Develops HTML/Bootstrap/Javascript UI for matches and stadium
- Builds Flask routes in `app.py`

---

# 4. Initial API & Backend Layer Plan

## External APIs

### 1. OpenLigaDB
Used for:
- Current matchday schedules
- Past results
- League standings and tables

### 2. TheSportsDB (v1)
Used for:
- Team badges
- Stadium names
- Team details and media assets

### 3. Overpass API
Used for:
- Stadium geographic coordinates
- Latitude and longitude for map visualization

---

# Technologies Used

- **Python 3**
- **Flask or Django**
- **SQLite**
- **Bootstrap 5**
- **Folium**
- **Requests**
- **HTML / CSS / JavaScript**

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