import base64
import os
import secrets
import shutil
from typing import Annotated, Optional, List

import httpx
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from starlette import status
from starlette.responses import FileResponse



async def download_image(image_uri: str) -> str:
    save_file = os.path.join(IMAGE_DIR, image_uri.split('/')[-1])

    async with httpx.AsyncClient() as client:
        async with client.stream("GET", image_uri, follow_redirects=True) as response:
            response.raise_for_status()
            with open(save_file, 'wb') as fout:
                async for chunk in response.aiter_bytes():
                    fout.write(chunk)

    print('Saved to', save_file)
    return save_file


# Data model for the form
class Profile(BaseModel):
    name: str
    career: str
    pets: Optional[List[str]] = []


store = {
    "input": None,
    "profile": None,
    "images": {}  # {"dog": "path/to/file.jpg", ...}
}

# Basic HTTP authentication using student id 13234612
############################################################################
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
############################################################################

app = FastAPI(dependencies=[Depends(check_creds)])

# Serve static files
########################################################################
@app.get("/", response_class=FileResponse)
async def index():
    return 'index.html'

@app.get("/style.css", response_class=FileResponse)
async def style_css():
    return 'style.css'

@app.get("/script.js", response_class=FileResponse)
async def script_js():
    return 'script.js'

@app.get("/form", response_class=FileResponse)
async def form():
    return 'psycho.html'
###########################################################################

@app.post("/submit")
async def submit(personal_data: Profile):
    store["input"] = personal_data.model_dump()
    return {"message": "Data successfully submitted"}


OMDB_API_KEY = "4fe82850"

PET_APIS = {
    "dog": "https://dog.ceo/api/breeds/image/random",
    "cat": "https://api.thecatapi.com/v1/images/search",
    "duck": "https://random-d.uk/api/v2/random"
}

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

IMAGE_DIR = "pet_images"
@app.get("/analyse")
async def analyse():
    # Wipe and recreate the image folder
    if os.path.exists(IMAGE_DIR):
        shutil.rmtree(IMAGE_DIR)
    os.makedirs(IMAGE_DIR)

    if not store["input"]:
        raise HTTPException(status_code=400, detail="No input data. Please submit the form first.")

    input_data = store["input"]
    profile = generate_profile(input_data)

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
            meta_res = await client.get(PET_APIS[pet])
            meta = meta_res.json()
            image_url = get_image_url_from_response(pet, meta)
            saved_path = await download_image(image_url)
            store["images"][pet] = saved_path

    store["profile"] = profile
    return {"message": "Analysis complete"}


@app.get("/view/input")
async def view_input():
    if not store["input"]:
        raise HTTPException(status_code=404, detail="No input data found")
    return store["input"]


@app.get("/view/profile")
async def view_profile():
    if not store["profile"]:
        raise HTTPException(status_code=404, detail="No profile found. Run analyse first.")

    response = dict(store["profile"])
    response["pet_images"] = {
        pet: f"/images/{pet}" for pet in store["images"]
    }
    return response


@app.get("/images/{pet}")
async def get_image(pet: str):
    path = store["images"].get(pet)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)