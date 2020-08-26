import json
import os
from pathlib import Path
import boto3
import logging
from botocore.exceptions import ClientError


def serialize_as_json(target_object, path, encoding='utf-8'):
    with open(path, 'w', encoding=encoding) as stream:
        stream.write(json.dumps(target_object, indent=4, ensure_ascii=False))


def deserialize_from_json(path, encoding='utf-8'):
    with open(path, 'r', encoding=encoding) as stream:
        return json.loads(stream.read())


def try_create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_file_paths_in_directory(path, patterns):
    return [str(file_path) for pattern in patterns for file_path in Path(path).rglob(pattern)]


def get_image_file_paths_recursive(folder_path, patterns_string):
    patterns = patterns_string.split(',')

    return get_file_paths_in_directory(folder_path, patterns)


class CloudStorage:
    """AWS S3 Upload collection of methods
    :param aws_access_key_id: (optional) If provided overrides AWS CLI
    :param aws_secret_access_key: (optional) If provided overrides AWS CLI
    :param region_name: (optional) AWS region name (i.e. us-east-1)
    :param s3_bucket: (optional) default bucket name
    :param s3_key_prefix: (optional) every upload goes under this prefix as a subdirectory in S3
    :return: True if file was uploaded, else False
    """
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, region_name=None, s3_bucket=None,
                 s3_key_prefix=""):

        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.s3_client = self.session.client('s3')
        self.s3_bucket_default = s3_bucket
        self.s3_key_prefix = s3_key_prefix

    def upload_file(self, local_file, s3_key, s3_bucket=None):
        """Upload a file to an S3 s3_bucket

        :param local_file: File to upload
        :param s3_bucket: s3_bucket to upload to
        :param s3_key: S3 object name. If not specified then local_file is used
        :return: True if file was uploaded, else False
        """

        s3_bucket = s3_bucket or self.s3_bucket_default
        assert s3_bucket, "You must provide an S3 bucket or initialize this class with an S3 bucket"

        # If S3 s3_key was not specified, use local_file
        if s3_key is None:
            s3_key = local_file

        # Upload the file
        try:
            s3_key = os.path.join(self.s3_key_prefix, s3_key).replace("\\", "/")
            print("Uploading: \n\tfrom:\t{}\n\tto:\t{}".format(local_file, s3_key))
            response = self.s3_client.upload_file(local_file, s3_bucket, s3_key)
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def upload_dir(self, local_dir, s3_key, s3_bucket=None):
        """Upload every file in directory to an S3 s3_bucket

        :param local_dir: Directory with files to upload
        :param s3_bucket: s3_bucket to upload to
        :param s3_key: S3 object name. If not specified then local_file is used
        :return: True if file was uploaded, else False
        """

        s3_bucket = s3_bucket or self.s3_bucket_default
        assert s3_bucket, "You must provide an S3 bucket or initialize this class with an S3 bucket"
        assert os.path.isdir(local_dir), "local_dir must be a valid directory and not a file"

        print("Uploading from local: \n\t{}".format(local_dir))
        print("Uploading to S3: \n\tBucket:{}\n\tkey:{}".format(s3_bucket, s3_key))

        for subdir, dirs, files in os.walk(local_dir):
            for file in files:
                # Fixing subdir
                full_path = os.path.join(subdir, file)
                s3_subdir = os.path.basename(os.path.normpath(subdir))
                s3_path = os.path.join(s3_key, s3_subdir, file)
                s3_path = s3_path.replace("\\", "/")

                upload_successful = self.upload_file(local_file=full_path, s3_bucket=s3_bucket, s3_key=s3_path)
                if not upload_successful:
                    print("Upload failed...")
