from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.core.security import get_current_user
from app.models.user import User
from app.core.supabase import admin_supabase
from app.core.config import settings


router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"],
)


ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.post("/proof")
async def upload_proof(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WEBP images are allowed.",
        )

    contents = await file.read()

    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image size must be less than 5 MB.",
        )

    extension = file.filename.split(".")[-1].lower()

    filename = (
        f"{current_user.id}/"
        f"{uuid4()}.{extension}"
    )

    try:
        storage = admin_supabase.storage.from_("transaction-proofs")

        storage.upload(
            filename,
            contents,
            {
                "content-type": file.content_type,
                "upsert": "false",
            },
        )

        public_url = storage.get_public_url(filename)

        return {
            "message": "Proof uploaded successfully.",
            "proof_url": public_url,
            "file_name": file.filename,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to upload proof: {str(error)}",
        )