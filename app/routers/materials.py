from fastapi import APIRouter, Depends, Request
from dependencies import *
from storage import list_files, delete_file, get_presigned_url, PresignedUrlType
import schemas
from fastapi_cache.decorator import cache

router = APIRouter(
    prefix="/courses/{course_id}/lectures/{lecture_id}/materials",
    tags=["materials"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    dependencies=[Depends(check_if_course_exists),
                  Depends(check_if_lecture_exists)],
    response_model=schemas.GetLectureMaterialResponse,
    summary="Get a list of names of files uploaded for a lecture",
    description="Get a list of names of files uploaded for a lecture. Only course members and admins can access this endpoint. The list is cached for 60 seconds.",
)
@cache(expire=60)
async def get_course_materials(request: Request, course_id: str, lecture_id: str, is_member=Depends(is_member_of_course), user=Depends(decode_token)):
    if not is_member and user["role"] is not models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {
        "data": [key.split('/')[-1] for key in list_files(f'{course_id}/{lecture_id}/')]
    }


@router.put(
    "/",
    status_code=201,
    dependencies=[Depends(check_if_course_exists),
                  Depends(check_if_lecture_exists)],
    summary="Get link for uploading lecture material",
    description="Get link for uploading lecture material. If there is already a file with the same name, it will be overwritten. Only course instructors and admins can access this endpoint. The link is presigned which means that it will not work with additional headers. The link is valid for 5 minutes.",
)
def upload_course_material(course_id: str, lecture_id: str, body: schemas.UploadLectureMaterialRequest, user = Depends(decode_token), is_instructor = Depends(is_course_instructor)):
    if user["role"] is not models.UserRole.admin or not is_instructor:
        raise HTTPException(status_code=403, detail="You have to be an admin or instructor to upload lecture material")
    return get_presigned_url(f'{course_id}/{lecture_id}/{body.filename}', PresignedUrlType.PUT)


@router.get(
    "/{filename}",
    dependencies=[Depends(check_if_course_exists), Depends(
        check_if_lecture_exists)],
    summary="Get link for downloading lecture material",
    description="Get link for downloading lecture material. Only course members and admins can access this endpoint. The link is presigned which means that it will not work with additional headers. The link is valid for 5 minutes.",
)
def get_course_material(course_id: str, lecture_id: str, filename: str, is_member=Depends(is_member_of_course), user=Depends(decode_token)):
    if not is_member and user["role"] is not models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not filename in [key.split('/')[-1] for key in list_files(f'{course_id}/{lecture_id}/')]:
        raise HTTPException(status_code=404, detail="File not found")
    return get_presigned_url(f'{course_id}/{lecture_id}/{filename}')


@router.delete(
    "/{filename}",
    status_code=204,
    dependencies=[Depends(check_if_course_exists), Depends(
        check_if_lecture_exists), Depends(check_if_file_exists)],
    summary="Delete lecture material",
    description="Delete lecture material. Only course instructors and admins can access this endpoint.",
)
def delete_course_material(course_id: str, lecture_id: str, filename: str, user = Depends(decode_token), is_instructor = Depends(is_course_instructor)):
    if user["role"] is not models.UserRole.admin or not is_instructor:
        raise HTTPException(status_code=403, detail="You have to be an admin or instructor to delete lecture material")
    return delete_file(f'{course_id}/{lecture_id}/{filename}')
