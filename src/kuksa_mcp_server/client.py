from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from kuksa_client.grpc import Datapoint as KuksaDatapoint
from kuksa_client.grpc.aio import VSSClient

from .config import KuksaConfig


class KuksaDatabrokerError(Exception):
    """Raised when the databroker returns an error."""


def _datapoint_to_dict(dp: KuksaDatapoint) -> dict[str, Any]:
    return {
        "timestamp": dp.timestamp.isoformat() if dp.timestamp else None,
        "value": dp.value,
    }


class KuksaDatabrokerClient:
    """Async wrapper around kuksa-client's VSSClient."""

    def __init__(self, config: KuksaConfig) -> None:
        self._config = config
        self._client: VSSClient | None = None

    async def connect(self) -> None:
        if self._client is not None:
            return
        self._client = VSSClient(
            self._config.host,
            self._config.port,
            token=self._config.token,
        )
        await self._client.connect()

    async def disconnect(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.disconnect()
        finally:
            self._client = None

    async def get_value(self, path: str) -> dict[str, Any]:
        raw = await self._ensure_client().get_current_values([path])
        entry = raw.get(path)
        if entry is None:
            raise KuksaDatabrokerError(f"Signal '{path}' not found")
        return {
            "path": path,
            **_datapoint_to_dict(entry),
        }

    async def get_values(self, paths: list[str]) -> list[dict[str, Any]]:
        raw = await self._ensure_client().get_current_values(paths)
        result: list[dict[str, Any]] = []
        for path in paths:
            entry = raw.get(path)
            if entry is not None:
                result.append({
                    "path": path,
                    **_datapoint_to_dict(entry),
                })
        return result

    async def set_value(self, path: str, value: Any, datatype: str = "string") -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        dp = KuksaDatapoint(value, now)
        await self._ensure_client().set_target_values({path: dp})
        return {"path": path, "value": value, "datatype": datatype, "status": "set"}

    async def list_signals(self, branch: str = "Vehicle") -> list[dict[str, Any]]:
        raw = await self._ensure_client().get_metadata([branch])
        results: list[dict[str, Any]] = []
        for path, meta in raw.items():
            results.append({
                "path": path,
                "data_type": str(meta.data_type) if meta.data_type else None,
                "entry_type": str(meta.entry_type) if meta.entry_type else None,
                "description": meta.description or "",
                "unit": meta.unit or "",
            })
        return results

    async def get_server_info(self) -> dict[str, Any]:
        _ = self._ensure_client()
        return {
            "name": "Kuksa Databroker",
            "address": self._config.address,
        }

    def _ensure_client(self) -> VSSClient:
        if self._client is None:
            raise KuksaDatabrokerError("Not connected to databroker")
        return self._client


@asynccontextmanager
async def create_client(config: KuksaConfig) -> AsyncIterator[KuksaDatabrokerClient]:
    client = KuksaDatabrokerClient(config)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()
