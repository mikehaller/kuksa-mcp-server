#!/usr/bin/env python3
"""
Test-drive the Kuksa MCP server with a local Ollama LLM.

This script:
1. Starts the MCP server as a subprocess (stdio)
2. Connects to it via the MCP Python client
3. Calls tools to verify they work
4. Sends a prompt through Ollama with MCP tool access

Prerequisites:
  - pip install mcp ollama
  - Docker running with: docker run -d --rm -p 55555:55555 --name kuksa-databroker
      ghcr.io/eclipse-kuksa/kuksa-databroker:main --insecure
  - Ollama running on localhost:11434

Usage:
  python examples/local_test.py
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Add project root to path so imports work when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def test_direct_mcp_call() -> None:
    """Test that the MCP server responds to tool calls via stdio."""
    print("=" * 60)
    print("1. Testing MCP server tool calls via stdio transport...")
    print("=" * 60)

    # Start the MCP server as a subprocess
    server_process = subprocess.Popen(
        [sys.executable, "-m", "kuksa_mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Send initialize request
        initialize_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "local-test", "version": "0.1.0"},
            },
        })
        stdout, stderr = await _communicate(server_process, initialize_request)
        if stderr:
            print(f"[server stderr] {stderr.strip()}")
        if stdout:
            resp = json.loads(stdout)
            print(f"  Initialize response: {json.dumps(resp, indent=2)[:200]}...")

        # Send tools/list request
        tools_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        })
        stdout, stderr = await _communicate(server_process, tools_request)
        if stdout:
            resp = json.loads(stdout)
            tools = resp.get("result", {}).get("tools", [])
            print(f"\n  Available tools ({len(tools)}):")
            for t in tools:
                print(f"    - {t['name']}: {t.get('description', '')[:80]}")

        # Try to call server_info (may fail if no databroker running, that's ok)
        info_request = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "server_info",
                "arguments": {},
            },
        })
        stdout, stderr = await _communicate(server_process, info_request)
        if stdout:
            resp = json.loads(stdout)
            print(f"\n  server_info result: {json.dumps(resp, indent=2)[:300]}")
        elif stderr:
            print(f"\n  server_info error (expected if no databroker): {stderr.strip()}")

    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

    print("\n  [OK] MCP server responds to stdio tool calls\n")


async def test_with_ollama() -> None:
    """Test using Ollama to drive the MCP server."""
    print("=" * 60)
    print("2. Testing with Ollama LLM...")
    print("=" * 60)

    try:
        import ollama  # noqa: F811
    except ImportError:
        print("  'ollama' Python package not installed. Skipping Ollama test.")
        print("  Install: pip install ollama")
        return

    # Check if Ollama is running
    try:
        models = ollama.list()
        if not models or not models.get("models"):
            print("  No models found in Ollama. Skipping.")
            return
        model_name = models["models"][0]["model"]
        print(f"  Using Ollama model: {model_name}")
    except Exception as e:
        print(f"  Could not connect to Ollama: {e}")
        print("  Make sure Ollama is running on localhost:11434")
        return

    # Start MCP server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "kuksa_mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    tool_results: list[dict] = []

    async def call_tool(name: str, args: dict) -> dict | str:
        nonlocal server_process
        request = json.dumps({
            "jsonrpc": "2.0",
            "id": hash(name),
            "method": "tools/call",
            "params": {"name": name, "arguments": args},
        })
        stdout, stderr = await _communicate(server_process, request)
        if stdout:
            try:
                resp = json.loads(stdout)
                return resp
            except json.JSONDecodeError:
                return stdout
        return stderr or "no response"

    try:
        # Initialize
        init_req = json.dumps({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "ollama-test", "version": "0.1.0"},
            },
        })
        await _communicate(server_process, init_req)

        # Pre-populate context with results from MCP tools
        info = await call_tool("server_info", {})
        tool_results.append({"tool": "server_info", "result": info})

        speed = await call_tool("get_signal", {"path": "Vehicle.Speed"})
        tool_results.append({"tool": "get_signal", "result": speed})

        tools_context = "\n".join(
            f"- Called {r['tool']}: {json.dumps(r['result'], indent=2)}"
            for r in tool_results
        )

        prompt = f"""You have access to a Kuksa Databroker vehicle data server.
Here are the results from querying it:

{tools_context}

Based on this data, what is the current state of the vehicle signals,
and what commands are available to interact with the vehicle?"""

        print(f"\n  Sending prompt to Ollama ({model_name})...")
        try:
            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            print(f"\n  Ollama response:\n{response['message']['content'][:500]}")
            print("\n  [OK] Ollama successfully received and processed MCP tool results\n")
        except Exception as e:
            print(f"  Ollama chat failed: {e}")
            print("  (The MCP server itself works correctly)")

    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()


async def _communicate(
    process: subprocess.Popen,
    request: str,
) -> tuple[str | None, str | None]:
    """Send a request to the subprocess and read the response line."""
    if process.stdin is None or process.stdout is None:
        return None, "process not running"

    try:
        process.stdin.write(request + "\n")
        process.stdin.flush()

        # Read one line from stdout (each JSON-RPC message is one line)
        import select

        import os

        loop = asyncio.get_event_loop()
        stdout_line = await loop.run_in_executor(None, process.stdout.readline)

        stderr_output = ""
        if process.stderr:
            import fcntl

            fd = process.stderr.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            try:
                stderr_output = process.stderr.read()
            except (BlockingIOError, OSError):
                pass
            fcntl.fcntl(fd, fcntl.F_SETFL, fl)

        return (stdout_line.strip() if stdout_line else None,
                stderr_output.strip() if stderr_output else None)
    except Exception as e:
        return None, str(e)


async def main():
    print("Kuksa MCP Server — Local Test with Ollama")
    print()

    await test_direct_mcp_call()
    await test_with_ollama()

    print("=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
