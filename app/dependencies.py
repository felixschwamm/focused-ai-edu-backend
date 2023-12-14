from fastapi import Depends, HTTPException, Header
from db import Session
from sqlalchemy.exc import NoResultFound
import models
from storage import list_files
import jwt
from loguru import logger


def get_session():
    logger.trace("Creating session")
    session = Session()
    try:
        yield session
    finally:
        logger.trace("Closing session")
        session.close()


def decode_token(authorization: str = Header(description='A bearer token'), session=Depends(get_session)):
    logger.trace("Decoding token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        user = session.query(models.User).filter(
            models.User.id == payload["sub"]).all()
        if user == []:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "role": user[0].role,
            "id": user[0].id,
            "name": user[0].name
        }
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


def is_course_instructor(course_id: str, user=Depends(decode_token), session=Depends(get_session)) -> bool:
    try:
        session.query(models.CourseMembership).filter(
            models.CourseMembership.user_id == user["id"]).filter(models.CourseMembership.course_id == course_id).filter(models.CourseMembership.is_instructor.is_(True)).one()
        return True
    except NoResultFound:
        return False
    

def is_member_of_course(course_id: str, user=Depends(decode_token), session=Depends(get_session)) -> bool:
    try:
        session.query(models.CourseMembership).filter(
            models.CourseMembership.user_id == user["id"]).filter(models.CourseMembership.course_id == course_id).one()
        return True
    except NoResultFound:
        return False


def check_if_course_exists(course_id: str, session=Depends(get_session)):
    try:
        session.query(models.Course).filter(
            models.Course.id == course_id).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Course not found")


def check_if_lecture_exists(lecture_id: str, session=Depends(get_session)):
    try:
        session.query(models.Lecture).filter(
            models.Lecture.id == lecture_id).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Lecture not found")


def check_if_file_exists(filename: str):
    if list_files(filename) == []:
        raise HTTPException(status_code=404, detail="File not found")
