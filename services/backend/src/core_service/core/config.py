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
    # 포트 기본값은 표준(5432 등)이 아니라 이 개발 머신에서 Docker에 열 수 있는
    # 범위(9670-9680)에 맞춘 infra/docker-compose.yml 매핑과 짝을 이룬다.
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=9670, alias="DB_PORT")
    db_name: str = Field(default="silveryarn", alias="DB_NAME")
    db_user: str = Field(default="silveryarn", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")

    # --- STORAGE_ (MinIO) ---
    storage_endpoint: str = Field(default="localhost:9675", alias="STORAGE_ENDPOINT")
    storage_access_key: str = Field(default="", alias="STORAGE_ACCESS_KEY")
    storage_secret_key: str = Field(default="", alias="STORAGE_SECRET_KEY")
    storage_bucket_photos: str = Field(default="silveryarn-photos", alias="STORAGE_BUCKET_PHOTOS")
    storage_secure: bool = Field(default=False, alias="STORAGE_SECURE")

    # --- VECTORDB_ (Qdrant) ---
    vectordb_host: str = Field(default="localhost", alias="VECTORDB_HOST")
    vectordb_port: int = Field(default=9672, alias="VECTORDB_PORT")
    vectordb_api_key: str | None = Field(default=None, alias="VECTORDB_API_KEY")

    # --- GRAPH_ (Neo4j) ---
    graph_uri: str = Field(default="bolt://localhost:9674", alias="GRAPH_URI")
    graph_user: str = Field(default="neo4j", alias="GRAPH_USER")
    graph_password: str = Field(default="", alias="GRAPH_PASSWORD")

    # --- STT_ (Whisper Large-v3, 온프레미스) ---
    stt_endpoint: str = Field(default="http://localhost:9001", alias="STT_ENDPOINT")

    # --- EMBEDDING_ (BGE-M3) ---
    embedding_endpoint: str = Field(default="http://localhost:9002", alias="EMBEDDING_ENDPOINT")

    # --- LLM_ (vLLM) ---
    llm_endpoint: str = Field(default="http://localhost:8001/v1", alias="LLM_ENDPOINT")
    llm_model_name: str = Field(default="", alias="LLM_MODEL_NAME")

    # --- AUTH_ (Keycloak SSO, decisions.md #17 / #47) ---
    auth_issuer_url: str = Field(default="", alias="AUTH_ISSUER_URL")
    auth_client_id: str = Field(default="silveryarn-backend", alias="AUTH_CLIENT_ID")
    auth_secret: str = Field(default="", alias="AUTH_SECRET")
    # 토큰 audience 검증값. 비우면 client_id를 쓴다.
    auth_audience: str = Field(default="", alias="AUTH_AUDIENCE")
    # JWKS 엔드포인트. 비우면 issuer_url에서 표준 경로로 유도한다.
    auth_jwks_url: str = Field(default="", alias="AUTH_JWKS_URL")
    auth_jwks_cache_seconds: int = Field(default=600, alias="AUTH_JWKS_CACHE_SECONDS")
    # 2FA(step-up)로 인정할 토큰 `amr` claim 값들(콤마 구분). Keycloak 인증흐름 설정에 맞춘다.
    auth_2fa_amr_values_raw: str = Field(default="mfa,otp,hwk", alias="AUTH_2FA_AMR_VALUES")

    @property
    def resolved_jwks_url(self) -> str:
        if self.auth_jwks_url:
            return self.auth_jwks_url
        return f"{self.auth_issuer_url.rstrip('/')}/protocol/openid-connect/certs"

    @property
    def resolved_audience(self) -> str:
        return self.auth_audience or self.auth_client_id

    @property
    def auth_2fa_amr_values(self) -> set[str]:
        return {v.strip() for v in self.auth_2fa_amr_values_raw.split(",") if v.strip()}

    # --- SYNC_ (배치 동기화, sync-contract.md) ---
    sync_max_retry: int = Field(default=5, alias="SYNC_MAX_RETRY")
    sync_checksum_algo: str = Field(default="sha256", alias="SYNC_CHECKSUM_ALGO")

    # --- PII_ (애플리케이션 레벨 필드 암호화 — schema.md §5, decisions.md #45, CTO 검토 B4) ---
    # KEK(Key Encryption Key): Fernet 키 문자열. 회전 대비로 콤마 구분 다중 키 허용
    # (첫 키로 암호화, 전체 키로 복호화 시도 — MultiFernet). 온프레미스 Vault 이전 전까지
    # 시크릿 매니저/환경변수로 주입한다(CONVENTIONS.md §4). 비어 있으면 PII 대상
    # repository가 처음 호출될 때 RuntimeError(생성 방법 안내 포함).
    pii_kek: str = Field(default="", alias="PII_KEK")

    # blind index(동등검색용 HMAC, `contact_bidx` 등) 전용 키 — decisions.md #60(2026-09-12).
    # PII_KEK와 같은 값에서 유도하던 이전 방식은 "하나 유출 시 둘 다 노출"되는 결함이라
    # 정식 분리했다. 비어 있으면 crypto.py가 하위호환을 위해 PII_KEK에서 유도(경고 로그).
    blind_index_key: str = Field(default="", alias="BLIND_INDEX_KEY")

    # --- Worker (arq, sync-contract.md §2) ---
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=9671, alias="REDIS_PORT")

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
