from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response

DEMO_USERS: dict[str, str] = {
    "demo.approver": "Approver",
    "demo.admin": "Admin",
}


@dataclass(frozen=True)
class UserSession:
    username: str
    role: str


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, UserSession] = {}

    def create(self, session: UserSession) -> str:
        token = secrets.token_hex(16)
        self._sessions[token] = session
        return token

    def get(self, token: str | None) -> UserSession | None:
        if token is None:
            return None
        return self._sessions.get(token)

    def remove(self, token: str | None) -> None:
        if token is not None:
            self._sessions.pop(token, None)


async def get_session_from_request(request: Request) -> UserSession:
    session = getattr(request.state, "session", None)
    if session is None:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    return session


def require_role(*allowed_roles: str):
    async def dependency(request: Request) -> UserSession:
        session = getattr(request.state, "session", None)
        if session is None:
            raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
        if session.role not in allowed_roles:
            raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
        return session

    return dependency


auth_router = APIRouter(prefix="/api/auth")


@auth_router.post("/login")
async def login(request: Request) -> dict:
    payload = await request.json()
    username = payload.get("username")
    password = payload.get("password")
    demo_user = DEMO_USERS.get(username)

    if username == "demo.approver" and password == "ChangeMe123!":
        role = "Approver"
    elif username == "demo.admin" and password == "ChangeMe123!":
        role = "Admin"
    else:
        return JSONResponse(status_code=401, content={"error": "Invalid username or password."})

    token = request.app.state.session_store.create(UserSession(username=username, role=role))
    return {"token": token, "username": username, "role": role}


@auth_router.post("/logout")
async def logout(request: Request) -> Response:
    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        request.app.state.session_store.remove(token)
    return Response(status_code=204)
