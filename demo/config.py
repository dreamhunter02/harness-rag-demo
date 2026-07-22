from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", ROOT / ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    harness1_base_url: str = "http://127.0.0.1:8001/v1"
    harness1_model: str = "harness-1"
    harness1_timeout_seconds: int = 900
    harness1_max_turns: int = 40
    openai_api_key: str | None = None
    openai_frontier_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    brev_instance_name: str | None = None
    brev_hourly_usd: float = 0
    demo_mode: str = "live"
    demo_data_dir: Path = ROOT / "data"
    demo_replay_dir: Path = ROOT / "fixtures" / "replays"
    run_timeout_seconds: int = 180

    @property
    def corpus_dir(self) -> Path:
        return self.demo_data_dir / "corpus"

    @property
    def chroma_dir(self) -> Path:
        return self.demo_data_dir / "chroma"


settings = Settings()
