from fastapi import APIRouter, Depends, HTTPException
import models
import schemas
from dependencies import *
import uuid
from typing import Annotated
from storage import list_files, delete_file
from loguru import logger

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/",
    status_code=201,
    tags=["courses"],
    summary='Create a course',
    description='Create a course. Only teachers and admins can access this endpoint.',
    responses={
        403: {"description": "Forbidden"}
    }
)
def create_course(course: schemas.PostCourseRequest, session=Depends(get_session), user=Depends(decode_token)):
    if user["role"] not in [models.UserRole.admin, models.UserRole.teacher]:
        raise HTTPException(status_code=403, detail="Forbidden")
    course_id = str(uuid.uuid4())
    session.add(models.Course(
        name=course.name,
        id=course_id,
    ))
    session.add(models.CourseMembership(
        user_id=user["id"],
        course_id=course_id,
        is_instructor=True,
    ))
    session.commit()
    logger.info(f"Created course {course_id}")
    logger.info(f"Added user {user['id']} to course {course_id}")

@router.post(
    "/{course_id}/users",
    status_code=201,
    dependencies=[Depends(check_if_course_exists)],
    tags=["courses"],
    summary='Add a user to a course',
    description='Add a user to a course. Only admins and course instructors can access this endpoint.',
    responses={
        403: {"description": "Forbidden"},
        404: {"description": "User not found"},
        409: {"description": "User already in course"}
    }
)
def add_user_to_course(course_id: str, is_instructor: Annotated[bool, Depends(is_course_instructor)], new_user: schemas.AddUserToCourseRequest, session=Depends(get_session), user=Depends(decode_token)):
    if not is_instructor and not user["role"] == models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        session.query(models.User).filter(models.User.id == new_user.user_id).one()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="User not found")
    course_membership_query = session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == new_user.user_id, models.CourseMembership.course_id == course_id)
    if course_membership_query.count() > 0:
        raise HTTPException(status_code=409, detail="User already in course")
    new_user_role = session.query(models.User).filter(models.User.id == new_user.user_id).one().role
    if new_user.is_instructor and new_user_role == models.UserRole.student:
        raise HTTPException(status_code=403, detail="Only admins and teachers can add instructors to courses")
    session.add(models.CourseMembership(
        user_id=new_user.user_id,
        course_id=course_id,
        is_instructor=new_user.is_instructor,
    ))
    session.commit()
    logger.info(f"Added user {new_user.user_id} to course {course_id}")


@router.delete(
    "/{course_id}",
    status_code=204,
    dependencies=[Depends(check_if_course_exists)],
    tags=["courses"],
    summary='Delete a course',
    description='Delete a course. Only admins and course instructors can access this endpoint.',
    responses={
        403: {"description": "Forbidden"}
    }
)
def delete_course(course_id: str, is_instructor: Annotated[bool, Depends(is_course_instructor)], session=Depends(get_session), user=Depends(decode_token)):
    if not is_instructor and not user["role"] == models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    session.query(models.Course).filter(models.Course.id == course_id).delete()
    session.query(models.Lecture).filter(
        models.Lecture.course_id == course_id).delete()
    session.commit()
    files_in_course = list_files(f'{course_id}/')
    for file in files_in_course:
        logger.trace(f"Cleaning file {file} for course {course_id}")
        delete_file(file)
    logger.info(f"Deleted course {course_id}")
        

@router.delete(
    "/{course_id}/users/{user_id}",
    status_code=204,
    dependencies=[Depends(check_if_course_exists)],
    tags=["courses"],
    summary='Remove a user from a course',
    description='Remove a user from a course. Only admins and course instructors can access this endpoint.',
    responses={
        403: {"description": "Forbidden"},
        404: {"description": "User not found"}
    }
)
def remove_user_from_course(course_id: str, user_id: str, is_instructor: Annotated[bool, Depends(is_course_instructor)], session=Depends(get_session), user=Depends(decode_token)):
    if not is_instructor and not user["role"] == models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        session.query(models.CourseMembership).filter(
            models.CourseMembership.user_id == user_id, models.CourseMembership.course_id == course_id).delete()
    except NoResultFound:
        raise HTTPException(status_code=404, detail="User not found")
    session.commit()
    logger.info(f"Removed user {user_id} from course {course_id}")
    

@router.get(
    "/{course_id}/users",
    response_model=schemas.GetCourseMembersResponse,
    dependencies=[Depends(check_if_course_exists)],
    tags=["courses"],
    summary='Get all users in a course',
    description='Get all users in a course.',
    responses={
        404: {"description": "Course not found"}
    }
)
def get_course_users(course_id: str, session=Depends(get_session)):
    res = session.query(models.User, models.CourseMembership).join(models.CourseMembership, models.CourseMembership.user_id == models.User.id).filter(models.CourseMembership.course_id == course_id).all()
    return {
        "data": [{
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "is_instructor": course_membership.is_instructor
        } for user, course_membership in res
        ]
    }
    
@router.get(
    "/",
    tags=["courses"],
    summary='Get all courses',
    description='Get all courses in the system. Only teachers and admins can access this endpoint.',
    responses={
        403: {"description": "Forbidden"}
    },
    response_model=schemas.GetCoursesResponse
)
def get_courses(session=Depends(get_session), page: int = 1, user=Depends(decode_token)):
    if user["role"] not in [models.UserRole.admin, models.UserRole.teacher]:
        raise HTTPException(status_code=403, detail="Only teachers and admins can list all courses")
    return {
        "data": session.query(models.Course).limit(10).offset((page - 1) * 10).all()
    }
    
@router.get(
    "/{course_id}",
    response_model=schemas.GetCourseResponse,
    dependencies=[Depends(check_if_course_exists)],
    tags=["courses"],
    summary='Get a course',
    description='Get a course by id.',
    responses={
        404: {"description": "Course not found"}
    }
)
def get_course(course_id: str, session=Depends(get_session)):
    return {
        "data": session.query(models.Course).filter(models.Course.id == course_id).one()
    }
    
@router.put(
    "/{course_id}/users/{user_id}/settings",
    status_code=204,
    dependencies=[Depends(check_if_course_exists)],
    tags=["courses"],
    summary='Updates the instructor status of a user in a course',
    description='Updates the instructor status of a user in a course. Only admins and course instructors can access this endpoint.',
    responses={
        403: {"description": "Forbidden"},
        404: {"description": "User not found"}
    }
)
def update_user_instrucor_status(course_id: str, user_id: str, body: schemas.UpdateCourseMemberInstrucorStatusRequest, is_instructor: Annotated[bool, Depends(is_course_instructor)], session=Depends(get_session), user=Depends(decode_token)):
    if not is_instructor and not user["role"] == models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        session.query(models.CourseMembership).filter(
            models.CourseMembership.user_id == user_id, models.CourseMembership.course_id == course_id).update({"is_instructor": body.is_instructor})
    except NoResultFound:
        raise HTTPException(status_code=404, detail="User not found")
    new_user_role = session.query(models.User).filter(models.User.id == user_id).one().role
    if body.is_instructor and new_user_role == models.UserRole.student:
        raise HTTPException(status_code=403, detail="Only admins and teachers can add instructors to courses")
    session.commit()
    logger.info(f"Updated users {user_id} instructor status in course {course_id} to {is_instructor}")