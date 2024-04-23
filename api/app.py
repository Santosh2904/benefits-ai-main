from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enum import Enum
from datetime import date

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Gender(Enum):
    male = "M"
    female = "F"

class IDExtractResponse(BaseModel):
    first_name: str
    last_name: str
    sex: Gender  # Use the Gender enum directly
    date_of_birth: date
    address_line_1: str
    address_line_2: str
    city: str
    state: str
    misc: dict

dummy_response = IDExtractResponse(
    first_name='John',
    last_name='Doe',
    sex=Gender.male,  # Use enum member
    date_of_birth=date(1985, 5, 23),
    address_line_1='271 Huntington Av',
    address_line_2='Ste 3',
    city='Boston',
    state='Massachusetts',
    misc={}
)

@app.post("/id-extract/", response_model=IDExtractResponse)
async def upload_image(file: UploadFile = File(...)) -> IDExtractResponse:
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    file_content = await file.read()
    print(f'File Content: {file_content}')
    # Process the file_content as needed for your application
    return dummy_response
