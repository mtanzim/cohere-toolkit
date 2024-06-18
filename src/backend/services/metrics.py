import asyncio
import hashlib
import json
import os
import threading
import time
import uuid

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import Message

from backend.chat.collate import to_dict
from backend.schemas.metrics import MetricsData

REPORT_ENDPOINT = os.getenv("REPORT_ENDPOINT", "")

import time

from starlette.responses import Response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.trace_id = str(uuid.uuid4())
        response = await call_next(request)
        data = self.get_data(request.scope, response, request)
        threading.Thread(target=report_metrics_thread, args=(data,)).start()
        return response

    def get_data(self, scope, response, request):
        data = {}
        trace_id = None
        if hasattr(request.state, "trace_id"):
            trace_id = request.state.trace_id

        if scope["type"] != "http":
            return None

        data = MetricsData(
            method=self.get_method(scope),
            endpoint_name=self.get_endpoint_name(scope, request),
            user_id_hash=self.get_user_id_hash(request),
            success=self.get_success(response),
            trace_id=trace_id,
            status_code=self.get_status_code(response),
            object_ids=self.get_object_ids(request),
            error=self.get_error(response),
        )

        return data

    def get_method(self, scope):
        try:
            return scope["method"].lower()
        except KeyError:
            return "unknown"
        except Exception as e:
            print("Failed to get method:", e)
            return "unknown"

    def get_endpoint_name(self, scope, request):
        try:
            path = scope["path"]
            # Replace path parameters with their names
            for key, value in request.path_params.items():
                path = path.replace(value, f":{key}")
            return path.lower()
        except KeyError:
            return "unknown"
        except Exception as e:
            print("Failed to get endpoint name:", e)
            return "unknown"

    def get_status_code(self, response):
        try:
            return response.status_code
        except Exception as e:
            print("Failed to get status code:", e)
            return 500

    def get_success(self, response):
        try:
            return 200 <= response.status_code < 400
        except Exception as e:
            print("Failed to get success:", e)
            return False

    def get_user_id_hash(self, request):
        try:
            user_id = request.headers.get("User-Id", None)
            return hash_string(user_id)
        except Exception as e:
            print("Failed to get user id hash:", e)
            return None

    def get_object_ids(self, request):
        object_ids = {}
        try:
            for key, value in request.path_params.items():
                object_ids[key] = hash_string(value)

            for key, value in request.query_params.items():
                object_ids[key] = hash_string(value)

            return object_ids
        except Exception as e:
            print("Failed to get object ids:", e)
            return {}

    def get_error(self, response):
        try:
            if 400 <= response.status_code < 600:
                return response.read().decode()
            return None
        except Exception as e:
            print("Failed to get error:", e)
            return None


def hash_string(s):
    if s is None:
        return None

    return hashlib.sha256(s.encode()).hexdigest().lower()


async def report_metrics(data):
    if not isinstance(data, dict):
        data = to_dict(data)

    data["secret"] = "secret"

    if not REPORT_ENDPOINT:
        print("No report endpoint set")
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(REPORT_ENDPOINT, json=data)
    except Exception as e:
        print("Failed to report metrics:", e)


def report_metrics_thread(data):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(report_metrics(data))
    loop.close()
