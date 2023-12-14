from fastapi import FastAPI, HTTPException, Depends, Request
import models
import schemas
from db import Session
from utils import generate_mock_jwt
from dependencies import get_session, decode_token

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers import courses, lectures, materials
from loguru import logger
import sys

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

import uuid

app = FastAPI()

# set log level to TRACE
logger.remove()
logger.add(sys.stderr, level="TRACE")

# add routers
app.include_router(courses.router)
app.include_router(lectures.router)
app.include_router(materials.router)

# set up rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create the database tables
session = Session()
models.Base.metadata.create_all(bind=session.get_bind())
session.close()

# Initialize the cache
FastAPICache.init(InMemoryBackend())


@app.post(
    "/login",
    response_model=schemas.LoginResponse,
    summary='Mock login',
    responses={
        401: {"description": "Wrong password"},
        404: {"description": "User not found"}
    },
    description="Mock login endpoint. Use 'password' as password for all users. You should use the id and not the name of the user.",
)
def login(request: Request, login_request: schemas.LoginRequest, session=Depends(get_session)):
    if login_request.password != "password":
        raise HTTPException(status_code=401, detail="Wrong password")
    user = session.query(models.User).filter(
        models.User.id == login_request.user_id).all()
    if user == []:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"User {login_request.user_id} logged in")
    return {
        "token": generate_mock_jwt(login_request.user_id)
    }


@app.get(
    "/me",
    response_model=schemas.User,
    summary='Get current user',
)
def get_me(user=Depends(decode_token)):
    return user


@app.get(
    "/users",
    response_model=schemas.GetUserResponse,
    tags=["users"],
    summary='Get all users',
    description='Get all users in the system. Only teachers and admins can access this endpoint.',
    responses={
        403: {"description": "Forbidden"}
    }
)
async def get_users(session=Depends(get_session), user=Depends(decode_token)):
    if user["role"] not in [models.UserRole.admin, models.UserRole.teacher]:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {
        "data": session.query(models.User).all()
    }


@app.post(
    "/users",
    response_model=schemas.User,
    tags=["users"],
    summary='Create a user',
    description='Create a user. Only admins can access this endpoint.',
    responses={
        403: {"description": "Forbidden"}
    }
)
def create_user(user: schemas.PostUserRequest, session=Depends(get_session), current_user=Depends(decode_token)):
    if current_user["role"] is not models.UserRole.admin:
        raise HTTPException(
            status_code=403, detail="Only admins can create users")
    session.add(models.User(
        name=user.name,
        id=str(uuid.uuid4()),
        role=user.role
    ))
    session.commit()
    logger.info(f"Created user {user.name}")


@app.get(
    "/my/courses",
    response_model=schemas.GetCourseResponse,
    summary='Get my courses',
    description='Get all courses that the currently authenticated user is enrolled in.',
    tags=["courses"],
    responses={
        403: {"description": "Forbidden"}
    }
)
def get_my_courses(session=Depends(get_session), user=Depends(decode_token)):
    return {
        "data": session.query(models.Course).join(models.CourseMembership, models.CourseMembership.course_id == models.Course.id).filter(models.CourseMembership.user_id == user["id"]).all()
    }
