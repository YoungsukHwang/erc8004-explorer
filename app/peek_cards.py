"""Peek raw JSON cards to discover actual key names."""
from __future__ import annotations
import json
from bq import run_query, IDENTITY_BASE_CTE, INLINE_JSON_EXPR

# Pull 6 inline cards: 2 functional-looking (high data length), 2 short, 2 random
sql = f"""
WITH {IDENTITY_BASE_CTE},
decoded AS (
  SELECT
    agent_id,
    owner,
    LENGTH(agent_uri) AS uri_len,
    {INLINE_JSON_EXPR} AS card_json
  FROM identity_base
  WHERE STARTS_WITH(agent_uri, 'data:application/json;base64,')
)
SELECT agent_id, owner, uri_len, card_json
FROM decoded
WHERE card_json IS NOT NULL
ORDER BY uri_len DESC
LIMIT 6
"""

df = run_query(sql)
for i, row in df.iterrows():
    print(f"\n{'='*78}\nagent_id={row.agent_id}  owner={row.owner}  uri_len={row.uri_len}\n{'='*78}")
    try:
        parsed = json.loads(row.card_json)
        # Print top-level keys + a peek at array contents
        print("Top-level keys:", list(parsed.keys()))
        for k, v in parsed.items():
            if isinstance(v, list):
                print(f"  {k} (list, len={len(v)}):")
                if v:
                    print(f"    item[0] keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0]).__name__}")
                    print(f"    item[0] sample: {json.dumps(v[0])[:200]}")
            elif isinstance(v, dict):
                print(f"  {k} (dict): keys={list(v.keys())}")
            else:
                sv = str(v)
                print(f"  {k}: {sv[:100]}")
    except Exception as e:
        print(f"PARSE ERROR: {e}")
        print(row.card_json[:300])
