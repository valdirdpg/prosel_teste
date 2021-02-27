from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MinioPublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.MINIO_PUBLIC_BUCKET_NAME
    access_key = settings.MINIO_ACCESS_KEY
    secret_key = settings.MINIO_SECRET_KEY
    location = settings.MINIO_MEDIA_LOCATION
    endpoint_url = settings.MINIO_URL
    auto_create_bucket = settings.MINIO_AUTO_CREATE_BUCKET
    object_parameters = settings.MINIO_DEFAULT_OBJECT_PARAMETERS
    bucket_acl = settings.MINIO_PUBLIC_ACL
    querystring_auth = settings.MINIO_PUBLIC_QUERYSTRING_AUTH
    file_overwrite = False


class MinioMediaStorage(S3Boto3Storage):
    bucket_name = settings.MINIO_MEDIA_BUCKET_NAME
    access_key = settings.MINIO_ACCESS_KEY
    secret_key = settings.MINIO_SECRET_KEY
    location = settings.MINIO_MEDIA_LOCATION
    endpoint_url = settings.MINIO_URL
    auto_create_bucket = settings.MINIO_AUTO_CREATE_BUCKET
    object_parameters = settings.MINIO_DEFAULT_OBJECT_PARAMETERS
    bucket_acl = settings.MINIO_PRIVATE_ACL
    file_overwrite = False


class MinioAssestsStorage(S3Boto3Storage):
    bucket_name = settings.MINIO_PUBLIC_BUCKET_NAME
    access_key = settings.MINIO_ACCESS_KEY
    secret_key = settings.MINIO_SECRET_KEY
    location = settings.MINIO_ASSETS_LOCATION
    endpoint_url = settings.MINIO_URL
    auto_create_bucket = settings.MINIO_AUTO_CREATE_BUCKET
    object_parameters = settings.MINIO_DEFAULT_OBJECT_PARAMETERS
    bucket_acl = settings.MINIO_PUBLIC_ACL
    querystring_auth = settings.MINIO_PUBLIC_QUERYSTRING_AUTH
    file_overwrite = True
