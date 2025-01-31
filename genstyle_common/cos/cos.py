import os
from qcloud_cos import CosConfig, CosS3Client

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