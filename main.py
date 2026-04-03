import base64
import os
import secrets
import shutil
import httpx

from typing import Annotated, Optional, List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from starlette import status
from starlette.responses import FileResponse

##############################
#Helper Functions
##############################

# Helper function to get image url from each api response
def get_image_url_from_response(pet: str, data: dict) -> str:
    if pet == "dog":
        return data["message"]
    elif pet == "cat":
        return data[0]["url"]
    elif pet == "duck":
        return data["url"]

def generate_profile(input_data: dict) -> dict:
    career = input_data.get("career", "").lower()
    name = input_data.get("name", "")
    pets = input_data.get("pets", [])

    suitability = f"{name}, your passion for '{career}' suggests "
    if len(career) > 8:
        suitability += "a detail-oriented mind — highly suited!"
    else:
        suitability += "a bold, concise thinker — moderately suited."

    if "dog" in pets:
        movie_query = "Lassie"
    elif "cat" in pets:
        movie_query = "The Cat Returns"
    elif "duck" in pets:
        movie_query = "Howard the Duck"
    else:
        movie_query = career

    return {"suitability": suitability, "movie_query": movie_query}

###########
# Constants
###########

# Data model for the form
class Profile(BaseModel):
    name: str
    career: str
    pets: Optional[List[str]] = []


store = {
    "input": None, #unput from  submit
    "profile": None, #generated profile
    "images": {}  # a path to image file(s)
}

OMDB_API_KEY = "4fe82850"

PET_APIS = {
    "dog": "https://dog.ceo/api/breeds/image/random",
    "cat": "https://api.thecatapi.com/v1/images/search",
    "duck": "https://random-d.uk/api/v2/random"
}

##########################################################
# Function to download image from lecture changed to async
##########################################################
async def download_image(image_uri: str) -> str:
    save_file = image_uri.split('/')[-1]

    async with httpx.AsyncClient() as client:
        async with client.stream("GET", image_uri, follow_redirects=True) as response:
            response.raise_for_status()
            with open(save_file, 'wb') as fout:
                async for chunk in response.aiter_bytes():
                    fout.write(chunk)

    print('Saved to', save_file)
    return save_file

###########################################################################
# Basic HTTP authentication using my student id 13234612 taken from lecture
###########################################################################
security = HTTPBasic()

def check_creds(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_username = b'13234612'
    correct_password = b'13234612'

    current_username = credentials.username.encode()
    current_password = credentials.password.encode()

    user_correct = secrets.compare_digest(current_username, correct_username)
    pasw_correct = secrets.compare_digest(current_password, correct_password)

    if not (user_correct and pasw_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return current_username


###############################################
# Start FASTAPI depending on http authenticaion 
###############################################
app = FastAPI(dependencies=[Depends(check_creds)])


#################################
# Endpoints to Serve static files
#################################
@app.get("/", response_class=FileResponse)
async def index():
    return 'index.html'

@app.get("/style.css", response_class=FileResponse)
async def style_css():
    return 'style.css'

@app.get("/script.js", response_class=FileResponse)
async def script_js():
    return 'script.js'




#########################
#Assignment endpoints
########################
@app.get("/form", response_class=FileResponse)
async def form():
    return 'psycho.html'

@app.post("/submit")
async def submit(personal_data: Profile):
    store["input"] = personal_data.model_dump() #Convert to dictionary
    return {"message": "Data submitted successfuly"}

@app.get("/view/input")
async def view_input():
    if not store["input"]:
        raise HTTPException(status_code=404, detail="No input data found!")
    return store["input"]    

@app.get("/analyse")
async def analyse():

    if not store["input"]:
        raise HTTPException(status_code=400, detail="submit the form first!")

    input_data = store["input"]
    profile = generate_profile(input_data) #start profile dictionary on input data

# Fetch movie recommendation from OMDB and pet images from respective APIs
# using a shared async client for multiple requests,
# storing movie data in profile and image file paths in store
    async with httpx.AsyncClient() as client:
        movie_res = await client.get(
            "http://www.omdbapi.com/",
            params={"apikey": OMDB_API_KEY, "t": profile["movie_query"]}
        )
        movie_data = movie_res.json()
        profile["movie"] = {
            "title": movie_data.get("Title", "Unknown"),
            "year": movie_data.get("Year", ""),
            "plot": movie_data.get("Plot", ""),
            "poster": movie_data.get("Poster", "")
        }

        store["images"] = {}
        for pet in input_data.get("pets", []):
            api_response = await client.get(PET_APIS[pet])
            api_data = api_response.json()
            image_url = get_image_url_from_response(pet, api_data)
            saved_file_path = await download_image(image_url)
            store["images"][pet] = saved_file_path

    store["profile"] = profile
    return {"message": "Analysis complete"}

## Returns profile data with pet image endpoints appended to the JSON for the front end to use
@app.get("/view/profile")
async def view_profile():
    if not store["profile"]:
        raise HTTPException(status_code=404, detail="No profile found. Run analyse first!")

    response = dict(store["profile"])
    response["pet_images"] = {
        pet: f"/images/{pet}" for pet in store["images"]
    }
    return response

#Additional endpoint to serve the images
@app.get("/images/{pet}", response_class=FileResponse)
async def get_image(pet: str):
    path = store["images"].get(pet)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found!")
    return path









