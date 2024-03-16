from typing import Annotated, Optional
from sqlalchemy.orm import Session

from fastapi import Depends, FastAPI, HTTPException, Query, Form
from fastapi.security import OAuth2PasswordRequestForm

import uuid
from uuid import UUID

from .service.thoughtspace_service import ThoughtSpaceService
from .models._message import MessagesResponse, NewMessageRequest, RevisionRequest

from .data._db_config import get_db
from .models._user_auth import RegisterUser, UserOutput, LoginResonse, GPTToken
from .service._user_auth import (
    service_signup_users,
    service_login_for_access_token,
    create_access_token,
    gpt_tokens_service,
)

from .utils._helpers import get_current_user_dep

app = FastAPI(
    title="Choir",
    description="Choir Chat",
    version="2.0.0",
    contact={
        "name": "Yusef Mosiah Nathanson",
        "email": "yusef@choir.chat",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    servers=[
        {"url": "https://caxgpt-lilac.vercel.app", "description": "Production server"},
    ],
    docs_url="/api/docs",
)


# user_auth.py web layer routes
@app.post("/api/oauth/login", response_model=LoginResonse, tags=["OAuth2 Authentication"])
async def login_authorization(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    Authorization URL for OAuth2

    Args:
        form_data (Annotated[OAuth2PasswordRequestForm, Depends()]): Form Data
        db (Session, optional): Dependency Injection

    Returns:
        LoginResonse: Login Response
    """
    print("FFFform_data", form_data)
    return await service_login_for_access_token(form_data, db)


@app.post("/api/oauth/token", response_model=GPTToken, tags=["OAuth2 Authentication"])
async def tokens_manager_oauth_codeflow(
    grant_type: str = Form(...),
    refresh_token: Optional[str] = Form(None),
    code: Optional[str] = Form(None),
):
    """
    Token URl For OAuth Code Grant Flow

    Args:
        grant_type (str): Grant Type
        code (Optional[str], optional)
        refresh_token (Optional[str], optional)

    Returns:
        access_token (str)
        token_type (str)
        expires_in (int)
        refresh_token (str)
    """
    return await gpt_tokens_service(grant_type, refresh_token, code)


# Get temp Code against user_id to implentent OAuth2 for Custom Gpt
@app.get("/api/oauth/temp-code", tags=["OAuth2 Authentication"])
async def get_temp_code(user_id: UUID):
    """
    Get Temp Code against user_id to implentent OAuth2 for Custom Gpt

    Args:
        user_id (UUID): User ID

    Returns:
        code (str): Temp Code
    """
    code = create_access_token(data={"id": user_id})
    return {"code": code}


@app.post("/api/oauth/signup", response_model=UserOutput, tags=["OAuth2 Authentication"])
async def signup_users(user_data: RegisterUser, db: Session = Depends(get_db)):
    """
    Signup Users

    Args:
        user_data (RegisterUser): User Data
        db (Session, optional):  Dependency Injection

    Returns:
        UserOutput: User Output
    """
    return await service_signup_users(user_data, db)


@app.post("/api/new_message")
async def new_message_endpoint(
    request: NewMessageRequest,
    db: Session = Depends(get_db),  # Inject the DB session here
    user_id: UUID = Depends(get_current_user_dep),
):
    """
    Send a new message for authenticated users.
    """
    try:
        service = ThoughtSpaceService(db=db)  # Initialize the service with the db session
        response = await service.new_message(request.input_text, str(user_id))
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard", tags=["Dashboard"])
async def dashboard(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_dep),
):
    """
    Dashboard endpoint to get the user's voice balance and messages.

    Args:
        db (Session, optional): Dependency Injection
        user_id (UUID, optional): Dependency Injection

    Returns:
        dict: User's voice balance and messages
    """
    try:
        service = ThoughtSpaceService(db=db)
        dashboard_data = await service.get_dashboard_data(str(user_id))
        if dashboard_data is None:
            raise HTTPException(status_code=404, detail="User not found or no messages available.")
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resonance_search")
async def resonance_search_endpoint(
    request: NewMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Endpoint for similarity search accessible to all users, including unauthenticated ones.
    """
    try:
        anonymous_user_id = "anonymous"  # Handle as needed for anonymous searches
        service = ThoughtSpaceService(db=db)
        response = await service.search(request.input_text)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/revise_message_proposal", tags=["Message Revision"])
# async def revise_message_proposal(
#     revision_request: RevisionRequest,  # Assuming RevisionRequest is a Pydantic model you've defined
#     db: Session = Depends(get_db),
#     user_id: UUID = Depends(get_current_user_dep),
# ):
#     """
#     Endpoint for users to propose revisions to messages.

#     Args:
#         revision_request (RevisionRequest): The revision proposal details.
#         db (Session, optional): Dependency Injection.
#         user_id (UUID, optional): Dependency Injection, identifies the user proposing the revision.

#     Returns:
#         dict: A response indicating the success or failure of the revision proposal.
#     """
#     try:
#         service = ThoughtSpaceService(db=db)  # Assuming ThoughtSpaceService has a method for handling revisions
#         response = await service.propose_revision(revision_request, str(user_id))
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
