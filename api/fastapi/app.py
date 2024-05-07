from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from id_extract import process_id_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
class IDExtractResponse(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    address_line_1: str
    address_line_2: str
    city: str
    state: str
    misc: dict
"""

@app.post("/id-extract/", response_model=dict)
async def upload_image(file: UploadFile = File(...)) -> str:
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    file_content = await file.read()
    return process_id_document(file_content)
