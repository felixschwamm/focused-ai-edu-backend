from pydantic import BaseModel
from models import UserRole

class Course(BaseModel):
    id : str
    name: str
    
class Lecture(BaseModel):
    id: str
    name: str
    completed: bool
    
class GetLecturesResponse(BaseModel):
    data: list[Lecture]
    
    model_config = {
        "from_attributes": True
    }
    
class PostUserRequest(BaseModel):
    name: str
    role: UserRole
    
class PostLectureRequest(BaseModel):
    name: str
    
class GetLectureResponse(BaseModel):
    data: Lecture
    
    model_config = {
        "from_attributes": True
    }
    
class UploadLectureMaterialRequest(BaseModel):
    filename: str
    
class PostCourseRequest(BaseModel):
    name: str
    
class LoginResponse(BaseModel):
    token: str
    
class LoginRequest(BaseModel):
    user_id: str
    password: str
    
class GetLectureMaterialResponse(BaseModel):
    data: list[str]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    "file1.pdf",
                    "file2.txt",
                    "file3.docx"
                ]
            }
        
        }
    }
    
class User(BaseModel):
    name: str
    role: UserRole
    id: str
    
class GetUserResponse(BaseModel):
    data: list[User]
    
    model_config = {
        "from_attributes": True
    }
        
class GetCoursesResponse(BaseModel):
    data: list[Course]
    
    model_config = {
        "from_attributes": True
    }
    
class GetCourseResponse(BaseModel):
    data: Course
    
    model_config = {
        "from_attributes": True
    }
        
class AddUserToCourseRequest(BaseModel):
    user_id: str
    is_instructor: bool = False
    
class CourseMember(User):
    is_instructor: bool
    
class GetCourseMembersResponse(BaseModel):
    data: list[CourseMember]
    
    model_config = {
        "from_attributes": True
    }
    
class UpdateCourseMemberInstrucorStatusRequest(BaseModel):
    is_instructor: bool
    
class UpdateLectureStatusRequest(BaseModel):
    completed: bool

class GetLectureStatusResponse(BaseModel):
    completed: bool