import os
import json
import re
from typing import Optional
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
# Initialize FastAPI app
app = FastAPI()

# Mount static files directory (make sure you have a "static" folder in your project)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates (assuming your templates are in the "templates" folder)
templates = Jinja2Templates(directory="templates")

# Initialize Firestore client (ensure you have proper credentials set up)
from google.cloud import firestore
db = firestore.Client(project="formula-racing-453707")

def get_user_token(request: Request) -> Optional[str]:
    """Retrieve the 'token' cookie, if it exists."""
    return request.cookies.get("token")
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msg = "Invalid input. Please enter correct values for each field."
    path = request.url.path

    # Determine which template to re-render based on the URL.
    if path == "/add_driver":
        return templates.TemplateResponse("add_driver.html", {
            "request": request,
            "error": error_msg,
            "driver": None
        }, status_code=HTTP_422_UNPROCESSABLE_ENTITY)
    elif path == "/add_team":
        return templates.TemplateResponse("add_team.html", {
            "request": request,
            "error": error_msg,
            "team": None
        }, status_code=HTTP_422_UNPROCESSABLE_ENTITY)
    elif path == "/query_driver":
        return templates.TemplateResponse("query_driver.html", {
            "request": request,
            "error": error_msg,
            "drivers": None
        }, status_code=HTTP_422_UNPROCESSABLE_ENTITY)
    elif path == "/query_team":
        return templates.TemplateResponse("query_team.html", {
            "request": request,
            "error": error_msg,
            "teams": None
        }, status_code=HTTP_422_UNPROCESSABLE_ENTITY)
    # Add other endpoints as needed.
    else:
        # Fallback: render a generic error template.
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": error_msg
        }, status_code=HTTP_422_UNPROCESSABLE_ENTITY)

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    try:
        token = get_user_token(request)
        if not token:
            # No token: render the login page.
            return templates.TemplateResponse("login.html", {
                "request": request,
                "show_login_box": True
            })
        # Token exists: seed Firestore data if necessary.
        # --- Seed Drivers ---
        drivers_ref = db.collection('drivers').limit(1).stream()
        drivers_exist = any(True for _ in drivers_ref)
        # if not drivers_exist:
        #     sample_drivers = [
        #         {
        #             'name': 'Lewis Hamilton',
        #             'age': 38,
        #             'pole_positions': 103,
        #             'race_wins': 103,
        #             'total_points': 4400,
        #             'world_titles': 7,
        #             'fastest_laps': 61,
        #             'team': 'Mercedes'
        #         },
        #         {
        #             'name': 'Max Verstappen',
        #             'age': 25,
        #             'pole_positions': 26,
        #             'race_wins': 36,
        #             'total_points': 2099,
        #             'world_titles': 2,
        #             'fastest_laps': 23,
        #             'team': 'Red Bull Racing'
        #         },
        #         {
        #             'name': 'Sebastian Vettel',
        #             'age': 35,
        #             'pole_positions': 57,
        #             'race_wins': 53,
        #             'total_points': 3088,
        #             'world_titles': 4,
        #             'fastest_laps': 38,
        #             'team': 'Retired (last with Aston Martin)'
        #         },
        #     ]
        #     for d in sample_drivers:
        #         db.collection('drivers').add(d)
        # --- Seed Teams ---
        teams_ref = db.collection('teams').limit(1).stream()
        teams_exist = any(True for _ in teams_ref)
        # if not teams_exist:
        #     sample_teams = [
        #         {
        #             'team_name': 'Mercedes',
        #             'year_founded': 1954,
        #             'pole_positions': 135,
        #             'race_wins': 125,
        #             'constructor_titles': 8,
        #             'finishing_position': 3
        #         },
        #         {
        #             'team_name': 'Red Bull Racing',
        #             'year_founded': 2005,
        #             'pole_positions': 93,
        #             'race_wins': 92,
        #             'constructor_titles': 5,
        #             'finishing_position': 1
        #         },
        #         {
        #             'team_name': 'Ferrari',
        #             'year_founded': 1950,
        #             'pole_positions': 242,
        #             'race_wins': 242,
        #             'constructor_titles': 16,
        #             'finishing_position': 2
        #         },
        #     ]
        #     for t in sample_teams:
        #         db.collection('teams').add(t)
        # --- Retrieve Data ---
        drivers_list = []
        for doc in db.collection('drivers').stream():
            data = doc.to_dict()
            data['id'] = doc.id
            drivers_list.append(data)
        teams_list = []
        for doc in db.collection('teams').stream():
            data = doc.to_dict()
            data['id'] = doc.id
            teams_list.append(data)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "logged_in": True,
            "drivers": drivers_list,
            "teams": teams_list
        })
    except Exception as e:
        # Consider using logging in production instead of print.
        print("Error in root route:", e)
        raise e

# @app.get("/signout")
# def signout():
#     response = RedirectResponse(url="/")
#     response.set_cookie(key="token", value="", expires=0, path="/")
#     return response

# ----- ADD DRIVER -----
@app.get("/add_driver", response_class=HTMLResponse)
def add_driver_get(request: Request):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    return templates.TemplateResponse("add_driver.html", {
        "request": request,
        "error": None,
        "driver": None
    })

@app.post("/add_driver", response_class=HTMLResponse)
def add_driver_post(
    request: Request,
    driver_name: str = Form(...),
    age: int = Form(...),
    pole_positions: int = Form(...),
    race_wins: int = Form(...),
    total_points: int = Form(...),
    world_titles: int = Form(...),
    fastest_laps: int = Form(...),
    team_name: str = Form(...)
):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    
    # Normalize and validate the driver name
    name = driver_name.strip()
    if not name:
        return templates.TemplateResponse("add_driver.html", {
            "request": request,
            "error": "Driver name cannot be empty.",
            "driver": None
        })
    # Enforce that the name contains at least one letter
    if not re.search("[a-zA-Z]", name):
        return templates.TemplateResponse("add_driver.html", {
            "request": request,
            "error": "Driver name must contain at least one alphabetic character.",
            "driver": None
        })
    normalized_name = name.lower()
    
    # Check for duplicates using the normalized name
    duplicate_query = list(db.collection('drivers').where('name_lower', '==', normalized_name).stream())
    if duplicate_query:
        return templates.TemplateResponse("add_driver.html", {
            "request": request,
            "error": "Driver with this name already exists.",
            "driver": None
        })
    
    driver_data = {
        "name": name,
        "name_lower": normalized_name,
        "age": age,
        "pole_positions": pole_positions,
        "race_wins": race_wins,
        "total_points": total_points,
        "world_titles": world_titles,
        "fastest_laps": fastest_laps,
        "team": team_name.strip()
    }
    db.collection("drivers").add(driver_data)
    return RedirectResponse(url="/", status_code=302)

# ----- ADD TEAM -----
@app.get("/add_team", response_class=HTMLResponse)
def add_team_get(request: Request):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    return templates.TemplateResponse("add_team.html", {
        "request": request,
        "error": None,
        "team": None
    })

@app.post("/add_team", response_class=HTMLResponse)
def add_team_post(
    request: Request,
    team_name: str = Form(...),
    year_founded: int = Form(...),
    pole_positions: int = Form(...),
    race_wins: int = Form(...),
    constructor_titles: int = Form(...),
    finishing_position: int = Form(...)
):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    
    # Normalize and validate the team name.
    name = team_name.strip()
    if not name:
        return templates.TemplateResponse("add_team.html", {
            "request": request,
            "error": "Team name cannot be empty.",
            "team": None
        })
    if not re.search("[a-zA-Z]", name):
        return templates.TemplateResponse("add_team.html", {
            "request": request,
            "error": "Team name must contain at least one alphabetic character.",
            "team": None
        })
    normalized_name = name.lower()
    
    # First, try to find duplicates using the normalized field.
    duplicate_query = list(db.collection('teams')
                           .where('team_name_lower', '==', normalized_name)
                           .stream())
    
    duplicate_found = bool(duplicate_query)
    
    # Fallback: if no duplicate was found using the normalized field,
    # check all teams manually for those that might be missing "team_name_lower".
    if not duplicate_found:
        for doc in db.collection('teams').stream():
            data = doc.to_dict()
            # If the document doesn't have the normalized field, compare manually.
            if "team_name_lower" not in data:
                existing_name = data.get("team_name", "").strip().lower()
                if existing_name == normalized_name:
                    duplicate_found = True
                    break

    if duplicate_found:
        return templates.TemplateResponse("add_team.html", {
            "request": request,
            "error": "Team with this name already exists.",
            "team": None
        })
    
    team_data = {
        "team_name": name,
        "team_name_lower": normalized_name,  # Save normalized name for duplicate checks
        "year_founded": year_founded,
        "pole_positions": pole_positions,
        "race_wins": race_wins,
        "constructor_titles": constructor_titles,
        "finishing_position": finishing_position
    }
    db.collection("teams").add(team_data)
    return RedirectResponse(url="/", status_code=302)

# ----- QUERY DRIVERS -----
@app.get("/query_driver", response_class=HTMLResponse)
def query_driver_get(request: Request):
    return templates.TemplateResponse("query_driver.html", {
        "request": request,
        "drivers": None,
        "error": None
    })

@app.post("/query_driver", response_class=HTMLResponse)
def query_driver_post(
    request: Request,
    attribute: str = Form(...),
    operation: str = Form(...),
    value_str: str = Form(...)
):
    try:
        value = int(value_str)
    except ValueError:
        return templates.TemplateResponse("query_driver.html", {
            "request": request,
            "drivers": None,
            "error": "The value must be a valid number."
        })
    coll_ref = db.collection('drivers')
    if operation == "=":
        query_ref = coll_ref.where(attribute, '==', value)
    elif operation == "<":
        query_ref = coll_ref.where(attribute, '<', value)
    elif operation == ">":
        query_ref = coll_ref.where(attribute, '>', value)
    else:
        query_ref = coll_ref
    driver_results = []
    for doc in query_ref.stream():
        d = doc.to_dict()
        d['id'] = doc.id
        driver_results.append(d)
    return templates.TemplateResponse("query_driver.html", {
        "request": request,
        "drivers": driver_results,
        "error": None
    })

# ----- QUERY TEAMS -----
@app.get("/query_team", response_class=HTMLResponse)
def query_team_get(request: Request):
    return templates.TemplateResponse("query_team.html", {
        "request": request,
        "teams": None,
        "error": None
    })

@app.post("/query_team", response_class=HTMLResponse)
def query_team_post(
    request: Request,
    attribute: str = Form(...),
    operation: str = Form(...),
    value_str: str = Form(...)
):
    try:
        value = int(value_str)
    except ValueError:
        return templates.TemplateResponse("query_team.html", {
            "request": request,
            "teams": None,
            "error": "The value must be a valid number."
        })
    coll_ref = db.collection('teams')
    if operation == "=":
        query_ref = coll_ref.where(attribute, '==', value)
    elif operation == "<":
        query_ref = coll_ref.where(attribute, '<', value)
    elif operation == ">":
        query_ref = coll_ref.where(attribute, '>', value)
    else:
        query_ref = coll_ref
    team_results = []
    for doc in query_ref.stream():
        t = doc.to_dict()
        t['id'] = doc.id
        team_results.append(t)
    return templates.TemplateResponse("query_team.html", {
        "request": request,
        "teams": team_results,
        "error": None
    })

# ----- DRIVER DETAILS -----
@app.get("/driver_details/{driver_id}", response_class=HTMLResponse)
def driver_details(request: Request, driver_id: str):
    doc = db.collection('drivers').document(driver_id).get()
    driver_data = None
    if doc.exists:
        driver_data = doc.to_dict()
        driver_data['id'] = driver_id
    return templates.TemplateResponse("driver_details.html", {
        "request": request,
        "driver": driver_data,
        "logged_in": True  # Consider making this consistent across templates if needed.
    })

# ----- TEAM DETAILS -----
@app.get("/team_details/{team_id}", response_class=HTMLResponse)
def team_details(request: Request, team_id: str):
    doc = db.collection('teams').document(team_id).get()
    team_data = None
    if doc.exists:
        team_data = doc.to_dict()
        team_data['id'] = team_id
    return templates.TemplateResponse("team_details.html", {
        "request": request,
        "team": team_data,
        "logged_in": True
    })

# ----- EDIT DRIVER -----
@app.get("/edit_driver/{driver_id}", response_class=HTMLResponse)
def edit_driver_get(request: Request, driver_id: str):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    doc = db.collection('drivers').document(driver_id).get()
    driver_data = None
    if doc.exists:
        driver_data = doc.to_dict()
        driver_data['id'] = driver_id
    return templates.TemplateResponse("add_driver.html", {
        "request": request,
        "driver": driver_data,
        "error": None
    })

@app.post("/edit_driver/{driver_id}", response_class=HTMLResponse)
def edit_driver_post(
    request: Request,
    driver_id: str,
    driver_name: str = Form(...),
    age: int = Form(...),
    pole_positions: int = Form(...),
    race_wins: int = Form(...),
    total_points: int = Form(...),
    world_titles: int = Form(...),
    fastest_laps: int = Form(...),
    team_name: str = Form(...)
):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    
    new_name = driver_name.strip()
    if not new_name:
        return templates.TemplateResponse("add_driver.html", {
            "request": request,
            "error": "Driver name cannot be empty.",
            "driver": None
        })
    new_name_lower = new_name.lower()
    
    # Check if there is any other driver (different document id) with the same normalized name.
    duplicates = list(db.collection('drivers').where('name_lower', '==', new_name_lower).stream())
    for doc in duplicates:
        if doc.id != driver_id:
            return templates.TemplateResponse("add_driver.html", {
                "request": request,
                "error": "Another driver with this name already exists.",
                "driver": None
            })
    
    doc_ref = db.collection('drivers').document(driver_id)
    doc_ref.update({
        'name': new_name,
        'name_lower': new_name_lower,
        'age': age,
        'pole_positions': pole_positions,
        'race_wins': race_wins,
        'total_points': total_points,
        'world_titles': world_titles,
        'fastest_laps': fastest_laps,
        'team': team_name.strip()
    })
    return RedirectResponse(url=f"/driver_details/{driver_id}", status_code=302)

# ----- EDIT TEAM -----
@app.get("/edit_team/{team_id}", response_class=HTMLResponse)
def edit_team_get(request: Request, team_id: str):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    doc = db.collection('teams').document(team_id).get()
    team_data = None
    if doc.exists:
        team_data = doc.to_dict()
        team_data['id'] = team_id
    return templates.TemplateResponse("add_team.html", {
        "request": request,
        "team": team_data,
        "error": None
    })

@app.post("/edit_team/{team_id}", response_class=HTMLResponse)
def edit_team_post(
    request: Request,
    team_id: str,
    team_name: str = Form(...),
    year_founded: int = Form(...),
    pole_positions: int = Form(...),
    race_wins: int = Form(...),
    constructor_titles: int = Form(...),
    finishing_position: int = Form(...)
):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    doc_ref = db.collection('teams').document(team_id)
    doc_ref.update({
        'team_name': team_name.strip(),
        'year_founded': year_founded,
        'pole_positions': pole_positions,
        'race_wins': race_wins,
        'constructor_titles': constructor_titles,
        'finishing_position': finishing_position
    })
    return RedirectResponse(url=f"/team_details/{team_id}", status_code=302)

# ----- DELETE DRIVER -----
@app.get("/delete_driver/{driver_id}")
def delete_driver(request: Request, driver_id: str):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    db.collection('drivers').document(driver_id).delete()
    return RedirectResponse(url="/")

# ----- DELETE TEAM -----
@app.get("/delete_team/{team_id}")
def delete_team(request: Request, team_id: str):
    if not get_user_token(request):
        return RedirectResponse(url="/")
    db.collection('teams').document(team_id).delete()
    return RedirectResponse(url="/")

# ----- COMPARE DRIVERS -----
@app.get("/compare_drivers", response_class=HTMLResponse)
def compare_drivers_get(request: Request):
    return templates.TemplateResponse("compare_drivers.html", {
        "request": request,
        "driver1": None,
        "driver2": None,
        "error": None
    })

@app.post("/compare_drivers", response_class=HTMLResponse)
def compare_drivers_post(
    request: Request,
    driver1: str = Form(...),
    driver2: str = Form(...)
):
    d1_name = driver1.strip()
    d2_name = driver2.strip()
    if not d1_name or not d2_name:
        return templates.TemplateResponse("compare_drivers.html", {
            "request": request,
            "driver1": None,
            "driver2": None,
            "error": "Please enter names for both drivers."
        })
    d1_query = list(db.collection('drivers').where('name', '==', d1_name).stream())
    d2_query = list(db.collection('drivers').where('name', '==', d2_name).stream())
    driverA = d1_query[0].to_dict() if d1_query else None
    driverB = d2_query[0].to_dict() if d2_query else None
    if not driverA or not driverB:
        return templates.TemplateResponse("compare_drivers.html", {
            "request": request,
            "driver1": driverA,
            "driver2": driverB,
            "error": "One or both drivers were not found. Check spelling and try again."
        })
    return templates.TemplateResponse("compare_drivers.html", {
        "request": request,
        "driver1": driverA,
        "driver2": driverB,
        "error": None
    })

# ----- COMPARE TEAMS -----
@app.get("/compare_teams", response_class=HTMLResponse)
def compare_teams_get(request: Request):
    return templates.TemplateResponse("compare_teams.html", {
        "request": request,
        "team1": None,
        "team2": None,
        "error": None
    })

@app.post("/compare_teams", response_class=HTMLResponse)
def compare_teams_post(
    request: Request,
    team1: str = Form(...),
    team2: str = Form(...)
):
    t1_name = team1.strip()
    t2_name = team2.strip()
    if not t1_name or not t2_name:
        return templates.TemplateResponse("compare_teams.html", {
            "request": request,
            "team1": None,
            "team2": None,
            "error": "Please enter names for both teams."
        })
    t1_query = list(db.collection('teams').where('team_name', '==', t1_name).stream())
    t2_query = list(db.collection('teams').where('team_name', '==', t2_name).stream())
    teamA = t1_query[0].to_dict() if t1_query else None
    teamB = t2_query[0].to_dict() if t2_query else None
    if not teamA or not teamB:
        return templates.TemplateResponse("compare_teams.html", {
            "request": request,
            "team1": teamA,
            "team2": teamB,
            "error": "One or both teams were not found. Check spelling and try again."
        })
    return templates.TemplateResponse("compare_teams.html", {
        "request": request,
        "team1": teamA,
        "team2": teamB,
        "error": None
    })

# ----- Run the FastAPI Server -----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
