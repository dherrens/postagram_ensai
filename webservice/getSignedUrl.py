import logging
import boto3
from boto3.dynamodb.conditions import Key
import os
import json
import uuid
from pathlib import Path
from botocore.exceptions import ClientError

s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))
logger = logging.getLogger("uvicorn")

def getSignedUrl(filename: str,filetype: str, postId: str, user):
    bucket = os.getenv("BUCKET")
    filename = f'{uuid.uuid4()}{Path(filename).name}'
    object_name = f"{user}/{postId}/{filename}"

    try:
        url = s3_client.generate_presigned_url(
            Params={
            "Bucket": bucket,
            "Key": object_name,
            "ContentType": filetype
        },
            ClientMethod='put_object'
        )

        dynamodb = boto3.resource('dynamodb', region_name=os.getenv("REGION"))
        table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))

        table.update_item(
            Key={
                "user": f"USER#{user}",
                "id": f"POST#{postId}",
            },
            AttributeUpdates={
                "image": {
                    "Value": object_name,
                    "Action": "PUT"
                }
            },
            ReturnValues='UPDATED_NEW'
        )

    except ClientError as e:
        logging.error(e)


    logger.info(f'Url: {url}')
    return {
            "uploadURL": url,
            "objectName" : object_name
        }

def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object
    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_name
            },
            ExpiresIn=expiration
        )
    except ClientError as e:
        logging.error(e)
        return None
    # The response contains the presigned URL
    return response
