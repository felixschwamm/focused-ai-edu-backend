from fastapi import APIRouter, Depends, HTTPException
import models
import uuid
from dependencies import *
import schemas
from storage import list_files, delete_file
from loguru import logger

router = APIRouter(
    prefix="/courses/{course_id}/lectures",
    tags=["lectures"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    dependencies=[Depends(check_if_course_exists)],
    tags=["lectures"],
    summary="Lists all lectures in a course",
    description="Lists all lectures in a course. Only members of the course and admins can access this endpoint.",
    response_model=schemas.GetLecturesResponse
)
def get_course_lectures(course_id: str, session=Depends(get_session), is_member=Depends(is_member_of_course), user=Depends(decode_token)):
    if not is_member and user["role"] is not models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    query = session.query(models.Lecture, models.LectureUserProgress.completed).outerjoin(models.LectureUserProgress, (models.Lecture.id == models.LectureUserProgress.lecture_id) &(models.LectureUserProgress.user_id == user['id'])).filter(models.Lecture.course_id == course_id).order_by(models.Lecture.name)
    res = query.all()
    return {
        "data": [{
            "id": lecture.id,
            "name": lecture.name,
            "completed": completed if completed is not None else False
        } for lecture, completed in res]
    }


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(check_if_course_exists)],
    tags=["lectures"],
    summary="Create a lecture",
    description="Create a lecture. Only instructors and admins can access this endpoint.",
)
def post_course_lecture(course_id: str, lecture: schemas.PostLectureRequest, session=Depends(get_session), user=Depends(decode_token), is_instructor=Depends(is_course_instructor)):
    if not is_instructor and user["role"] is not models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    session.add(models.Lecture(
        name=lecture.name,
        id=str(uuid.uuid4()),
        course_id=course_id,
    ))
    session.commit()
    logger.info(f"Created lecture {lecture.name} in course {course_id}")
    
    
@router.get(
    "/{lecture_id}",
    response_model=schemas.GetLectureResponse,
    dependencies=[Depends(check_if_course_exists),
                  Depends(check_if_lecture_exists)],
    tags=["lectures"],
    summary="Get a specific lecture",
    description="Get a specific lecture. Only members of the course and admins can access this endpoint.",
)
def get_course_lecture(course_id: str, lecture_id: str, session=Depends(get_session), is_member=Depends(is_member_of_course), user=Depends(decode_token)):
    if not is_member and user["role"] is not models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    res = session.query(models.Lecture, models.LectureUserProgress.completed).outerjoin(models.LectureUserProgress, models.LectureUserProgress.lecture_id == models.Lecture.id).filter(models.Lecture.id == lecture_id).all()
    return {
        "data": {
            "id": res[0][0].id,
            "name": res[0][0].name,
            "completed": res[0][1] if res[0][1] is not None else False
        }
    }


@router.delete(
    "/{lecture_id}",
    status_code=204,
    dependencies=[Depends(check_if_course_exists),
                  Depends(check_if_lecture_exists)],
    tags=["lectures"],
    summary="Delete a lecture",
    description="Delete a lecture. Only instructors and admins can access this endpoint.",
)
def delete_course_lecture(course_id: str, lecture_id: str, session=Depends(get_session), user=Depends(decode_token), is_instructor=Depends(is_course_instructor)):
    if not is_instructor and user["role"] is not models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        session.query(models.Lecture).filter(
            models.Lecture.id == lecture_id).delete()
        files_in_lec = list_files(f'{course_id}/{lecture_id}/')
        for file in files_in_lec:
            delete_file(file)
        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    logger.info(f"Deleted lecture {lecture_id} in course {course_id}")


@router.put(
    '/{lecture_id}/status',
    status_code=204,
    dependencies=[Depends(check_if_course_exists),
                  Depends(check_if_lecture_exists)],
    tags=["lectures"],
    summary="Update lecture status",
    description="Update lecture status for the currently authenticated user."
)
def update_lecture_status(course_id: str, lecture_id: str, status: schemas.UpdateLectureStatusRequest, user=Depends(decode_token), session=Depends(get_session), is_member=Depends(is_member_of_course)):
    if not is_member and user["role"] is not models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    res = session.query(models.LectureUserProgress).filter(
        models.LectureUserProgress.user_id == user["id"], models.LectureUserProgress.lecture_id == lecture_id).all()
    if res == []:
        session.add(models.LectureUserProgress(
            user_id=user["id"],
            lecture_id=lecture_id,
            completed=status.completed
        ))
    else:
        session.query(models.LectureUserProgress).filter(
            models.LectureUserProgress.user_id == user["id"], models.LectureUserProgress.lecture_id == lecture_id).update({"completed": status.completed})
    session.commit()
    logger.info(f"Updated lecture status for user {user['id']} in lecture {lecture_id} to {status.completed}")
    
@router.get(
    "/{lecture_id}/status",
    response_model=schemas.GetLectureStatusResponse,
    dependencies=[Depends(check_if_course_exists),
                  Depends(check_if_lecture_exists)],
    tags=["lectures"],
    summary="Get lecture status",
    description="Get lecture status for the currently authenticated user."
)
def get_lecture_status(course_id: str, lecture_id: str, user=Depends(decode_token), session=Depends(get_session), is_member=Depends(is_member_of_course)):
    if not is_member and user["role"] is not models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        return {
            "completed": session.query(models.LectureUserProgress).filter(
                models.LectureUserProgress.user_id == user["id"], models.LectureUserProgress.lecture_id == lecture_id).one().completed
        }
    except NoResultFound:
        return {
            "completed": False
        }
