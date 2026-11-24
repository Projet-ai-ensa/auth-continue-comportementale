from typing import Annotated, Literal, Self

from fastapi import APIRouter, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from api.schemas import Count, Measurement

Identifier = Annotated[str, Field(min_length=1)]
SignedMeasurement = Annotated[float, Field(strict=True, allow_inf_nan=False)]
CollectionStatus = Literal["collected", "no_data"]


class KeyboardFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hold_count: Count
    hold_mean_ms: Measurement | None
    flight_count: Count
    flight_mean_ms: SignedMeasurement | None
    flight_min_ms: SignedMeasurement | None

    @model_validator(mode="after")
    def validate_statistics(self) -> Self:
        if (self.hold_mean_ms is None) != (self.hold_count == 0):
            raise ValueError("hold_mean_ms must be null exactly when hold_count is zero")

        flight_statistics = (self.flight_mean_ms, self.flight_min_ms)
        if any((value is None) != (self.flight_count == 0) for value in flight_statistics):
            raise ValueError("flight statistics must be null exactly when flight_count is zero")

        if self.flight_min_ms is not None and self.flight_mean_ms is not None:
            if self.flight_min_ms > self.flight_mean_ms:
                raise ValueError("flight_min_ms must not exceed flight_mean_ms")

        return self


class KeyboardQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hold_count: Count
    flight_count: Count
    expired_hold_count: Count
    incomplete_flight_count: Count
    status: CollectionStatus


class KeyboardObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["keyboard-proposal-1"]
    session_id: Identifier
    window_id: Identifier
    window_started_at: AwareDatetime
    window_duration_ms: Annotated[int, Field(strict=True, gt=0)]
    collector_version: Identifier
    keyboard_features: KeyboardFeatures
    quality: KeyboardQuality

    @field_validator("window_started_at", mode="before")
    @classmethod
    def require_timestamp_string(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("window_started_at must be a timestamp string")
        return value

    @model_validator(mode="after")
    def validate_quality(self) -> Self:
        features = self.keyboard_features
        quality = self.quality
        if (quality.hold_count, quality.flight_count) != (features.hold_count, features.flight_count):
            raise ValueError("quality counts must match keyboard feature counts")

        expected_status = "collected" if features.hold_count or features.flight_count else "no_data"
        if quality.status != expected_status:
            raise ValueError("quality status must reflect the available statistics")

        return self


class KeyboardAcknowledgment(BaseModel):
    status: Literal["validated"] = "validated"
    collection_status: CollectionStatus


class KeyboardValidationError(BaseModel):
    detail: Literal["Invalid keyboard observation."] = "Invalid keyboard observation."


class KeyboardRoute(APIRoute):
    def get_route_handler(self):
        route_handler = super().get_route_handler()

        async def handle(request: Request):
            try:
                return await route_handler(request)
            except RequestValidationError:
                # Validation errors can contain rejected values and unknown field names.
                return JSONResponse(status_code=422, content=KeyboardValidationError().model_dump())

        return handle


router = APIRouter(route_class=KeyboardRoute)


@router.post(
    "/v1/keyboard-observations",
    summary="Validate aggregate keyboard observations (provisional)",
    description="Local prototype. Validates the proposed payload without persistence or inference.",
    responses={422: {"model": KeyboardValidationError}},
)
def receive_keyboard_observation(observation: KeyboardObservation) -> KeyboardAcknowledgment:
    return KeyboardAcknowledgment(collection_status=observation.quality.status)
