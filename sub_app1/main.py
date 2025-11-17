from fastapi import Depends, FastAPI
from repositories.tokens_repo import get_access_tokens_no_date_check
from security.auth import verify_any_token
from security.encrypting_jwt import decode_jwt_token
from sub_app1.routes.blog import router as blog_router
import os
import time
import math
import redis
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from limits import parse
from limits.storage import RedisStorage
from limits.strategies import FixedWindowRateLimiter
from typing import Tuple
from schemas.response_schema import APIResponse

 

app = FastAPI(title="Rest API For Users To Fetch Blogs")
 
# Include routes
app.include_router(blog_router, prefix="/articles", tags=["Read articles"])
