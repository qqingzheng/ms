import os
from qcloud_cos import CosConfig, CosS3Client
import boto3
from botocore.exceptions import ClientError
import requests


if os.environ['COS_TYPE'] == 'tencent':
    secret_id = os.environ['COS_SECRET_ID']
    secret_key = os.environ['COS_SECRET_KEY']
    region = os.environ['COS_REGION']
    token = None
    scheme = 'https'
    cos_config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
    cos_setting = {
        'bucket': os.environ['COS_BUCKET']
    }

    def upload_file(target, rb_file):
        client = CosS3Client(cos_config)
        response = client.put_object(
            Bucket=cos_setting['bucket'],
            Key=target,
            Body=rb_file,
            StorageClass='STANDARD',
            EnableMD5=False
        )
        return f"https://{cos_setting['bucket']}.cos.{region}.myqcloud.com/{target}"

elif os.environ['COS_TYPE'] == 'aws':
    s3 = boto3.client('s3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name=os.environ['AWS_REGION']
    )
    def upload_file(target, rb_file):
        s3.put_object(
            Bucket=os.environ['AWS_BUCKET'],
            Key=target,
            Body=rb_file
        )
        return f"{os.environ['AWS_CLOUDFRONT_URL']}/{target}"