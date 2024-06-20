import asyncio
import hashlib
import logging
import os
import threading
import uuid
import json

from httpx import AsyncHTTPTransport
from httpx._client import AsyncClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse

from backend.chat.collate import to_dict
from backend.schemas.metrics import MetricsData

REPORT_ENDPOINT = os.getenv("REPORT_ENDPOINT", None)
NUM_RETRIES = 0

import time

from starlette.responses import Response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.trace_id = str(uuid.uuid4())
        request.state.agent = None
        request.state.user = None

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = time.perf_counter() - start_time

        data = self.get_data(request.scope, response, request, duration_ms)
        threading.Thread(target=report_metrics_thread, args=(data,)).start()
        return response

    def get_data(self, scope, response, request, duration_ms):
        data = {}

        if scope["type"] != "http":
            return None

        agent = self.get_agent(request)
        agent_id = agent.get("id", None) if agent else None

        data = MetricsData(
            method=self.get_method(scope),
            endpoint_name=self.get_endpoint_name(scope, request),
            user_id=self.get_user_id(request),
            user=self.get_user(request),
            success=self.get_success(response),
            trace_id=request.state.trace_id,
            status_code=self.get_status_code(response),
            object_ids=self.get_object_ids(request),
            assistant=agent,
            assistant_id=agent_id,
            duration_ms=duration_ms,
        )

        return data

    def get_method(self, scope):
        try:
            return scope["method"].lower()
        except KeyError:
            return "unknown"
        except Exception as e:
            logging.warning(f"Failed to get method:  {e}")
            return "unknown"

    def get_endpoint_name(self, scope, request):
        try:
            path = scope["path"]
            # Replace path parameters with their names
            for key, value in request.path_params.items():
                path = path.replace(value, f":{key}")

            path = path[:-1] if path.endswith("/") else path
            return path.lower()
        except KeyError:
            return "unknown"
        except Exception as e:
            logging.warning(f"Failed to get endpoint name: {e}")
            return "unknown"

    def get_status_code(self, response):
        try:
            return response.status_code
        except Exception as e:
            logging.warning(f"Failed to get status code: {e}")
            return 500

    def get_success(self, response):
        try:
            return 200 <= response.status_code < 400
        except Exception as e:
            logging.warning(f"Failed to get success: {e}")
            return False

    def get_user_id(self, request):
        try:
            user_id = request.headers.get("User-Id", None)

            if not user_id:
                user_id = (
                    request.state.user.id
                    if hasattr(request.state, "user") and request.state.user
                    else None
                )

            return user_id
        except Exception as e:
            logging.warning(f"Failed to get user id: {e}")
            return None

    def get_user(self, request):
        if not hasattr(request.state, "user") or not request.state.user:
            return None

        try:
            return {
                "id": request.state.user.id,
                "fullname": request.state.user.fullname,
                "email": request.state.user.email,
            }
        except Exception as e:
            logging.warning(f"Failed to get user: {e}")
            return None

    def get_object_ids(self, request):
        object_ids = {}
        try:
            for key, value in request.path_params.items():
                object_ids[key] = value

            for key, value in request.query_params.items():
                object_ids[key] = value

            return object_ids
        except Exception as e:
            logging.warning(f"Failed to get object ids: {e}")
            return {}

    def get_agent(self, request):
        if not hasattr(request.state, "agent") or not request.state.agent:
            return None

        return {
            "id": request.state.agent.id,
            "version": request.state.agent.version,
            "name": request.state.agent.name,
            "temperature": request.state.agent.temperature,
            "model": request.state.agent.model,
            "deployment": request.state.agent.deployment,
            "description": request.state.agent.description,
            "preamble": request.state.agent.preamble,
            "tools": request.state.agent.tools,
        }


def hash_string(s):
    if s is None:
        return None

    return hashlib.sha256(s.encode()).hexdigest().lower()


async def report_metrics(data):
    if not isinstance(data, dict):
        data = to_dict(data)

    data["secret"] = "secret"
    signal = {}
    signal["signal"] = data
    json_string = json.dumps(signal)
    # just general curl commands to test the endpoint for now
    print(
        f"\n\ncurl -X POST -H \"Content-Type: application/json\" -d '{json_string}' <ENDPOINT_HERE>\n\n"
    )

    if not REPORT_ENDPOINT:
        raise Exception("No report endpoint set")

    transport = AsyncHTTPTransport(retries=NUM_RETRIES)
    try:
        async with AsyncClient(transport=transport) as client:
            await client.post(REPORT_ENDPOINT, json=signal)
    except Exception as e:
        logging.error(f"Failed to report metrics: {e}")


def report_metrics_thread(data):
    if not REPORT_ENDPOINT:
        return

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(report_metrics(data))
        loop.close()
    except Exception as e:
        pass
