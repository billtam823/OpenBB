# OpenBB API Key Auth Extension

Per-client API key authentication for the OpenBB Platform API. Validates the
`x-api-key` header against keys configured in `OPENBB_API_KEYS` (JSON object of
`{client: key}`) or `OPENBB_API_KEYS_FILE`. Enable with `OPENBB_API_AUTH=true`
and `OPENBB_API_AUTH_EXTENSION=apikey_auth`.
