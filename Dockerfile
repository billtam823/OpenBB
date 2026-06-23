FROM python:3.12-slim-bookworm

WORKDIR /app

# Install openbb and all standard providers from PyPI
RUN pip install --no-cache-dir "openbb[all]" openbb-platform-api

# Copy and reinstall locally modified packages to override PyPI versions
COPY openbb_platform/core/ ./openbb_platform/core/
COPY openbb_platform/providers/federal_reserve/ ./openbb_platform/providers/federal_reserve/
COPY openbb_platform/extensions/apikey_auth/ ./openbb_platform/extensions/apikey_auth/

RUN pip install --no-cache-dir --no-deps ./openbb_platform/core/ && \
    pip install --no-cache-dir --no-deps ./openbb_platform/providers/federal_reserve/ && \
    pip install --no-cache-dir --no-deps ./openbb_platform/extensions/apikey_auth/

EXPOSE 6900

ENTRYPOINT ["openbb-api", "--host", "0.0.0.0", "--port", "6900"]
