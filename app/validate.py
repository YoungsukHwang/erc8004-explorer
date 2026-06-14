"""Standalone validation: agent_uri decoding, JSON parsing, agent_class buckets.

Run with: python -m app.validate  (from /Users/YoungsukHwang/projects/ethglobal)
"""
from __future__ import annotations

import sys
import pandas as pd

from bq import (
    run_query,
    IDENTITY_BASE_CTE,
    INLINE_JSON_EXPR,
)

pd.set_option("display.max_colwidth", 80)
pd.set_option("display.width", 160)


def step(title: str) -> None:
    print(f"\n{'='*78}\n{title}\n{'='*78}")


# -----------------------------------------------------------------------------
# Step 1 — Sanity check: total Registered events, with vs without agent_uri
# -----------------------------------------------------------------------------

def s1_counts() -> None:
    step("Step 1 — Registered counts + uri scheme distribution")
    sql = f"""
    WITH {IDENTITY_BASE_CTE}
    SELECT
      COUNT(*) AS n_registered,
      COUNTIF(agent_uri IS NOT NULL AND agent_uri != '') AS n_with_uri,
      COUNTIF(agent_uri IS NULL OR agent_uri = '') AS n_no_uri,
      COUNTIF(STARTS_WITH(agent_uri, 'data:application/json;base64,')) AS n_inline_b64,
      COUNTIF(STARTS_WITH(agent_uri, 'https://')) AS n_https,
      COUNTIF(STARTS_WITH(agent_uri, 'http://')) AS n_http,
      COUNTIF(STARTS_WITH(agent_uri, 'ipfs://')) AS n_ipfs
    FROM identity_base
    """
    df = run_query(sql)
    print(df.T)


# -----------------------------------------------------------------------------
# Step 2 — Sample 5 inline JSON cards (raw + parsed name/desc)
# -----------------------------------------------------------------------------

def s2_sample_inline() -> None:
    step("Step 2 — Sample inline base64 JSON cards (real keys)")
    sql = f"""
    WITH {IDENTITY_BASE_CTE},
    decoded AS (
      SELECT
        agent_id, owner,
        {INLINE_JSON_EXPR} AS card_json
      FROM identity_base
      WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
    )
    SELECT
      agent_id, owner,
      JSON_VALUE(card_json, '$.name') AS name,
      JSON_VALUE(card_json, '$.x402Support') AS x402,
      JSON_VALUE(card_json, '$.active') AS active,
      JSON_VALUE(card_json, '$.registeredVia') AS registered_via,
      JSON_VALUE(card_json, '$.nftOrigin.contract') AS nft_contract,
      ARRAY_LENGTH(JSON_QUERY_ARRAY(card_json, '$.services')) AS n_services
    FROM decoded
    WHERE card_json IS NOT NULL
    LIMIT 6
    """
    df = run_query(sql)
    print(df)


# -----------------------------------------------------------------------------
# Step 3 — agent_class bucketing
#   Priority (top wins):
#     1. no_uri      — uri missing
#     2. not_json    — uri present but not parseable inline JSON / external
#     3. test_spam   — name or description contains 'test' (case-insensitive)
#     4. nft_pfp     — name/description hints at NFT/PFP/monster/character
#     5. functional  — has at least one service endpoint
#     6. other_card  — has a card but none of the above
# -----------------------------------------------------------------------------

AGENT_CLASS_SQL = f"""
WITH {IDENTITY_BASE_CTE},
decoded AS (
  SELECT
    agent_id, owner, agent_uri,
    CASE
      WHEN STARTS_WITH(agent_uri, 'data:application/json;base64,')
        THEN {INLINE_JSON_EXPR}
      ELSE NULL
    END AS card_json
  FROM identity_base
),
classified AS (
  SELECT
    agent_id, owner, agent_uri, card_json,
    LOWER(COALESCE(JSON_VALUE(card_json, '$.name'), '')) AS name_l,
    LOWER(COALESCE(JSON_VALUE(card_json, '$.description'), '')) AS desc_l,
    JSON_QUERY_ARRAY(card_json, '$.services') AS services_arr,
    JSON_VALUE(card_json, '$.nftOrigin.contract') AS nft_contract
  FROM decoded
)
SELECT
  CASE
    WHEN agent_uri IS NULL OR agent_uri = '' THEN '1_no_uri'
    WHEN card_json IS NULL THEN '2_external_uri'
    WHEN REGEXP_CONTAINS(name_l, r'\\btest\\b') OR REGEXP_CONTAINS(desc_l, r'\\btest\\b') THEN '3_test_spam'
    WHEN ARRAY_LENGTH(services_arr) > 0 THEN '4_functional'
    WHEN nft_contract IS NOT NULL THEN '5_nft_wrapper'
    ELSE '6_other_card'
  END AS agent_class,
  COUNT(*) AS n,
  COUNT(DISTINCT owner) AS n_owners
FROM classified
GROUP BY agent_class
ORDER BY agent_class
"""


def s3_classify() -> None:
    step("Step 3 — agent_class bucket counts")
    df = run_query(AGENT_CLASS_SQL)
    total = df["n"].sum()
    df["pct"] = (df["n"] / total * 100).round(2)
    print(df)
    print(f"\nTotal: {total:,}")


# -----------------------------------------------------------------------------
# Step 4 — Inline JSON deep dive: top categories from services / skills / x402
# -----------------------------------------------------------------------------

def s4_json_distributions() -> None:
    step("Step 4a — x402Support distribution")
    sql = f"""
    WITH {IDENTITY_BASE_CTE},
    decoded AS (
      SELECT {INLINE_JSON_EXPR} AS card_json
      FROM identity_base
      WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
    )
    SELECT
      COALESCE(LOWER(JSON_VALUE(card_json, '$.x402Support')), '(null)') AS x402,
      COUNT(*) AS n
    FROM decoded
    WHERE card_json IS NOT NULL
    GROUP BY x402 ORDER BY n DESC
    """
    print(run_query(sql))

    step("Step 4b — Top service.name (protocol slot: OASF / web / MCP / A2A)")
    sql2 = f"""
    WITH {IDENTITY_BASE_CTE},
    decoded AS (
      SELECT {INLINE_JSON_EXPR} AS card_json
      FROM identity_base
      WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
    ),
    flat AS (
      SELECT LOWER(JSON_VALUE(svc, '$.name')) AS svc_name
      FROM decoded, UNNEST(COALESCE(JSON_QUERY_ARRAY(card_json, '$.services'), [])) AS svc
    )
    SELECT COALESCE(svc_name, '(null)') AS svc_name, COUNT(*) AS n
    FROM flat GROUP BY svc_name ORDER BY n DESC LIMIT 15
    """
    print(run_query(sql2))

    step("Step 4c — Top skills (services[i].skills, string array)")
    sql3 = f"""
    WITH {IDENTITY_BASE_CTE},
    decoded AS (
      SELECT {INLINE_JSON_EXPR} AS card_json
      FROM identity_base
      WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
    ),
    flat AS (
      SELECT LOWER(sk) AS skill
      FROM decoded,
           UNNEST(COALESCE(JSON_QUERY_ARRAY(card_json, '$.services'), [])) AS svc,
           UNNEST(JSON_VALUE_ARRAY(svc, '$.skills')) AS sk
    )
    SELECT skill, COUNT(*) AS n
    FROM flat WHERE skill IS NOT NULL
    GROUP BY skill ORDER BY n DESC LIMIT 20
    """
    print(run_query(sql3))

    step("Step 4d — Top registeredVia platforms (bot-farm signal)")
    sql4 = f"""
    WITH {IDENTITY_BASE_CTE},
    decoded AS (
      SELECT owner, {INLINE_JSON_EXPR} AS card_json
      FROM identity_base
      WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
    )
    SELECT
      COALESCE(JSON_VALUE(card_json, '$.registeredVia'), '(null)') AS registered_via,
      COUNT(*) AS n,
      COUNT(DISTINCT owner) AS n_owners
    FROM decoded
    WHERE card_json IS NOT NULL
    GROUP BY registered_via ORDER BY n DESC LIMIT 10
    """
    print(run_query(sql4))

    step("Step 4e — active=true vs false (self-reported live)")
    sql5 = f"""
    WITH {IDENTITY_BASE_CTE},
    decoded AS (
      SELECT {INLINE_JSON_EXPR} AS card_json
      FROM identity_base
      WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
    )
    SELECT
      COALESCE(LOWER(JSON_VALUE(card_json, '$.active')), '(null)') AS active,
      COUNT(*) AS n
    FROM decoded WHERE card_json IS NOT NULL
    GROUP BY active ORDER BY n DESC
    """
    print(run_query(sql5))


if __name__ == "__main__":
    steps = sys.argv[1:] or ["1", "2", "3", "4"]
    if "1" in steps: s1_counts()
    if "2" in steps: s2_sample_inline()
    if "3" in steps: s3_classify()
    if "4" in steps: s4_json_distributions()
