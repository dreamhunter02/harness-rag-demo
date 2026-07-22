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
    harness1_timeout_seconds: int = 90
    harness1_max_turns: int = 12
    harness1_max_generation_tokens: int = 768
    retrieval_result_limit: int = 5
    curated_document_limit: int = 12
    openai_api_key: str | None = None
    frontier_api_key: str | None = None
    frontier_base_url: str = "https://api.openai.com/v1"
    openai_frontier_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str | None = None
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_concurrency: int = 4
    harness1_remote_host: str = "teamdgxa100"
    harness1_hourly_usd: float = 0
    pricing_effective_date: str = "2026-07-21"
    frontier_input_per_million_usd: float = 0.15
    frontier_output_per_million_usd: float = 0.60
    demo_mode: str = "live"
    demo_data_dir: Path = ROOT / "data"
    demo_replay_dir: Path = ROOT / "fixtures" / "replays"
    run_timeout_seconds: int = 300

    @property
    def corpus_dir(self) -> Path:
        return self.demo_data_dir / "corpus"

    @property
    def chroma_dir(self) -> Path:
        return self.demo_data_dir / "chroma"

    @property
    def resolved_embedding_api_key(self) -> str | None:
        return self.embedding_api_key or self.openai_api_key

    @property
    def resolved_frontier_api_key(self) -> str | None:
        return self.frontier_api_key or self.openai_api_key


settings = Settings()
