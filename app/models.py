from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Enum, ForeignKey, Boolean
import enum

class UserRole(enum.Enum):
    teacher = "teacher"
    student = "student"
    admin = "admin"

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    name: Mapped[str] = mapped_column('user_name', String)
    role: Mapped[UserRole] = mapped_column('user_role', Enum(UserRole))
    id: Mapped[str] = mapped_column('user_id', String, primary_key=True)
    
class Course(Base):
    __tablename__ = 'courses'
    
    id: Mapped[str] = mapped_column('course_id', String, primary_key=True)
    name: Mapped[str] = mapped_column('course_name', String)
    
class CourseMembership(Base):
    __tablename__ = 'course_membership'
    
    user_id: Mapped[str] = mapped_column('user_id', String, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    course_id: Mapped[str] = mapped_column('course_id', String,ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
    is_instructor: Mapped[bool] = mapped_column('is_instructor', Boolean)
    
    user: Mapped[User] = relationship("User", backref="course_membership")
    course: Mapped[Course] = relationship("Course", backref="course_membership")
    
class Lecture(Base):
    __tablename__ = 'lectures'
    
    id: Mapped[str] = mapped_column('lecture_id', String, primary_key=True)
    course_id: Mapped[str] = mapped_column('course_id', String, ForeignKey('courses.course_id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column('lecture_name', String)
    
    course: Mapped[Course] = relationship("Course", backref="lectures")
    
class LectureUserProgress(Base):
    __tablename__ = 'lecture_user_progress'
    
    user_id: Mapped[str] = mapped_column('user_id', String, ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    lecture_id: Mapped[str] = mapped_column('lecture_id', String, ForeignKey('lectures.lecture_id', ondelete='CASCADE'), primary_key=True)
    completed: Mapped[bool] = mapped_column('lecture_completed', Boolean)
    
    user: Mapped[User] = relationship("User", backref="lecture_user_progress")
    lecture: Mapped[Lecture] = relationship("Lecture", backref="lecture_user_progress")