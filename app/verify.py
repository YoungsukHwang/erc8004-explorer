"""Cross-check every headline number the dashboard claims.

Each section runs two or more independent paths to the same number. Any mismatch
or surprise is flagged inline. Run with:

    python verify.py
"""
from __future__ import annotations

import pandas as pd

from bq import (
    run_query,
    LOGS,
    IDENTITY_REGISTRY,
    REPUTATION_REGISTRY,
    SIG_REGISTERED,
    SIG_NEW_FEEDBACK,
    PARTITION_CUT,
    IDENTITY_BASE_CTE,
    REPUTATION_BASE_CTE,
    INLINE_JSON_EXPR,
)

pd.set_option("display.max_colwidth", 80)
pd.set_option("display.width", 160)


def hdr(t):
    print(f"\n{'='*78}\n{t}\n{'='*78}")


# =============================================================================
# 1) Total Registered — does it really equal 34,566?
# =============================================================================
hdr("1) Total Registered events — three independent paths")

# Path A: our standard CTE
df = run_query(f"WITH {IDENTITY_BASE_CTE} SELECT COUNT(*) AS n FROM identity_base")
nA = int(df.iloc[0]["n"])
print(f"  A (IDENTITY_BASE_CTE, partition cut + sig filter): {nA:,}")

# Path B: raw count with no CTE, no decoding
df = run_query(f"""
SELECT COUNT(*) AS n
FROM {LOGS}
WHERE address = '{IDENTITY_REGISTRY}'
  AND topics[SAFE_OFFSET(0)] = '{SIG_REGISTERED}'
  AND block_timestamp >= {PARTITION_CUT}
""")
nB = int(df.iloc[0]["n"])
print(f"  B (raw logs, same filters):                       {nB:,}")

# Path C: drop partition cut entirely — is anything hiding before 2026-01-28?
df = run_query(f"""
SELECT COUNT(*) AS n,
       MIN(block_timestamp) AS first_event,
       MAX(block_timestamp) AS last_event
FROM {LOGS}
WHERE address = '{IDENTITY_REGISTRY}'
  AND topics[SAFE_OFFSET(0)] = '{SIG_REGISTERED}'
""")
print(f"  C (no partition cut):                             {int(df.iloc[0]['n']):,}")
print(f"      first_event = {df.iloc[0]['first_event']}")
print(f"      last_event  = {df.iloc[0]['last_event']}")

# Path D: distinct agent_id (handoff says no duplicate agent_id)
df = run_query(f"""
WITH {IDENTITY_BASE_CTE}
SELECT COUNT(DISTINCT agent_id) AS n_distinct,
       COUNT(*) AS n_rows,
       COUNTIF(agent_id IS NULL) AS n_null_agent_id
FROM identity_base
""")
print(f"  D distinct agent_id vs row count:")
print(f"      distinct agent_id = {int(df.iloc[0]['n_distinct']):,}")
print(f"      total rows        = {int(df.iloc[0]['n_rows']):,}")
print(f"      null agent_id     = {int(df.iloc[0]['n_null_agent_id']):,}")


# =============================================================================
# 2) URI scheme breakdown — does the sum equal 34,566?
# =============================================================================
hdr("2) URI scheme breakdown — must sum to Registered total")

df = run_query(f"""
WITH {IDENTITY_BASE_CTE}
SELECT
  CASE
    WHEN agent_uri IS NULL THEN 'NULL'
    WHEN agent_uri = '' THEN 'empty_string'
    WHEN STARTS_WITH(agent_uri, 'data:application/json;base64,') THEN 'inline_base64'
    WHEN STARTS_WITH(agent_uri, 'data:application/json') THEN 'inline_other'
    WHEN STARTS_WITH(agent_uri, 'data:') THEN 'data_other'
    WHEN STARTS_WITH(agent_uri, 'https://') THEN 'https'
    WHEN STARTS_WITH(agent_uri, 'http://') THEN 'http'
    WHEN STARTS_WITH(agent_uri, 'ipfs://') THEN 'ipfs'
    ELSE 'other'
  END AS scheme,
  COUNT(*) AS n
FROM identity_base
GROUP BY scheme
ORDER BY n DESC
""")
print(df.to_string(index=False))
print(f"  SUM = {df['n'].sum():,}  (expected {nA:,})")
print(f"  match: {df['n'].sum() == nA}")


# =============================================================================
# 3) inline_base64 = 9,520 — and how many actually decode to non-null JSON?
# =============================================================================
hdr("3) inline_base64 decoding — does FROM_BASE64 ever fail silently?")

df = run_query(f"""
WITH {IDENTITY_BASE_CTE},
inline AS (
  SELECT agent_uri, {INLINE_JSON_EXPR} AS card_json
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT
  COUNT(*) AS n_inline,
  COUNTIF(card_json IS NULL) AS n_decode_null,
  COUNTIF(card_json IS NOT NULL) AS n_decoded_ok,
  COUNTIF(SAFE.PARSE_JSON(card_json) IS NULL AND card_json IS NOT NULL) AS n_invalid_json,
  COUNTIF(SAFE.PARSE_JSON(card_json) IS NOT NULL) AS n_valid_json
FROM inline
""")
print(df.T)


# =============================================================================
# 4) x402Support = 4,389 — DEEP CHECK (the one the user asked about)
# =============================================================================
hdr("4) x402Support — exhaustive verification")

# 4a: try every plausible key spelling and see which ones the cards actually use
hdr("  4a) Which key spellings exist in the JSON?")
df = run_query(f"""
WITH {IDENTITY_BASE_CTE},
inline AS (
  SELECT {INLINE_JSON_EXPR} AS card_json
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT
  COUNT(*) AS n_inline,
  COUNTIF(JSON_VALUE(card_json, '$.x402Support')  IS NOT NULL) AS k_x402Support,
  COUNTIF(JSON_VALUE(card_json, '$.x402support')  IS NOT NULL) AS k_x402support,
  COUNTIF(JSON_VALUE(card_json, '$.X402Support')  IS NOT NULL) AS k_X402Support,
  COUNTIF(JSON_VALUE(card_json, '$.x402_support') IS NOT NULL) AS k_x402_support,
  COUNTIF(JSON_VALUE(card_json, '$.x402')         IS NOT NULL) AS k_x402,
  COUNTIF(JSON_VALUE(card_json, '$.X402')         IS NOT NULL) AS k_X402
FROM inline
WHERE card_json IS NOT NULL
""")
print(df.T)

# 4b: raw value distribution for x402Support
hdr("  4b) Raw value distribution of x402Support (no LOWER, no normalization)")
df = run_query(f"""
WITH {IDENTITY_BASE_CTE},
inline AS (
  SELECT {INLINE_JSON_EXPR} AS card_json
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT
  JSON_VALUE(card_json, '$.x402Support') AS raw_value,
  COUNT(*) AS n
FROM inline
WHERE card_json IS NOT NULL
GROUP BY raw_value
ORDER BY n DESC
""")
print(df.to_string(index=False))

# 4c: our dashboard's exact predicate
hdr("  4c) Dashboard predicate: LOWER(JSON_VALUE(card,'$.x402Support'))='true'")
df = run_query(f"""
WITH {IDENTITY_BASE_CTE},
inline AS (
  SELECT {INLINE_JSON_EXPR} AS card_json
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT
  COUNT(*) AS n_inline,
  COUNTIF(card_json IS NOT NULL) AS n_decoded,
  COUNTIF(LOWER(JSON_VALUE(card_json, '$.x402Support')) = 'true') AS n_x402_true,
  COUNTIF(LOWER(JSON_VALUE(card_json, '$.x402Support')) = 'false') AS n_x402_false,
  COUNTIF(JSON_VALUE(card_json, '$.x402Support') IS NULL) AS n_x402_null
FROM inline
""")
print(df.T)

# 4d: cross-check with PARSE_JSON + actual boolean lookup
hdr("  4d) Cross-check: BOOL(PARSE_JSON.x402Support) — native JSON type")
df = run_query(f"""
WITH {IDENTITY_BASE_CTE},
inline AS (
  SELECT SAFE.PARSE_JSON({INLINE_JSON_EXPR}) AS j
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT
  COUNTIF(j IS NOT NULL) AS n_parsed,
  COUNTIF(SAFE.BOOL(j.x402Support) = TRUE) AS n_true_native,
  COUNTIF(SAFE.BOOL(j.x402Support) = FALSE) AS n_false_native,
  COUNTIF(j.x402Support IS NULL) AS n_missing
FROM inline
""")
print(df.T)

# 4e: are there cards where x402Support claim doesn't match reality? Random sample.
hdr("  4e) 5 random cards claiming x402Support=true — does the description back it up?")
df = run_query(f"""
WITH {IDENTITY_BASE_CTE},
inline AS (
  SELECT agent_id, owner, {INLINE_JSON_EXPR} AS card_json
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT
  agent_id,
  JSON_VALUE(card_json, '$.name') AS name,
  JSON_VALUE(card_json, '$.x402Support') AS x402,
  JSON_VALUE(card_json, '$.registeredVia') AS registered_via,
  ARRAY_LENGTH(JSON_QUERY_ARRAY(card_json, '$.services')) AS n_services
FROM inline
WHERE LOWER(JSON_VALUE(card_json, '$.x402Support')) = 'true'
ORDER BY RAND() LIMIT 5
""")
print(df.to_string(index=False))

# 4f: split by registeredVia — is x402=true dominated by one platform?
hdr("  4f) x402=true breakdown by registeredVia")
df = run_query(f"""
WITH {IDENTITY_BASE_CTE},
inline AS (
  SELECT {INLINE_JSON_EXPR} AS card_json
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT
  COALESCE(JSON_VALUE(card_json, '$.registeredVia'), '(null)') AS registered_via,
  COUNTIF(LOWER(JSON_VALUE(card_json, '$.x402Support')) = 'true') AS n_x402_true,
  COUNTIF(LOWER(JSON_VALUE(card_json, '$.x402Support')) = 'false') AS n_x402_false,
  COUNT(*) AS n_total
FROM inline
WHERE card_json IS NOT NULL
GROUP BY registered_via
ORDER BY n_total DESC LIMIT 10
""")
print(df.to_string(index=False))


# =============================================================================
# 5) Functional count (services length > 0) — sanity check
# =============================================================================
hdr("5) Functional agents (services array non-empty)")
df = run_query(f"""
WITH {IDENTITY_BASE_CTE},
inline AS (
  SELECT {INLINE_JSON_EXPR} AS card_json
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT
  COUNTIF(JSON_QUERY_ARRAY(card_json, '$.services') IS NULL) AS n_services_missing_or_not_array,
  COUNTIF(ARRAY_LENGTH(JSON_QUERY_ARRAY(card_json, '$.services')) = 0) AS n_services_empty,
  COUNTIF(ARRAY_LENGTH(JSON_QUERY_ARRAY(card_json, '$.services')) > 0) AS n_services_present
FROM inline
WHERE card_json IS NOT NULL
""")
print(df.T)


# =============================================================================
# 6) Sybil bar (>= 3 unique reviewers) — already matches handoff §C, re-verify
# =============================================================================
hdr("6) Sybil bar pass count — independent recomputation")
df = run_query(f"""
WITH {REPUTATION_BASE_CTE},
per_agent AS (
  SELECT agent_id, COUNT(DISTINCT client) AS uc
  FROM reputation_base GROUP BY agent_id
)
SELECT
  COUNT(*) AS total_rated_agents,
  COUNTIF(uc >= 3) AS pass_sybil,
  COUNTIF(uc = 2) AS exactly_2,
  COUNTIF(uc = 1) AS exactly_1
FROM per_agent
""")
print(df.T)


# =============================================================================
# 7) Owner concentration — re-verify top 1 number
# =============================================================================
hdr("7) Owner top1 share — recomputed without CTE")
df = run_query(f"""
SELECT
  CONCAT('0x', SUBSTR(topics[SAFE_OFFSET(2)], 27)) AS owner,
  COUNT(*) AS n
FROM {LOGS}
WHERE address = '{IDENTITY_REGISTRY}'
  AND topics[SAFE_OFFSET(0)] = '{SIG_REGISTERED}'
  AND block_timestamp >= {PARTITION_CUT}
GROUP BY owner
ORDER BY n DESC
LIMIT 3
""")
print(df.to_string(index=False))


# =============================================================================
# 8) External host counts — re-verify ag0.xyz / api.normies.art
# =============================================================================
hdr("8) External host top 5 — recomputed")
df = run_query(f"""
WITH {IDENTITY_BASE_CTE}
SELECT
  REGEXP_EXTRACT(agent_uri, r'^https?://([^/]+)') AS host,
  COUNT(*) AS n,
  COUNT(DISTINCT owner) AS n_owners
FROM identity_base
WHERE agent_uri LIKE 'http%'
GROUP BY host
ORDER BY n DESC LIMIT 5
""")
print(df.to_string(index=False))


print("\n" + "="*78)
print("DONE. Compare each section against the dashboard values manually.")
print("="*78)
