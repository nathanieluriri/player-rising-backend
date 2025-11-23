from bson import ObjectId
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from limits.strategies import FixedWindowRateLimiter
from datetime import datetime,timedelta
from limits.storage import RedisStorage
import math
from schemas.response_schema import APIResponse
from repositories.tokens_repo import get_access_tokens_no_date_check
from limits import parse
import time   
import os
from celery_worker import celery_app
from contextlib import asynccontextmanager
from core.scheduler import scheduler
from pymongo import MongoClient
import redis
from apscheduler.triggers.interval import IntervalTrigger
from starlette.middleware.sessions import SessionMiddleware
from security.auth import verify_admin_token
from sub_app1.main import app as Node1
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from core.database import db
fs = AsyncIOMotorGridFSBucket(db)
MONGO_URI = os.getenv("MONGO_URL")
REDIS_URI = f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6379')}/0"
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
# --- Heartbeat Function ---
def apscheduler_heartbeat():
        timestamp = time.time()
        redis_client.set("apscheduler:heartbeat", str(timestamp), ex=60)  # expires in 60s
        
        
@asynccontextmanager
async def lifespan(app:FastAPI):
    
    # --- Add Heartbeat Job ---
    scheduler.add_job(
        apscheduler_heartbeat,
        trigger=IntervalTrigger(seconds=15),
        id="apscheduler_heartbeat",
        name="APScheduler Heartbeat",
        replace_existing=True
    )

    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()
    

class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Record the start time before processing the request
        start_time = time.time()
        
        # Process the request and get the response
        response = await call_next(request)
        
        # Calculate the time taken to process the request
        process_time = time.time() - start_time
        
        # You can log the time or set it in the response headers
        response.headers['X-Process-Time'] = str(process_time)
        
        # Optionally, print it for logging purposes
        print(f"Request to {request.url} took {process_time:.6f} seconds")
        
        return response
    
    
    
    
# Create the FastAPI app
app = FastAPI(
    
    lifespan= lifespan,
    title="REST API",
    summary="THIS IS JUST A TEST TO SEE IF AUTOMATED DEPLOYMENT IS WORKING"
     
)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(SessionMiddleware, secret_key="some-random-string")
redis_url = os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL") \
    or f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}/0"


# Setup limiter
storage = RedisStorage(
   redis_url
)

limiter = FixedWindowRateLimiter(storage)

RATE_LIMITS = {
   "annonymous": parse("220/minute"),  # <-- CHANGED FROM 20
   "member": parse("260/minute"),  # <-- CHANGED FROM 60
   "admin": parse("3140/minute"), # <-- CHANGED FROM 140
}

async def get_user_type(request: Request) -> tuple[str, str]:
    """
    Return a tuple of (user_identifier, user_type)
    You can extract from JWT, headers, or session.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        ip_address = request.headers.get("X-Forwarded-For", request.client.host)
        user_id = ip_address
        user_type="annonymous"
        return user_id, user_type if user_type in RATE_LIMITS else "annonymous"
    
    
    token = auth_header.split(" ")[1] 
    access_token  =await get_access_tokens_no_date_check(accessToken=token)
    
    user_id = access_token.userId
    
    user_type = access_token.role

 
    return user_id, user_type if user_type in RATE_LIMITS else "annonymous"

class RateLimitingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id, user_type = await get_user_type(request)
        rate_limit_rule = RATE_LIMITS[user_type]

        # hit() → True if still under limit
        allowed = limiter.hit(rate_limit_rule, user_id)

        # Get current window stats (reset_time, remaining)
        reset_time, remaining = limiter.get_window_stats(rate_limit_rule, user_id)
        seconds_until_reset = max(math.ceil(reset_time - time.time()), 0)

        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={
                    "X-User-Type": user_type,
                    "X-User-Id":user_id,
                    "X-RateLimit-Limit": str(rate_limit_rule.amount),
                    "X-RateLimit-Remaining": str(max(remaining, 0)),
                    "X-RateLimit-Reset": str(seconds_until_reset),
                    "Retry-After": str(seconds_until_reset),
                },
                content=APIResponse(
                    status_code=429,
                    data={
                        "retry_after_seconds": seconds_until_reset,
                        "user_type": user_type,
                    },
                    detail="Too Many Requests",
                ).dict(),
            )

        # Normal flow
        response = await call_next(request)

        # Add rate-limit headers for successful requests too
        response.headers["X-User-Id"]=user_id
        response.headers["X-User-Type"] = user_type
        response.headers["X-RateLimit-Limit"] = str(rate_limit_rule.amount)
        response.headers["X-RateLimit-Remaining"] = str(max(remaining, 0))
        response.headers["X-RateLimit-Reset"] = str(seconds_until_reset)

        return response

 
app.add_middleware(RateLimitingMiddleware)

 

# Add CORS middleware (be cautious in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for HTTPExceptions
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            status_code=exc.status_code,
            data=None,
            detail=exc.detail,
        ).dict()
    )

async def test_scheduler(message):
    print(message)
# Simple test route
@app.get("/",tags=["Health"], include_in_schema=False)
def read_root():
    run_time = datetime.now() + timedelta(seconds=20)
    scheduler.add_job(test_scheduler,"date",run_date=run_time,args=[f"test message {run_time}"],misfire_grace_time=31536000)
    
    data= {"message": "Hello from FasterAPI!"}
    return APIResponse(status_code=200,detail="Successfully fetched data",data=data)


# Clients
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
redis_client = redis.Redis.from_url(REDIS_URI, socket_connect_timeout=2)
# Health check route
@app.get("/health",tags=["Health"])
async def health_check():
    overall_status = "healthy"
    services = {}

    # --- MongoDB Check ---
    start_time = time.perf_counter()
    try:
        mongo_client.admin.command("ping")
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        services["mongo"] = {
            "status": "healthy",
            "latency_ms": latency,
            "message": "MongoDB ping successful"
        }
    except Exception as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        services["mongo"] = {
            "status": "unhealthy",
            "latency_ms": latency,
            "message": str(e)
        }
        overall_status = "degraded"

    # --- Redis Check ---
    start_time = time.perf_counter()
    try:
        redis_client.ping()
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        services["redis"] = {
            "status": "healthy",
            "latency_ms": latency,
            "message": "Redis ping successful"
        }
    except Exception as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        services["redis"] = {
            "status": "unhealthy",
            "latency_ms": latency,
            "message": str(e)
        }
        overall_status = "degraded"

    # --- Worker (Heartbeat) Check ---
    start_time = time.perf_counter()
    # Check APScheduler
    try:
        aps_heartbeat = redis_client.get("apscheduler:heartbeat")
        if aps_heartbeat:
            last_seen = float(aps_heartbeat)
            age = time.time() - last_seen
            if age <= 30:
                services["apscheduler"] = {
                    "status": "healthy",
                    "latency_ms": 0,
                    "message": f"Last heartbeat {int(age)}s ago"
                }
            else:
                services["apscheduler"] = {
                    "status": "degraded",
                    "latency_ms": 0,
                    "message": f"Stale heartbeat (last seen {int(age)}s ago)"
                }
                overall_status = "degraded"
        else:
            services["apscheduler"] = {
                "status": "unhealthy",
                "latency_ms": 0,
                "message": "No heartbeat found"
            }
            overall_status = "degraded"
    except Exception as e:
        services["apscheduler"] = {
            "status": "unhealthy",
            "latency_ms": 0,
            "message": str(e)
        }
        overall_status = "degraded"

    # --- Final Structured Response ---
    data = {
        "status": overall_status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "services": services
    }
     # --- Celery health check ---
    try:
        result = celery_app.send_task("celery_worker.test_scheduler", args=["Health check ping"])
        response = result.get(timeout=5)
        services["celery"] = {
            "status": "healthy",
            "latency_ms": 0,
            "message": f"Worker response received successfully",
            "task_id": result.id
        }
    except TimeoutError:
        services["celery"] = {
            "status": "unhealthy",
            "latency_ms": 0,
            "message": "Celery task timed out"
        }
        overall_status = "degraded"
    except Exception as e:
        services["celery"] = {
            "status": "unhealthy",
            "latency_ms": 0,
            "message": str(e)
        }
        overall_status = "degraded"

    # --- Final response ---


    return APIResponse(
        status_code=200 if overall_status == "healthy" else 207,
        detail=f"Health check completed with status: {overall_status}",
        data={"status": overall_status, "services": services}
    )


@app.get("/task/{task_id}",tags=["Tasks"])
def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "state": result.state,    # PENDING, STARTED, SUCCESS, FAILURE
        "ready": result.ready(),
    }

    if result.successful():
        response["result"] = result.get()

    elif result.failed():
        response["error"] = str(result.result)

    return response

@app.get("/health-detailed",tags=["Health"], summary="Performs a detailed health check of all integrated services")
async def health_check():
    services = {}
    # This list will track the status of all services
    service_statuses = [] 
    
 

    # --- MongoDB Check ---
    service_name = "mongo"
    service_desc = "Primary Database (MongoDB)"
    start_time = time.perf_counter()
    try:
        mongo_client.admin.command("ping")
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        status = "healthy"
        services[service_name] = {
            "description": service_desc,
            "status": status,
            "latency_ms": latency,
            "message": "Connection successful and ping acknowledged."
        }
    except Exception as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        status = "unhealthy"
        services[service_name] = {
            "description": service_desc,
            "status": status,
            "latency_ms": latency,
            "message": f"Connection failed: {str(e)}"
        }
    service_statuses.append(status)

    # --- Redis Check ---
    service_name = "redis"
    service_desc = "Cache & Message Broker (Redis)"
    start_time = time.perf_counter()
    try:
        redis_client.ping()
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        status = "healthy"
        services[service_name] = {
            "description": service_desc,
            "status": status,
            "latency_ms": latency,
            "message": "Connection successful and ping acknowledged."
        }
    except Exception as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        status = "unhealthy"
        services[service_name] = {
            "description": service_desc,
            "status": status,
            "latency_ms": latency,
            "message": f"Connection failed: {str(e)}"
        }
    service_statuses.append(status)

    # --- APScheduler (Heartbeat) Check ---
    service_name = "apscheduler"
    service_desc = "Internal Job Scheduler (APScheduler)"
    start_time = time.perf_counter()
    try:
        # Check for the heartbeat key set by the scheduler
        aps_heartbeat = redis_client.get("apscheduler:heartbeat")
        latency = round((time.perf_counter() - start_time) * 1000, 2) # Latency of the check itself
        
        if aps_heartbeat:
            last_seen = float(aps_heartbeat)
            age = time.time() - last_seen
            
            if age <= 30: # Healthy if heartbeat is within 30 seconds
                status = "healthy"
                message = f"Scheduler is active. Last heartbeat {int(age)}s ago."
            else: # Degraded if heartbeat is stale
                status = "degraded"
                message = f"Stale heartbeat. Last seen {int(age)}s ago. Scheduler may be stuck or overloaded."
            
            services[service_name] = {
                "description": service_desc,
                "status": status,
                "latency_ms": latency,
                "message": message
            }
        else: # Unhealthy if no heartbeat key is found
            status = "unhealthy"
            services[service_name] = {
                "description": service_desc,
                "status": status,
                "latency_ms": latency,
                "message": "No heartbeat found. Scheduler may be down or has not run yet."
            }
    except Exception as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        status = "unhealthy"
        services[service_name] = {
            "description": service_desc,
            "status": status,
            "latency_ms": latency,
            "message": f"Failed to check scheduler heartbeat: {str(e)}"
        }
    service_statuses.append(status)

    # --- Celery Worker Check ---
    # This check is now run *before* the final response is built
    service_name = "celery"
    service_desc = "Background Task Worker (Celery)"
    start_time = time.perf_counter()
    task_id = None
    try:
        result = celery_app.send_task("celery_worker.test_scheduler", args=["Health check ping"])
        task_id = result.id
        # Wait for 5 seconds for the worker to respond
        response = result.get(timeout=5) 
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        status = "healthy"
        services[service_name] = {
            "description": service_desc,
            "status": status,
            "latency_ms": latency, # Now captures actual task round-trip time
            "message": f"Worker task executed successfully. Response: '{response}'",
            "task_id": task_id
        }
    except TimeoutError:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        status = "unhealthy"
        services[service_name] = {
            "description": service_desc,
            "status": status,
            "latency_ms": latency, # Will be ~5000+
            "message": "Celery task timed out after 5 seconds. Worker may be busy or down.",
            "task_id": task_id
        }
    except Exception as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        status = "unhealthy"
        services[service_name] = {
            "description": service_desc,
            "status": status,
            "latency_ms": latency,
            "message": f"Celery task failed to execute: {str(e)}",
            "task_id": task_id
        }
    service_statuses.append(status)

    # --- Determine Overall Status ---
 
    if "unhealthy" in service_statuses:
        overall_status = "unhealthy"
    elif "degraded" in service_statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    # --- Final Structured Response ---
 
    data = {
        "status": overall_status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), # Using ISO 8601 format
        "services": services
    }
    
    # --- Final response ---
     
    http_status_code = 200 if overall_status == "healthy" else 207

   
    return APIResponse(
        status_code=http_status_code,
        detail=f"Health check completed with status: {overall_status}",
        data=data  
    )
    
    
# ------------------------------
# Public route to serve videos
# ------------------------------

@app.get("/videos/{video_id}")
async def get_video(video_id: str):
    try:
        # NOT awaited
        download_stream = await fs.open_download_stream(ObjectId(video_id))

        return StreamingResponse(
            download_stream,
            media_type=download_stream.metadata.get("content_type", "video/mp4")
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Video not found")
    
app.mount("/api/v1", Node1)
# --- auto-routes-start ---
from api.v1.admin_route import router as v1_admin_route_router
from api.v1.blog import router as v1_blog_router
from api.v1.media_host import router as v1_image_host_router


app.include_router(v1_admin_route_router, prefix='/v1')
app.include_router(v1_blog_router, prefix='/v1',dependencies=[Depends(verify_admin_token)])
app.include_router(v1_image_host_router, prefix='/v1')

# --- auto-routes-end ---