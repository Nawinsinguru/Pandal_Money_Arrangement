from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.supabase import supabase
from app.core.database import get_db
from app.models.user import User


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        access_token = credentials.credentials

        # Validate the token with Supabase
        response = supabase.auth.get_user(access_token)

        supabase_user = response.user

        if supabase_user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token.",
            )

        # Find the application user
        app_user = (
            db.query(User)
            .filter(User.id == supabase_user.id)
            .first()
        )

        if app_user is None:
            raise HTTPException(
                status_code=401,
                detail="Application user not found.",
            )

        return app_user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )