from pydantic_settings import BaseSettings, SettingsConfigDict


class KuksaConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KUKSA_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    host: str = "127.0.0.1"
    port: int = 55555
    token: str | None = None

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"
