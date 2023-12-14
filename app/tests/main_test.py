import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from fastapi.testclient import TestClient
from main import app, get_session
from sqlalchemy.pool import StaticPool
from utils import generate_mock_jwt


@pytest.fixture
def test_db() -> sessionmaker:
    engine = create_engine(
        'sqlite:///:memory:', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def admin_user(test_db):
    session = test_db()
    user = models.User(id="admin_id", name="admin_name",
                       role=models.UserRole.admin)
    session.add(user)
    session.commit()
    session.close()
    return {
        "id": "admin_id",
        "name": "admin_name",
        "role": "admin"
    }


@pytest.fixture
def course_with_instructor(test_db):
    session = test_db()
    instructor = models.User(id="instructor_id", name="instructor_name",
                                role=models.UserRole.teacher)
    session.add(instructor)
    course = models.Course(id="course_id", name="course_name")
    session.add(course)
    session.add(models.CourseMembership(
        user_id="instructor_id",
        course_id=course.id,
        is_instructor=True,
    ))
    session.commit()
    session.close()
    return {
        "course": {
            "id": "course_id",
            "name": "course_name"
        },
        "instructor": {
            "id": "instructor_id",
            "name": "instructor_name",
            "role": "teacher"
        }
    }


@pytest.fixture
def teacher_user(test_db):
    session = test_db()
    user = models.User(id="teacher_id", name="teacher_name",
                       role=models.UserRole.teacher)
    session.add(user)
    session.commit()
    session.close()
    return {
        "id": "teacher_id",
        "name": "teacher_name",
        "role": "teacher"
    }


@pytest.fixture
def student_user(test_db):
    session = test_db()
    user = models.User(id="student_id", name="student_name",
                       role=models.UserRole.student)
    session.add(user)
    session.commit()
    session.close()
    return {
        "id": "student_id",
        "name": "student_name",
        "role": "student"
    }


@pytest.fixture
def test_client(test_db):

    def override_get_session():
        try:
            session = test_db()
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def test_get_users(test_db, test_client: TestClient):

    # Create a session
    session = test_db()

    # Create a admin user
    admin = models.User(
        id="admin_id", name="admin_name", role=models.UserRole.admin)

    # Create a teacher user
    teacher = models.User(
        id="teacher_id", name="teacher_name", role=models.UserRole.teacher)

    # Create a student user
    student = models.User(
        id="student_id", name="student_name", role=models.UserRole.student)

    # Add the user to the session
    session.add(admin)
    session.add(teacher)
    session.add(student)

    # Commit the session
    session.commit()

    # Check if the user exists
    assert session.query(models.User).filter(
        models.User.id == teacher.id).one() == teacher
    assert session.query(models.User).filter(
        models.User.id == student.id).one() == student

    # Check if the endpoint returns the users for admin
    assert test_client.get("/users", headers={'Authorization': 'Bearer ' + generate_mock_jwt('admin_id')}).json() == {
        "data": [
            {
                "id": "admin_id",
                "name": "admin_name",
                "role": "admin"
            },
            {
                "id": "teacher_id",
                "name": "teacher_name",
                "role": "teacher"
            },
            {
                "id": "student_id",
                "name": "student_name",
                "role": "student"
            }
        ]
    }

    # Check if the endpoint returns the users for teacher
    assert test_client.get("/users", headers={'Authorization': 'Bearer ' + generate_mock_jwt('teacher_id')}).json() == {
        "data": [
            {
                "id": "admin_id",
                "name": "admin_name",
                "role": "admin"
            },
            {
                "id": "teacher_id",
                "name": "teacher_name",
                "role": "teacher"
            },
            {
                "id": "student_id",
                "name": "student_name",
                "role": "student"
            }
        ]
    }

    # Check if the endpoint returns forbidden for student
    assert test_client.get("/users", headers={'Authorization': 'Bearer ' +
                                              generate_mock_jwt('student_id')}).status_code == 403


def test_get_courses(test_db, test_client: TestClient):

    # Create a session
    session = test_db()

    # Create a admin user
    admin = models.User(
        id="admin_id", name="admin_name", role=models.UserRole.admin)

    # Create a teacher user
    teacher = models.User(
        id="teacher_id", name="teacher_name", role=models.UserRole.teacher)

    # Create a student user
    student = models.User(
        id="student_id", name="student_name", role=models.UserRole.student)

    # Create a course
    course = models.Course(id="course_id", name="course_name")

    # Add to the session
    session.add(admin)
    session.add(teacher)
    session.add(student)
    session.add(course)

    # Commit the session
    session.commit()

    # Check if the course exists
    assert session.query(models.Course).filter(
        models.Course.id == course.id).one() == course

    # Check if the endpoint returns the courses for admin
    assert test_client.get("/courses", headers={'Authorization': 'Bearer ' + generate_mock_jwt('admin_id')}).json() == {
        "data": [
            {
                "id": "course_id",
                "name": "course_name"
            }
        ]
    }

    # Check if the endpoint returns the courses for teacher
    assert test_client.get("/courses", headers={'Authorization': 'Bearer ' + generate_mock_jwt('teacher_id')}).json() == {
        "data": [
            {
                "id": "course_id",
                "name": "course_name"
            }
        ]
    }

    # Check if the endpoint returns forbidden for student
    assert test_client.get("/courses", headers={'Authorization': 'Bearer ' +
                                                generate_mock_jwt('student_id')}).status_code == 403


def test_create_course(test_db, test_client: TestClient):
    session = test_db()

    teacher = models.User(id="user_id", name="user_name",
                          role=models.UserRole.teacher)

    session.add(teacher)
    session.commit()

    # Check if the endpoint returns the courses
    assert test_client.post("/courses", json={"name": "course_name"}, headers={
        "Authorization": "Bearer " + generate_mock_jwt("user_id")}).status_code == 201

    # Check if the course exists
    course = session.query(models.Course).filter(
        models.Course.name == "course_name").one()

    assert course.name == "course_name"


def test_delete_course(test_db, test_client: TestClient, admin_user, teacher_user, student_user):

    # create a session
    session = test_db()

    # create a course
    course = models.Course(id="course_id", name="course_name")
    session.add(course)
    session.commit()

    # check if the course exists
    assert session.query(models.Course).filter(
        models.Course.id == course.id).one() == course

    # check if the endpoint returns forbidden for student
    assert test_client.delete("/courses/course_id", headers={'Authorization': 'Bearer ' +
                                                             generate_mock_jwt('student_id')}).status_code == 403

    # check if the endpoint returns forbidden for teacher
    assert test_client.delete("/courses/course_id", headers={'Authorization': 'Bearer ' +
                                                             generate_mock_jwt('teacher_id')}).status_code == 403

    # check if the endpoint returns 204 for admin
    assert test_client.delete("/courses/course_id", headers={'Authorization': 'Bearer ' +
                                                             generate_mock_jwt('admin_id')}).status_code == 204

    # check if the course is deleted
    assert session.query(models.Course).filter(
        models.Course.id == "course_id").count() == 0

    # add teacher as instructor to the course
    session.add(models.CourseMembership(
        user_id=teacher_user["id"],
        course_id=course.id,
        is_instructor=True,
    ))

    # create the course again
    course = models.Course(id="course_id", name="course_name")
    session.add(course)
    session.commit()

    # check if the endpoint returns 204 for teacher
    assert test_client.delete("/courses/course_id", headers={'Authorization': 'Bearer ' +
                                                             generate_mock_jwt('teacher_id')}).status_code == 204

    # check if the course is deleted
    assert session.query(models.Course).filter(
        models.Course.id == "course_id").count() == 0


def test_add_user_to_course(course_with_instructor, test_client: TestClient, admin_user, teacher_user, student_user, test_db):

    session = test_db()

    # check if the endpoint returns forbidden for student
    assert test_client.post(f"/courses/{course_with_instructor['course']['id']}/users", json={"user_id": "student_id", "is_instructor": False}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                         generate_mock_jwt(student_user["id"])}).status_code == 403

    # check if the endpoint returns forbidden for teacher
    assert test_client.post(f"/courses/{course_with_instructor['course']['id']}/users", json={"user_id": "student_id", "is_instructor": False}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                         generate_mock_jwt(teacher_user["id"])}).status_code == 403

    # check if the endpoint returns 201 for admin
    assert test_client.post(f"/courses/{course_with_instructor['course']['id']}/users", json={"user_id": "student_id", "is_instructor": False}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                         generate_mock_jwt(admin_user["id"])}).status_code == 201

    # check if user is added to the course
    assert course_with_instructor["course"]["id"] in [course.id for course in session.query(models.Course).join(models.CourseMembership, models.CourseMembership.course_id == models.Course.id).filter(
        models.CourseMembership.user_id == "student_id").all()]

    # remove the user from the course
    session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == "student_id").delete()

    # check if the endpoint returns 201 for teacher with is_instructor = True
    assert test_client.post(f"/courses/{course_with_instructor['course']['id']}/users", json={"user_id": "student_id", "is_instructor": False}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                         generate_mock_jwt(course_with_instructor["instructor"]["id"])}).status_code == 201

    # check if user is added to the course
    assert course_with_instructor["course"]["id"] in [course.id for course in session.query(models.Course).join(models.CourseMembership, models.CourseMembership.course_id == models.Course.id).filter(
        models.CourseMembership.user_id == "student_id").all()]

    # remove the user from the course
    session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == "student_id").delete()

    # check if the endpoint returns 403 if one tries to add an student as instructor
    assert test_client.post(f"/courses/{course_with_instructor['course']['id']}/users", json={"user_id": "student_id", "is_instructor": True}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                        generate_mock_jwt(course_with_instructor["instructor"]["id"])}).status_code == 403


def test_set_course_member_settings(course_with_instructor, test_client: TestClient, admin_user, teacher_user, student_user, test_db):

    session = test_db()

    # add student to the course
    session.add(models.CourseMembership(
        user_id=student_user["id"],
        course_id=course_with_instructor["course"]["id"],
        is_instructor=False,
    ))

    # add teacher to the course
    session.add(models.CourseMembership(
        user_id=teacher_user["id"],
        course_id=course_with_instructor["course"]["id"],
        is_instructor=False,
    ))

    # add admin to the course
    session.add(models.CourseMembership(
        user_id=admin_user["id"],
        course_id=course_with_instructor["course"]["id"],
        is_instructor=False,
    ))

    # commit the session
    session.commit()

    # check if the endpoint returns forbidden for student
    assert test_client.put(f"/courses/{course_with_instructor['course']['id']}/users/{student_user['id']}/settings", json={"is_instructor": True}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                            generate_mock_jwt(student_user["id"])}).status_code == 403

    # check if the endpoint returns forbidden for teacher
    assert test_client.put(f"/courses/{course_with_instructor['course']['id']}/users/{student_user['id']}/settings", json={"is_instructor": True}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                            generate_mock_jwt(teacher_user["id"])}).status_code == 403

    # check if the endpoint returns 204 for admin
    assert test_client.put(f"/courses/{course_with_instructor['course']['id']}/users/{teacher_user['id']}/settings", json={"is_instructor": True}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                            generate_mock_jwt(admin_user["id"])}).status_code == 204

    # check if teacher is now instructor
    assert session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == "teacher_id").one().is_instructor == True

    # check if the endpoint returns 204 for teacher with is_instructor = True
    assert test_client.put(f"/courses/{course_with_instructor['course']['id']}/users/{admin_user['id']}/settings", json={"is_instructor": True}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                          generate_mock_jwt(course_with_instructor["instructor"]["id"])}).status_code == 204

    # check if admin is now instructor
    assert session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == "admin_id").one().is_instructor == True

    # check if the endpoint returns 403 if one tries to add an student as instructor
    assert test_client.put(f"/courses/{course_with_instructor['course']['id']}/users/{student_user['id']}/settings", json={"is_instructor": True}, headers={'Authorization': 'Bearer ' +
                                                                                                                                                            generate_mock_jwt(course_with_instructor["instructor"]["id"])}).status_code == 403


def test_remove_user_from_course(test_db, student_user, admin_user, teacher_user, course_with_instructor, test_client: TestClient):

    # create a session
    session = test_db()

    # add student to the course
    session.add(models.CourseMembership(
        user_id=student_user["id"],
        course_id=course_with_instructor["course"]["id"],
        is_instructor=False,
    ))

    # add teacher to the course
    session.add(models.CourseMembership(
        user_id=teacher_user["id"],
        course_id=course_with_instructor["course"]["id"],
        is_instructor=False,
    ))

    session.commit()

    # Check if student can remove the teacher from the course (should return 403)
    assert test_client.delete(f"/courses/{course_with_instructor['course']['id']}/users/{teacher_user['id']}", headers={'Authorization': 'Bearer ' +
                                                                                                                        generate_mock_jwt(student_user["id"])}).status_code == 403

    # check if admin can remove student from the course
    assert test_client.delete(f"/courses/{course_with_instructor['course']['id']}/users/{student_user['id']}", headers={'Authorization': 'Bearer ' +
                                                                                                                        generate_mock_jwt(admin_user["id"])}).status_code == 204

    # check if student is removed from the course
    assert session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == "student_id").count() == 0

    # add student to the course
    session.add(models.CourseMembership(
        user_id=student_user["id"],
        course_id=course_with_instructor["course"]["id"],
        is_instructor=False,
    ))

    session.commit()

    # check if teacher can remove student from the course (should return 403)
    assert test_client.delete(f"/courses/{course_with_instructor['course']['id']}/users/{student_user['id']}", headers={'Authorization': 'Bearer ' +
                                                                                                                        generate_mock_jwt(teacher_user["id"])}).status_code == 403

    # check if student is not removed from the course
    assert session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == "student_id").count() == 1

    # make teacher instructor
    session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == "teacher_id").one().is_instructor = True

    session.commit()

    # check if teacher can remove student from the course (should return 204)
    assert test_client.delete(f"/courses/{course_with_instructor['course']['id']}/users/{student_user['id']}", headers={'Authorization': 'Bearer ' +
                                                                                                                        generate_mock_jwt(teacher_user["id"])}).status_code == 204

    # check if student is removed from the course
    assert session.query(models.CourseMembership).filter(
        models.CourseMembership.user_id == "student_id").count() == 0
