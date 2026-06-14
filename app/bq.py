"""BigQuery connection + cached query helpers.

All queries MUST include the partition cut `block_timestamp >= TIMESTAMP '2026-01-28'`.
mainnet went live 2026-01-29; the cut keeps scans on a tiny slice of the public dataset.
"""
from __future__ import annotations

import os
import pandas as pd
from google.cloud import bigquery

try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False


DATASET = "bigquery-public-data.goog_blockchain_ethereum_mainnet_us"
LOGS = f"`{DATASET}.logs`"
TOKEN_TRANSFERS = f"`{DATASET}.token_transfers`"

IDENTITY_REGISTRY = "0x8004a169fb4a3325136eb29fa0ceb6d2e539a432"
REPUTATION_REGISTRY = "0x8004baa17c55a88189ae136b182e5fda19de9b63"
USDC_ADDRESS = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

SIG_REGISTERED = "0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a"
SIG_NEW_FEEDBACK = "0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc"

PARTITION_CUT = "TIMESTAMP '2026-01-28'"


def _client() -> bigquery.Client:
    """BigQuery client. On Streamlit Cloud, expects a `gcp_service_account`
    block in `st.secrets`. Locally, falls back to Application Default
    Credentials (`gcloud auth application-default login`)."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or "project-cc7ed957-d1e3-4c3f-8b5"
    if _HAS_STREAMLIT:
        try:
            sa = st.secrets.get("gcp_service_account")
        except Exception:
            sa = None
        if sa:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(dict(sa))
            return bigquery.Client(project=sa.get("project_id", project), credentials=creds)
    return bigquery.Client(project=project)


def _run(sql: str) -> pd.DataFrame:
    return _client().query(sql).result().to_dataframe(create_bqstorage_client=False)


if _HAS_STREAMLIT:
    @st.cache_data(ttl=3600, show_spinner=False)
    def run_query(sql: str) -> pd.DataFrame:
        return _run(sql)
else:
    def run_query(sql: str) -> pd.DataFrame:
        return _run(sql)


# -----------------------------------------------------------------------------
# Reusable SQL snippets
# -----------------------------------------------------------------------------

# Identity Registered base: agent_id (topics[1]) + owner (topics[2]) + agent_uri (data dynamic string)
IDENTITY_BASE_CTE = f"""
identity_base AS (
  SELECT
    block_timestamp,
    transaction_hash,
    SAFE_CAST(topics[SAFE_OFFSET(1)] AS INT64) AS agent_id,
    CONCAT('0x', SUBSTR(topics[SAFE_OFFSET(2)], 27)) AS owner,
    -- agent_uri = ABI dynamic string in `data`:
    -- bytes 1-2  = '0x', 3-66 = offset, 67-130 = length, 131..= payload
    SAFE_CONVERT_BYTES_TO_STRING(FROM_HEX(SUBSTR(
      data, 131,
      2 * SAFE_CAST(CONCAT('0x', SUBSTR(data, 67, 64)) AS INT64)
    ))) AS agent_uri
  FROM {LOGS}
  WHERE address = '{IDENTITY_REGISTRY}'
    AND topics[SAFE_OFFSET(0)] = '{SIG_REGISTERED}'
    AND block_timestamp >= {PARTITION_CUT}
)
"""

# Reputation NewFeedback base
REPUTATION_BASE_CTE = f"""
reputation_base AS (
  SELECT
    block_timestamp,
    transaction_hash,
    SAFE_CAST(topics[SAFE_OFFSET(1)] AS INT64) AS agent_id,
    CONCAT('0x', SUBSTR(topics[SAFE_OFFSET(2)], 27)) AS client,
    topics[SAFE_OFFSET(3)] AS feedback_uri_hash,
    CASE
      WHEN SUBSTR(data, 67, 1) = 'f' THEN NULL  -- negative-encoded, skip
      ELSE SAFE_CAST(CONCAT('0x', SUBSTR(data, 67, 64)) AS INT64)
           / POW(10, SAFE_CAST(CONCAT('0x', SUBSTR(data, 131, 64)) AS INT64))
    END AS score
  FROM {LOGS}
  WHERE address = '{REPUTATION_REGISTRY}'
    AND topics[SAFE_OFFSET(0)] = '{SIG_NEW_FEEDBACK}'
    AND block_timestamp >= {PARTITION_CUT}
)
"""

# Base64-decoded inline JSON for on-chain agent cards
INLINE_JSON_EXPR = """
SAFE_CONVERT_BYTES_TO_STRING(SAFE.FROM_BASE64(
  SUBSTR(agent_uri, LENGTH('data:application/json;base64,') + 1)
))
"""

# Unified x402Support extractor — cards use either capital-S or all-lowercase
# spelling, never both in the same card (verified). Returns lowercased value or NULL.
X402_VALUE_EXPR = """
LOWER(COALESCE(
  JSON_VALUE(card_json, '$.x402Support'),
  JSON_VALUE(card_json, '$.x402support')
))
"""
