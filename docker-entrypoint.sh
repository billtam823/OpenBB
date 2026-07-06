#!/bin/bash
# Run BOTH servers in one container:
#   - OpenBB REST API      on :6900  (x-api-key via apikey_auth)
#   - OpenBB MCP server     on :6901  (streamable-http)
# If either process exits, exit the container so Dokploy restarts it.

set -uo pipefail

# REST API. apikey_auth is honored via OPENBB_API_AUTH / OPENBB_API_KEYS env (set in Dokploy).
openbb-api --host 0.0.0.0 --port 6900 &
API_PID=$!

# MCP server. It proxies to an in-process copy of the OpenBB app; if apikey_auth were on,
# those internal calls would 401 — so force OPENBB_API_AUTH=false for THIS process only.
# The x-api-key gate protects the REST door (6900). Protect the MCP door (6901) by setting
# OPENBB_MCP_SERVER_AUTH='["user","pass"]' in Dokploy (clients send Bearer base64(user:pass)).
# --default-categories / --tool-discovery keep the exposed tool list small (no token bloat).
OPENBB_API_AUTH=false openbb-mcp \
    --transport streamable-http --host 0.0.0.0 --port 6901 \
    --default-categories equity --tool-discovery &
MCP_PID=$!

# Wait for whichever exits first, then bring the container down for a clean restart.
wait -n
echo "[entrypoint] a server process exited — stopping container for restart." >&2
kill "$API_PID" "$MCP_PID" 2>/dev/null || true
exit 1
