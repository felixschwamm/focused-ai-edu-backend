import boto3
import os
import dotenv
from io import IOBase
from botocore.response import StreamingBody
from enum import Enum
from loguru import logger

dotenv.load_dotenv()

_BUCKET_NAME = os.getenv("S3_BUCKET")
_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

_s3_client = boto3.client(
    "s3",
    aws_access_key_id=_ACCESS_KEY_ID,
    aws_secret_access_key=_SECRET_ACCESS_KEY,
)


class PresignedUrlType(Enum):
    GET = "get_object"
    PUT = "put_object"


def upload_file(file_obj: IOBase, key: str) -> None:
    """
        Uploads a file to S3

        :param file_obj: The file object to upload
        :param key: The key to upload the file to
    """

    _s3_client.upload_fileobj(
        file_obj,
        _BUCKET_NAME,
        key,
    )


def get_file(key: str) -> StreamingBody:
    return _s3_client.get_object(
        Bucket=_BUCKET_NAME,
        Key=key,
    )["Body"]


def delete_file(key: str) -> None:
    _s3_client.delete_object(
        Bucket=_BUCKET_NAME,
        Key=key,
    )
    logger.info(f"Deleted file {key}")


def list_files(prefix: str) -> list[str]:
    res = _s3_client.list_objects_v2(
        Bucket=_BUCKET_NAME,
        Prefix=prefix,
    )
    if "Contents" not in res:
        return []
    return [
        item["Key"]
        for item in res["Contents"]
    ]


def check_if_file_exists(key: str) -> bool:
    return len(list_files(key)) > 0


def get_presigned_url(key: str, type: PresignedUrlType = PresignedUrlType.GET) -> str:
    logger.trace(f"Generating presigned url for {key}")
    return _s3_client.generate_presigned_url(
        "get_object" if type == PresignedUrlType.GET else "put_object",
        Params={
            "Bucket": _BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=5 * 60,
    )


if __name__ == "__main__":
    print(get_presigned_url("test.txt"))
