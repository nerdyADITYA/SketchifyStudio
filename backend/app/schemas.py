from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "sketchify-studio-api"


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class StyleOptions(BaseModel):
    """Optional style customisation. Sliders are 0-100 (50 default); colour mode is grayscale or color."""

    model_config = ConfigDict(extra="forbid", strict=True)

    intensity: int = Field(50, ge=0, le=100)
    line_thickness: int = Field(50, ge=0, le=100)
    contrast: int = Field(50, ge=0, le=100)
    detail: int = Field(50, ge=0, le=100)
    shading: int = Field(50, ge=0, le=100)
    color_mode: Literal["grayscale", "color"] = "grayscale"
    color_strength: int = Field(100, ge=0, le=100)
