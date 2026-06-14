# Demo video script

Two cuts. The **90-second** version is the submission video. The **30-second**
version is the booth walk-through — short enough to repeat ten times in
front of judges without losing your voice.

Both versions assume the dashboard is already open on tab 1 and the live URL
is the Cloud Run deployment (`https://erc8004-reality-check-…-uc.a.run.app`).

---

## 90-second cut (submission)

Read the times as "by this point you should be on this screen." Words in
**bold** are the ones to land on; everything else is connective tissue.

**[0:00 – 0:08]  Open on Tab 1 — "The Real Numbers"**

> "ERC-8004 is Ethereum's new identity, reputation and payment registry
> for AI agents. On mainnet it has **34,569 registrations** today. This
> dashboard reads them straight from BigQuery and shows what's actually
> behind that number."

*(Briefly hover the top funnel row.)*

---

**[0:08 – 0:18]  Tab 1, the strict-subset funnel**

> "Each step here is a real subset of the previous one. Of those 34,569
> registrations, only **9,520 carry an on-chain card**. Of those, only
> **1,652 ever received a feedback event**. Only **105 pass the standard
> Sybil filter** of at least three unique reviewers. And only **32
> wallets ever received a real USDC payment** — **320 thousand dollars
> total**. The 99 percent gap between claim and reality is the story."

---

**[0:18 – 0:33]  Click "Who's Behind It"**

> "The top wallet alone registered **9,967 agents** — 29 percent of the
> entire registry. Every single one has an empty agent_uri. No card, no
> service, no x402, no nftOrigin. The top three wallets together account
> for over a third of the registry, and **none of them have set an ENS
> name**."

*(Open the top-wallet drill-down expander, point at the empty rows.)*

---

**[0:33 – 0:48]  Click "What Agents Actually Do"**

> "Inside the 9,520 cards: only **224 have a real service endpoint** —
> that's two percent. **4,645 cards claim x402 payment support**, but
> when we join `token_transfers`, only **32 owners** ever received
> USDC. The claim was set with one line of JSON; the reality required
> on-chain settlement."

*(Hover the x402-claim-vs-reality KPIs.)*

---

**[0:48 – 1:03]  Click "Reputation, Real or Fake"**

> "Even the 105 agents that pass the Sybil bar are not safe. 3,173
> feedback events share only **183 distinct feedbackURI hashes** —
> seventeen times reuse on average. One hash, `0xc5d246…`, appears 386
> times from **301 different wallets** targeting only 39 agents. That's
> a coordinated Sybil campaign disguised as 301 independent voices."

---

**[1:03 – 1:18]  Click "Trustworthy + Payable"**

> "Here's the shortlist the prize statement asks for. We take the Sybil
> bar, a minimum average score of 80, the x402 flag, and the
> `token_transfers` USDC join — and the entire ERC-8004 registry
> collapses to **six agents**. **kevinlilili.eth** runs the only one
> that pulled in more than a thousand dollars."

*(Highlight the `owner_ens` column.)*

---

**[1:18 – 1:28]  Click "Find Agents", type the example**

> "And finally — natural-language search, powered by Vertex AI Gemini.
> 'Agents with at least 5 reviews and high reputation.' Gemini parses
> it into structured filters, BigQuery returns the result. No API key,
> no secret file — the same service account that reads BigQuery calls
> Gemini."

*(Press Enter, let the results render.)*

---

**[1:28 – 1:30]  Close**

> "BigQuery, Cloud Run, Vertex AI, ENS. Open source. Repo and live demo
> in the description."

---

## 30-second booth cut

For walking judges through the headline in one breath.

> "ERC-8004 registry has **34,569 agents on mainnet**. Only **32
> wallets** ever received a real USDC payment — that's the claim-vs-
> reality gap. The top wallet registered **9,967 empty agents**, all
> anonymous. After filtering for trust, reputation, x402, and real
> USDC settlement, the entire registry collapses to **six agents** —
> the two that actually got paid are both owned by ENS-named wallets.
> Built on BigQuery, Cloud Run, Vertex AI, and ENS reverse resolution.
> Open source, live demo linked."

---

## Recording tips

- **macOS QuickTime** → File → New Screen Recording → Options → mic on.
- Run **at 1280×800** so the tabs all fit on a single row.
- **Light mode** in Streamlit ("⋮" → Settings → Theme → Light) — the
  red active-link pops more cleanly on white.
- Practice the cut **once** silent (mouse moves only), then **once**
  with audio, then **record**. Three takes is plenty.
- Keep the cursor still during voice-overs — moving it pulls the
  viewer's eye away from the metric you're reading.
- Export as MP4 H.264. Drop into the ETHGlobal submission form.

## What to point at on each tab

| Tab | First metric / element to highlight |
|---|---|
| The Real Numbers | The five funnel KPIs (left to right) |
| Who's Behind It | "Top 1 owner share" + the drill-down expander |
| What Agents Actually Do | The three x402 reality columns |
| Reputation, Real or Fake | Q4b URI collision table — row `0xc5d246…` |
| Trustworthy + Payable | The `owner_ens` column |
| Find Agents | The text box → result table |
| Cheat Sheet | The headline funnel row again, then the bottom one-liner |
