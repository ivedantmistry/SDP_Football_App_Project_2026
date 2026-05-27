import requests


def get_team_details(team_name):
    """
    Fetches team details and stadium information from TheSportsDB API.
    """
    url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={team_name}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        # Check if the API returned
        if data.get("teams"):
            team = data["teams"][0]

            extracted_data = {
                "id": team.get("idTeam"),
                "name": team.get("strTeam"),
                "badge_url": team.get("strTeamBadge"),
                "stadium_name": team.get("strStadium"),
                "stadium_location": team.get("strStadiumLocation"),
                "stadium_capacity": team.get("intStadiumCapacity"),
                "description": team.get("strDescriptionEN"),
            }
            return extracted_data
        else:
            return None  # Team not found

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
