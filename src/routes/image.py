import os
import tempfile

from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.services.cv_service import initiate

router = APIRouter(prefix="/image", tags=["image"])

@router.post("/upload_image/")
async def upload_license_plate(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name

        # Pass the image to your ML model to get the license plate text
        license_plate_text = initiate.main(tmp_file_path)

        # Optionally, store the result in the database if needed
        os.remove(tmp_file_path)

        return JSONResponse({"license_plate": license_plate_text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
