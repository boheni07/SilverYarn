"""환경변수 로딩 — CONVENTIONS.md §4 접두사 규칙을 그대로 따른다.

접두사별 담당 영역: DB_ / STORAGE_(MinIO) / VECTORDB_(Qdrant) / GRAPH_(Neo4j) /
STT_(Whisper) / EMBEDDING_(BGE-M3) / LLM_(vLLM) / AUTH_(Keycloak) / SYNC_(동기화 파라미터)

⚠️ 온프레미스 시크릿(DB/Storage/LLM/VectorDB 접속정보)은 .env 파일 평문 커밋 금지
   (CONVENTIONS.md §4 보안 원칙) — .env.local은 .gitignore 처리됨.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.local", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "silveryarn-core-service"
    api_prefix: str = "/api/v1"
    debug: bool = False

    # --- DB_ (PostgreSQL) ---
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="silveryarn", alias="DB_NAME")
    db_user: str = Field(default="silveryarn", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")

    # --- STORAGE_ (MinIO) ---
    storage_endpoint: str = Field(default="localhost:9000", alias="STORAGE_ENDPOINT")
    storage_access_key: str = Field(default="", alias="STORAGE_ACCESS_KEY")
    storage_secret_key: str = Field(default="", alias="STORAGE_SECRET_KEY")
    storage_bucket_photos: str = Field(default="silveryarn-photos", alias="STORAGE_BUCKET_PHOTOS")
    storage_secure: bool = Field(default=False, alias="STORAGE_SECURE")

    # --- VECTORDB_ (Qdrant) ---
    vectordb_host: str = Field(default="localhost", alias="VECTORDB_HOST")
    vectordb_port: int = Field(default=6333, alias="VECTORDB_PORT")
    vectordb_api_key: str | None = Field(default=None, alias="VECTORDB_API_KEY")

    # --- GRAPH_ (Neo4j) ---
    graph_uri: str = Field(default="bolt://localhost:7687", alias="GRAPH_URI")
    graph_user: str = Field(default="neo4j", alias="GRAPH_USER")
    graph_password: str = Field(default="", alias="GRAPH_PASSWORD")

    # --- STT_ (Whisper Large-v3, 온프레미스) ---
    stt_endpoint: str = Field(default="http://localhost:9001", alias="STT_ENDPOINT")

    # --- EMBEDDING_ (BGE-M3) ---
    embedding_endpoint: str = Field(default="http://localhost:9002", alias="EMBEDDING_ENDPOINT")

    # --- LLM_ (vLLM) ---
    llm_endpoint: str = Field(default="http://localhost:8001/v1", alias="LLM_ENDPOINT")
    llm_model_name: str = Field(default="", alias="LLM_MODEL_NAME")

    # --- AUTH_ (Keycloak SSO, decisions.md #17) ---
    auth_issuer_url: str = Field(default="", alias="AUTH_ISSUER_URL")
    auth_client_id: str = Field(default="silveryarn-backend", alias="AUTH_CLIENT_ID")
    auth_secret: str = Field(default="", alias="AUTH_SECRET")

    # --- SYNC_ (배치 동기화, sync-contract.md) ---
    sync_max_retry: int = Field(default=5, alias="SYNC_MAX_RETRY")
    sync_checksum_algo: str = Field(default="sha256", alias="SYNC_CHECKSUM_ALGO")

    # --- Worker (arq, sync-contract.md §2) ---
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    # --- CORS (apps/web 브라우저 요청 허용) ---
    # ⚠️ Server Component의 fetch는 Node 프로세스에서 실행돼 CORS 대상이 아니지만,
    # "use client" 컴포넌트의 fetch는 브라우저에서 직접 나간다 — CORSMiddleware가
    # 없으면 그 요청만 조용히 "Failed to fetch"로 실패한다(에러 응답조차 못 받음).
    # apps/web 실제 e2e 테스트 중(리뷰 화면 승인 버튼) 발견하고 추가했다.
    cors_allowed_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ALLOWED_ORIGINS"
    )

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins_raw.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        """SQLAlchemy async DSN (asyncpg 드라이버)."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
