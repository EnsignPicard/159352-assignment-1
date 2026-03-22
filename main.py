from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from starlette import status
from typing import Annotated, List
import secrets
from starlette.responses import FileResponse
from fileinput import filename
import httpx

security = HTTPBasic()

def download_image(image_uri: str) -> str:
    save_file = image_uri.split('/')[-1]
    uri = httpx.URL(image_uri)

    with httpx.stream("GET", uri, follow_redirects=True) as response:
        response.raise_for_status()
        with open(save_file, 'wb') as fout:
            for chunk in response.iter_bytes():
                fout.write(chunk)

    print('Saved to', save_file)
    return save_file

# Function to verify authentication of user
def check_creds(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    correct_username = b'13234612'
    correct_password = b'13234612'

    # The input credentials
    current_username = credentials.username.encode()
    current_password = credentials.password.encode()

    # Now compare them with the "correct" values
    user_correct = secrets.compare_digest(current_username, correct_username)
    pasw_correct = secrets.compare_digest(current_password, correct_password)

    # Action to take if authentication fails - here raise an HTTP exception
    # with 401 status. This will result in the client asking again for credentials
    if not (user_correct and pasw_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return current_username

# Data model for the form
class Profile(BaseModel):
    name: str

# Start the application and make it depend upon the successful
# completion of the check crecentials function
app = FastAPI(dependencies=[Depends(check_creds)])

# Serve the HTML form
@app.get("/", response_class=FileResponse)
async def form():
    return 'index.html'

@app.get("/form", response_class=FileResponse)
async def form():
    return 'psycho.html'

@app.get("static/style.css", response_class=FileResponse)
async def form():
    return 'style.css'

# Use a Pydantic data model parse request into a data type. With the Annotated[]
# construct, we tell FastAPI where to find the data in the HTTP request and how
# to handle it
@app.post("/submit")
async def submit(personal_data: Annotated[Profile, Form()]):
    return personal_data

@app.get("/analyze")
async def analyze():
    return

@app.get("/view/input")
async def viewinput():
    return

@app.get("/view/profile")
async def viewprofile():
    return

@app.get("/static/{path}", response_class=FileResponse)
async def static(path: str):
    return f'static/{path}'
'''
@app.post("/data/submit")
async def submit(request: Request):

    # Dump the header to the console
    for header in request.headers.items():
        print(header)

    # Get the request body - await means that the thread can do other things while
    # waiting to extract the body text from the request packet
    blob = await request.body()

    # Dump the request body to the console
    print(blob) # blob is a byte string

    # Each back the body text
    return {"message": "POST data received", "body": blob.decode("utf-8")}
'''

# Server responds with a cookie
# @app.get("/demo4/cookiemonster")
# async def cookiemonster(response: Response):
#   response.set_cookie("yummy_cookie", "chocolate", expires=100)
