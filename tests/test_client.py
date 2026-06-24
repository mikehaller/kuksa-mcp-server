from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kuksa_client.grpc import DataType, EntryType, Metadata as KuksaMetadata

from kuksa_mcp_server.client import KuksaDatabrokerClient, KuksaDatabrokerError
from kuksa_mcp_server.config import KuksaConfig


@pytest.fixture
def config():
    return KuksaConfig(host="127.0.0.1", port=55555)


@pytest.fixture
def mock_vss():
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    return client


@pytest.fixture
async def client(config, mock_vss):
    with patch("kuksa_mcp_server.client.VSSClient", return_value=mock_vss):
        c = KuksaDatabrokerClient(config)
        await c.connect()
        yield c
        await c.disconnect()


def _make_dp(value, ts=None):
    dp = MagicMock()
    dp.value = value
    dp.timestamp = ts
    return dp


@pytest.mark.asyncio
async def test_connect(mock_vss, client):
    mock_vss.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect(mock_vss, client):
    await client.disconnect()
    mock_vss.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_value_found(client, mock_vss):
    mock_vss.get_current_values = AsyncMock(
        return_value={"Vehicle.Speed": _make_dp(42.0)},
    )
    result = await client.get_value("Vehicle.Speed")
    assert result["path"] == "Vehicle.Speed"
    assert result["value"] == 42.0


@pytest.mark.asyncio
async def test_get_value_not_found(client, mock_vss):
    mock_vss.get_current_values = AsyncMock(return_value={})
    with pytest.raises(KuksaDatabrokerError, match="not found"):
        await client.get_value("Vehicle.Nonexistent")


@pytest.mark.asyncio
async def test_get_values(client, mock_vss):
    mock_vss.get_current_values = AsyncMock(
        return_value={
            "Vehicle.Speed": _make_dp(50.0),
            "Vehicle.Cabin.Door.Row1.Left.IsOpen": _make_dp(True),
        },
    )
    results = await client.get_values([
        "Vehicle.Speed",
        "Vehicle.Cabin.Door.Row1.Left.IsOpen",
    ])
    assert len(results) == 2
    assert results[0]["path"] == "Vehicle.Speed"
    assert results[1]["path"] == "Vehicle.Cabin.Door.Row1.Left.IsOpen"


@pytest.mark.asyncio
async def test_set_value(client, mock_vss):
    mock_vss.set_target_values = AsyncMock(return_value=None)
    result = await client.set_value("Vehicle.Speed", "100", "float")
    assert result["path"] == "Vehicle.Speed"
    assert result["status"] == "set"


@pytest.mark.asyncio
async def test_list_signals(client, mock_vss):
    meta_1 = KuksaMetadata(
        data_type=DataType.STRING,
        entry_type=EntryType.SENSOR,
        description="Vehicle speed",
        unit="km/h",
    )
    meta_2 = KuksaMetadata(
        data_type=DataType.BOOLEAN,
        entry_type=EntryType.SENSOR,
        description="Door open state",
        unit="",
    )
    mock_vss.get_metadata = AsyncMock(
        return_value={
            "Vehicle.Speed": meta_1,
            "Vehicle.Cabin.Door.Row1.Left.IsOpen": meta_2,
        },
    )
    results = await client.list_signals("Vehicle")
    assert len(results) >= 2


@pytest.mark.asyncio
async def test_get_server_info(client):
    info = await client.get_server_info()
    assert info["name"] == "Kuksa Databroker"
    assert "127.0.0.1" in info["address"]


@pytest.mark.asyncio
async def test_double_connect_is_noop(client):
    await client.connect()
    assert True


@pytest.mark.asyncio
async def test_method_before_connect_raises():
    c = KuksaDatabrokerClient(
        KuksaConfig(host="127.0.0.1", port=55555),
    )
    with pytest.raises(KuksaDatabrokerError, match="Not connected"):
        await c.get_value("Vehicle.Speed")
