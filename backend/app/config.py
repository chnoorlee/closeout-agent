from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Closeout"
    environment: Literal["development", "test", "production"] = "development"
    model: str = Field(default="gemini-3.5-flash", alias="CLOSEOUT_MODEL")
    store: Literal["auto", "memory", "firestore"] = Field(default="auto", alias="CLOSEOUT_STORE")
    dispatcher: Literal["auto", "local", "cloud-tasks"] = Field(
        default="auto", alias="CLOSEOUT_DISPATCHER"
    )
    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="global", alias="GOOGLE_CLOUD_LOCATION")
    use_vertex_ai: bool = Field(default=False, alias="GOOGLE_GENAI_USE_VERTEXAI")
    tasks_queue: str = Field(default="closeout-runs", alias="CLOSEOUT_TASKS_QUEUE")
    tasks_location: str = Field(default="us-central1", alias="CLOSEOUT_TASKS_LOCATION")
    service_url: str | None = Field(default=None, alias="CLOSEOUT_SERVICE_URL")
    task_service_account: str | None = Field(default=None, alias="CLOSEOUT_TASK_SERVICE_ACCOUNT")
    task_secret: str | None = Field(default=None, alias="CLOSEOUT_TASK_SECRET")
    demo_mode: bool = Field(default=True, alias="CLOSEOUT_DEMO_MODE")
    stage_delay_ms: int = Field(default=450, alias="CLOSEOUT_STAGE_DELAY_MS", ge=0, le=5000)

    @property
    def has_live_ai_config(self) -> bool:
        import os

        return bool(
            os.getenv("GOOGLE_API_KEY") or (self.use_vertex_ai and self.google_cloud_project)
        )

    @property
    def cloud_runtime_evidence(self) -> tuple[str, str] | None:
        import os

        service = os.getenv("K_SERVICE")
        revision = os.getenv("K_REVISION")
        if service and revision:
            return service, revision
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
