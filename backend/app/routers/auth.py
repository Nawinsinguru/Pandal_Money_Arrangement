from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.supabase import supabase
from app.core.database import get_db
from app.models.user import User
from app.models.member import PandalMember
from app.models.invitation import PandalInvitation
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

security = HTTPBearer()


@router.post("/register", response_model=AuthResponse)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        email = str(data.email).lower().strip()

        # 1. Create user in Supabase Authentication
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": data.password,
                "options": {
                    "data": {
                        "full_name": data.full_name
                    }
                },
            }
        )

        user = response.user
        session = response.session

        if user is None:
            raise HTTPException(
                status_code=400,
                detail="Registration failed.",
            )

        # 2. Create application user if not already present
        app_user = (
            db.query(User)
            .filter(User.id == user.id)
            .first()
        )

        if app_user is None:
            app_user = User(
                id=user.id,
                email=email,
                full_name=data.full_name,
            )

            db.add(app_user)
            db.flush()

        # 3. Find pending invitations for this email
        invitations = (
            db.query(PandalInvitation)
            .filter(
                PandalInvitation.email == email,
                PandalInvitation.status == "pending",
            )
            .all()
        )

        # 4. Add the user to each invited Pandal
        for invitation in invitations:

            existing_membership = (
                db.query(PandalMember)
                .filter(
                    PandalMember.pandal_id == invitation.pandal_id,
                    PandalMember.user_id == user.id,
                )
                .first()
            )

            if existing_membership is None:

                membership = PandalMember(
                    pandal_id=invitation.pandal_id,
                    user_id=user.id,
                    role=invitation.role,
                )

                db.add(membership)

            invitation.status = "accepted"

        db.commit()

        return AuthResponse(
            message="Registration successful.",
            access_token=session.access_token if session else None,
            refresh_token=session.refresh_token if session else None,
            user_id=str(user.id),
            email=user.email,
        )

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        error_message = str(error)

        if "already registered" in error_message.lower():
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )

        raise HTTPException(
            status_code=400,
            detail=error_message,
        )


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest):
    try:
        email = str(data.email).lower().strip()

        response = supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": data.password,
            }
        )

        user = response.user
        session = response.session

        if user is None or session is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            )

        return AuthResponse(
            message="Login successful.",
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user_id=str(user.id),
            email=user.email,
        )

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )


@router.get("/me")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        access_token = credentials.credentials

        # Validate token with Supabase
        response = supabase.auth.get_user(access_token)

        supabase_user = response.user

        if supabase_user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token.",
            )

        # Find application user
        app_user = (
            db.query(User)
            .filter(User.id == supabase_user.id)
            .first()
        )

        # Create application user if necessary
        if app_user is None:

            full_name = (
                supabase_user.user_metadata.get("full_name")
                if supabase_user.user_metadata
                else None
            )

            app_user = User(
                id=supabase_user.id,
                email=supabase_user.email,
                full_name=full_name or "User",
            )

            db.add(app_user)
            db.commit()
            db.refresh(app_user)

        return {
            "id": str(app_user.id),
            "email": app_user.email,
            "full_name": app_user.full_name,
            "message": "Authenticated user",
        }

    except HTTPException:
        raise

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )