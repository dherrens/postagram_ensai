import boto3
import os
from dotenv import load_dotenv
from typing import Union
import logging
from fastapi import FastAPI, Request, status, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import uuid
import json

from getSignedUrl import getSignedUrl, create_presigned_url

load_dotenv()

app = FastAPI()
logger = logging.getLogger("uvicorn")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logger.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class Post(BaseModel):
    title: str
    body: str


dynamodb = boto3.resource('dynamodb', region_name=os.getenv("REGION"))
table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))

@app.post("/posts")
async def post_a_post(post: Post, authorization: str | None = Header(default=None)):

    logger.info(f"title : {post.title}")
    logger.info(f"body : {post.body}")
    logger.info(f"user : {authorization}")

    dynamodb = boto3.resource('dynamodb', region_name=os.getenv("REGION"))

    table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))

    mon_post = {
        'user': f"USER#{authorization}",
        'id': f"POST#{uuid.uuid4()}",
        'title': post.title,
        'body': post.body,
    }
    reponse = table.put_item(
        Item=mon_post
    )

    # Doit retourner le résultat de la requête la table dynamodb
    return reponse

@app.get("/posts")
async def get_all_posts(user: Union[str, None] = None):

    # Doit retourner une liste de post
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv("REGION"))

    table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))

    if (user is None):
        posts = table.scan()
    else:
        posts = table.query(
            Select='ALL_ATTRIBUTES',
            ExpressionAttributeNames={"#user": "user"},
            KeyConditionExpression="#user = :user",
            ExpressionAttributeValues={
                ":user": f"USER#{user}",
            },
        )
    
    for item in posts["Items"]:
        if item.get('image') is not None:
            item['image'] = create_presigned_url(os.getenv("BUCKET"), item['image'])

    return posts["Items"]

    
@app.delete("/posts/{post_id}")
async def get_post_user_id(post_id: str):
    # Doit retourner le résultat de la requête la table dynamodb
    return []

@app.get("/signedUrlPut")
async def get_signed_url_put(filename: str,filetype: str, postId: str,authorization: str | None = Header(default=None)):
    return getSignedUrl(filename, filetype, postId, authorization)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")

