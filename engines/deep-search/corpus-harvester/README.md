# Corpus Harvester Runtime

Phase 4 operational hardening adds a file-based configuration layer,
request throttling, and explicit environment variable documentation.

## Runtime config

Default config path:

- `engines/deep-search/corpus-harvester/harvest.config.json`

Override with:

- `HARVEST_CONFIG_PATH=/absolute/or/relative/path/to/config.json`

## Required environment variables

- `BRAVE_API_KEY` — Brave Search API key.

Optional:

- `BRAVE_API_KEY_ENV_VAR` — env-var name that holds the Brave key.
  Defaults to `BRAVE_API_KEY`.

## Rate limits (configured in `harvest.config.json`)

- `rateLimits.braveRequestsPerMinute`
- `rateLimits.articleFetchMaxConcurrent`
- `rateLimits.articleFetchPerDomainCooldownMs`

## Security notes

- Keep secrets in `.env` locally.
- `.env` is gitignored.
- `.env.example` provides placeholders only.
