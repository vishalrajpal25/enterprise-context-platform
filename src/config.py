from pydantic_settings import BaseSettings
from enum import Enum


class ResolutionMode(str, Enum):
    ORCHESTRATOR = "orchestrator"   # Rule-based, deterministic, production-ready
    INTELLIGENT = "intelligent"     # Neuro-symbolic, experimental


class Settings(BaseSettings):
    # Resolution engine
    resolution_mode: ResolutionMode = ResolutionMode.ORCHESTRATOR
    llm_provider: str = "anthropic"  # "anthropic" or "openai"
    # Anthropic Haiku 4.5 — fast, cheap, sufficient for intent parsing.
    # Override with ECP_LLM_MODEL=claude-sonnet-4-6 for harder reasoning.
    llm_model: str = "claude-haiku-4-5-20251001"

    # Embeddings — provider-flexible. Defaults to Voyage (free tier, no card,
    # Anthropic's recommended embeddings partner). Switch to OpenAI by setting
    # ECP_EMBEDDING_PROVIDER=openai. Set to "none" to force the ILIKE fallback.
    # The active dimension MUST match what init_db.py creates the vector
    # columns with — both read settings.embedding_dim, so a single env var
    # change is all that's needed to swap providers cleanly.
    embedding_provider: str = "voyage"   # "voyage" | "openai" | "none"
    embedding_model: str = ""            # auto-picked from provider if empty
    embedding_dim: int = 512             # voyage-3-lite default; OpenAI text-embedding-3-small=1536

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "ecp_local_dev"

    # PostgreSQL
    postgres_dsn: str = "postgresql://ecp:ecp_local_dev@localhost:5432/ecp"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Vector store
    vector_backend: str = "pgvector"

    # Semantic layer (Cube.js REST)
    cube_api_url: str = ""
    cube_api_secret: str = ""

    # API security
    api_key: str = ""  # when set, every API request must include x-ecp-api-key

    # Search: when True, anonymous users receive empty search results (stricter OSS/prod posture)
    search_require_identity: bool = True

    # Anthropic (intent parsing in intelligent mode)
    anthropic_api_key: str = ""

    # Embedding provider keys — at least one must be set for real cosine
    # retrieval; otherwise the system logs a startup warning and falls
    # back to ILIKE text search transparently.
    voyage_api_key: str = ""
    openai_api_key: str = ""

    # Demo mode banner — public, non-prod deployments set this to true.
    # When true, startup logs a clear "DEMO MODE" banner and the /health endpoint
    # advertises demo_mode=true so visitors and crawlers cannot mistake the
    # public sandbox for a production security boundary.
    demo_mode: bool = False

    class Config:
        env_prefix = "ECP_"
        env_file = ".env"


settings = Settings()
