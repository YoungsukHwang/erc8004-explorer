# ERC-8004 Agent Explorer

**Target track:** GCP "Best On-Chain Agent Economy Application" — ETHGlobal NY 2026.

> *"We index the noise. You see the signal."*

The four existing ERC-8004 scanners (`8004scan`, `trust8004`, `agentscan`,
`8004agents`) all brag about big multi-chain registration counts. None of them
verify whether the agents do anything, whether the owners are independent,
or whether the reputation is real. This explorer opens the boxes.

## The headline (every number verified against raw BigQuery)

| Funnel stage | Count | % of registered |
|---|---:|---:|
| Identity Registered events on mainnet | **34,566** | 100% |
| Has any inline on-chain card | 9,520 | 27.5% |
| Has a non-empty service endpoint | **224** | **0.65%** |
| Has at least one feedback event | 1,652 | 4.8% |
| Passes the gist Sybil bar (≥ 3 unique reviewers) | **105** | **0.30%** |
| Claims `x402Support = true` | 4,645 | 13.4% |
| **…of those, actually received any USDC transfer** | **32** | **0.09%** |

Two extra things the competing scanners miss entirely:

- **Owner concentration:** the top wallet `0xd5d6d96…` alone registered
  **9,967 agents (28.8%)**; the top 20 wallets cover **55%** of all
  registrations. Single-owner external hosts (`api.normies.art` 1,171,
  `api.freaks.one` 267, `exquisites.es` 201) are bot-farm fingerprints.
- **Reputation washing:** the 3,173 feedback events share only **183
  distinct `feedbackURI` hashes** — mean 17× reuse per hash. One client
  gave 1,215 feedbacks across 1,102 agents using just **two URI hashes**.
  Another single hash (`0xc5d246…`) appears 386 times from 301 different
  clients targeting 39 agents — a coordinated Sybil campaign disguised as
  independent voices. The `unique_clients ≥ 3` filter doesn't catch any
  of this.

## Stack

- **Data:** `bigquery-public-data.goog_blockchain_ethereum_mainnet_us`
  (Google's public Ethereum mainnet dataset). Every query carries a
  `block_timestamp >= '2026-01-28'` partition cut so scans stay well inside
  the 1 TB / month BigQuery free tier.
- **Frontend:** Streamlit. Each tab calls `bq.run_query()` which is wrapped
  in `@st.cache_data(ttl=3600)`.
- **Contracts (verified on-chain):**
  - `IdentityRegistry` = `0x8004a169fb4a3325136eb29fa0ceb6d2e539a432`
  - `ReputationRegistry` = `0x8004baa17c55a88189ae136b182e5fda19de9b63`
  - `ValidationRegistry` — **no mainnet address.** Spec incomplete; we show
    this gap rather than hide it.

## Decoding (verified against raw bytes — do not trust any other write-up)

Identity / Reputation use *different* topic layouts. Both have indexed
`agent_id` at `topics[1]`, but `topics[2]` is the owner address for Identity
and the client (rater) address for Reputation. `topics[3]` only exists on
Reputation and carries the `feedbackURI` hash — the wash-detection field.

```
Registered  signature: 0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a
NewFeedback signature: 0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc

Identity Registered (num_topics=3):
  topics[1] = agent_id          (uint256)
  topics[2] = owner             (last 20 bytes)
  data      = agent_uri         (ABI dynamic string, often base64-inline JSON)

Reputation NewFeedback (num_topics=4):
  topics[1] = agent_id
  topics[2] = client (rater)
  topics[3] = feedbackURI hash   ← key field for wash detection
  data      = score, fixedDecimals, plain feedbackURI, agent card snapshot
```

Inline cards arrive as `data:application/json;base64,…` and decode cleanly
(9,520 / 9,521 succeed; 1 is base64-corrupt). Keys verified against raw card
inspection — **the spec is `x402Support` with a capital S**, but ~5% of
cards use lowercase `x402support`; we union both. `services[].name` (not
`protocol`) is the protocol slot. `services[].skills[]` is a string array
of OASF taxonomy paths.

## Project layout

```
app/
  bq.py        BigQuery client, partition cut, reusable CTE snippets
  queries.py   Every dashboard SQL, one function per view item
  app.py       Streamlit entry — 4 tabs
  verify.py    Standalone cross-check script: three independent paths to
               every headline number. Run before trusting anything.
  validate.py  Quick step-by-step JSON / agent_class sanity script
  peek_cards.py  Raw card inspector for key discovery
```

## How to run

```bash
# one-time setup
conda create -n erc8004 python=3.12
conda activate erc8004
pip install google-cloud-bigquery streamlit pandas db-dtypes
gcloud auth application-default login
gcloud auth application-default set-quota-project <your-gcp-project>

# launch
cd /path/to/ethglobal
streamlit run app/app.py
```

The first page load runs ~6 queries; subsequent loads hit the per-process
cache (TTL 1 h). Total bytes scanned per page load is single-digit GB
thanks to the partition cut.

## Deploy on Streamlit Community Cloud

`bq.py` looks for `st.secrets["gcp_service_account"]` first and only falls
back to ADC when it's missing — so the same code runs locally and on
Streamlit Cloud without any branching at call sites.

1. **Create a service account** in your GCP project (Console → IAM &
   Admin → Service Accounts → New). No special scopes needed at creation
   time.
2. **Grant two roles** to that service account on the project:
   - `BigQuery Data Viewer` (so it can read the public dataset)
   - `BigQuery Job User` (so it can run queries — bills to your project)
3. **Download a JSON key** (the service account → Keys → Add Key → JSON).
4. **Connect the repo** at `share.streamlit.io` → "New app" → point at
   `app/app.py`.
5. **Paste the JSON key into Secrets** as a TOML block:
   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "…"
   private_key = "-----BEGIN PRIVATE KEY-----\n…\n-----END PRIVATE KEY-----\n"
   client_email = "your-sa@your-project.iam.gserviceaccount.com"
   client_id = "…"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "…"
   ```
   Streamlit Cloud will redeploy automatically. The free tier is enough
   for the dashboard's per-load scans.

## The four views

1. **The Real Numbers** — the 6-step funnel above + daily/cumulative
   registration chart (the 22,695 launch-week spike, then a single-digit
   baseline).
2. **Who's Behind It** — owner Pareto (top 1 / 10 / 20 share), top 20
   owner table, external URI host breakdown (`n_owners = 1` = bot-farm
   signature), `registeredVia` cross-check.
3. **What Agents Actually Do** — `agent_class` 6-bucket classification,
   URI scheme breakdown (including the `plain_json` 2,164 cards that
   turn out to be Twitter-style user profiles, not ERC-8004 agents at
   all), x402 claim vs reality (4,645 claims → 32 USDC recipients), top
   `service.name` protocols (OASF / web / custom / MCP / A2A), top OASF
   skills, `registeredVia` platforms.
4. **Reputation, Real or Fake** — overall feedback counts and
   reviewer-count distribution (1,472 agents with exactly one reviewer is
   the long tail the Sybil bar dismisses), Q3 leaderboard (the 105
   agents that pass `unique_clients ≥ 3`), Q4 client dominance with a
   `uri_diversity` progress bar, Q4b feedback-URI hash collisions, plus
   drill-down expanders for score-outlier rows and perfect-100-only
   wallets.

## What we did NOT build (deliberate)

- **No risk model.** The pitch is *observation and exposure*, not
  scoring. Every number is a raw count or a documented ratio.
- **No off-chain fetches.** `https://` / `ipfs://` URIs are reported as a
  category (and broken down by host) but not dereferenced — they're not
  verifiable on-chain.
- **No multi-chain.** Mainnet only; the GCP track is specifically about
  on-chain agent economy and mainnet is where ERC-8004 actually lives.
- **No ValidationRegistry view.** There is no mainnet address yet
  (spec WIP). Acknowledged explicitly in the sidebar.

## Trust but verify

Run `python verify.py` from `app/` to cross-check every dashboard number
against an independent SQL path. Each section prints the value, a
second-path recomputation, and (for x402) a third native-JSON
`SAFE.BOOL(PARSE_JSON.x402Support)` check. Mismatches are flagged inline.
