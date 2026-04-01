from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class PullRequest(BaseModel):
    image: str = Field(min_length=1)


class RunRequest(BaseModel):
    image: str = Field(min_length=1)
    command: list[str] | None = None
    env: list[str] | None = None


class ComposeUpRequest(BaseModel):
    compose_yaml: str = Field(min_length=1)


class CheckoutRequest(BaseModel):
    return_url: str | None = None
