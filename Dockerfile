FROM python:3.12-slim-bookworm

WORKDIR /app

# Install openbb + all providers, the REST API server, and the MCP server from PyPI.
# Remove openbb-cftc: its startup hook (build_choices) crashes the whole app when the
# live CFTC data contains a null subcategory ("'NoneType' object has no attribute 'strip'").
# We don't use CFTC commitment-of-traders data, so drop the provider to keep startup healthy.
RUN pip install --no-cache-dir "openbb[all]" openbb-platform-api openbb-mcp-server && \
    pip uninstall -y openbb-cftc

# Copy and reinstall locally modified packages to override PyPI versions
COPY openbb_platform/core/ ./openbb_platform/core/
COPY openbb_platform/providers/federal_reserve/ ./openbb_platform/providers/federal_reserve/
COPY openbb_platform/extensions/apikey_auth/ ./openbb_platform/extensions/apikey_auth/

RUN pip install --no-cache-dir --no-deps ./openbb_platform/core/ && \
    pip install --no-cache-dir --no-deps ./openbb_platform/providers/federal_reserve/ && \
    pip install --no-cache-dir --no-deps ./openbb_platform/extensions/apikey_auth/

# Entrypoint runs BOTH servers: REST API on 6900, MCP on 6901.
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 6900 = REST API (x-api-key via apikey_auth); 6901 = MCP server (streamable-http)
EXPOSE 6900 6901

ENTRYPOINT ["/app/docker-entrypoint.sh"]
