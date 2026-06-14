# Demo video script

Three cuts. The **2-minute** version is the submission video. The
**90-second** booth walk-through is a backup; the **30-second** booth
pitch is what you say while a judge is still walking up.

All cuts assume the dashboard is already open on the first tab and the
live URL is the Cloud Run deployment
(`https://erc8004-reality-check-…-uc.a.run.app`).

---

## 2-minute cut (ETHGlobal submission — required 2-4 min)

The framing for this cut is **"observatory, not scanner."** Existing
ERC-8004 sites count registrations; this is the internal-analytics
dashboard that opens the box. Detailed numbers live in the dashboard —
the voice-over names what each tab is *for*.

**[0:00 – 0:22]  Open on the dashboard's first screen (brand row + Tab 1)**

> "Hi, I'm Young — I work on data science at American Express, and I
> built 8004 Reality Check. ERC-8004 is the new agent registry on
> Ethereum, and a few explorers already index it — but they all stop
> at the top-line number: thirty-four thousand agents registered.
> This is the first analytics dashboard built on Google's Web3
> ERC-8004 dataset that opens the box. Not just leaderboards —
> in-depth analytics on how ERC-8004 is actually used."

---

**[0:22 – 0:42]  Tab 1 — The Real Numbers funnel**

> "The first tab is the funnel. Everyone reports 34,569
> registrations. Watch what happens as we add reality. Of those,
> 9,520 carry an actual on-chain card. Only 224 expose a real
> service endpoint. 105 pass a three-reviewer trust bar. And just
> six are simultaneously trustworthy and payable."

*(Sweep across the funnel row left-to-right; land on the success
callout below it.)*

---

**[0:42 – 1:02]  Click "Who's Behind It"**

> "So who registered all of this? We dig into the owners. Here's the
> Pareto. One single wallet registered 9,967 agents — almost
> twenty-nine percent of the entire registry — every one with empty
> metadata. The top twenty wallets account for fifty-five percent.
> You can see external hosts run by a single wallet — bot-farm
> fingerprints. And the ENS column, right next to each address,
> turns anonymous hex into real identities wherever the owner has
> set one."

*(Open the top-wallet drill-down expander so the all-empty raw-counts
table is visible while you say "every one with empty metadata.")*

---

**[1:02 – 1:22]  Click "What Agents Actually Do"**

> "The third tab opens the agent cards — what the registrations
> actually are. Empty entries, NFT wrappers, test spam, and the
> genuine functional agents with real endpoints. We parse every
> on-chain base64 card inside BigQuery, then classify them. We also
> test the x402 claim against reality: 4,645 agents claim x402
> payment support — but only 32 owners ever received USDC on
> Ethereum mainnet, totaling about three hundred and twenty thousand
> dollars. Claim… versus settlement."

*(Hover the x402-claim-vs-reality KPIs while saying "claim versus
settlement.")*

---

**[1:22 – 1:44]  Click "Reputation, Real or Fake"**

> "Fourth tab — reputation. Every other scanner's filter is 'three
> or more unique reviewers.' It's here too — but so is what it
> misses. FeedbackURI hash collisions. Over three thousand feedback
> events share only 183 distinct hashes. One single piece of
> feedback was reused across 39 agents by 301 wallets — a
> coordinated wash campaign that sails right through the
> three-reviewer bar. The drill-downs surface the clients that only
> ever hand out perfect hundreds."

*(Scroll to the Q4b feedbackURI-collision table and rest on the
`0xc5d246…` row while you say "39 agents by 301 wallets.")*

---

**[1:44 – 2:02]  Click "Trustworthy + Payable"**

> "The fifth tab is the answer. It intersects everything — the Sybil
> bar, minimum reputation, the x402 claim, and real USDC settlement —
> and shows the agents that survive. And the ENS column tells the
> story: the registry's largest anonymous registrants have no ENS at
> all, while the agents that actually got paid — Surf, Ethy AI, Jeff
> Zyfai — are owned by ENS-named wallets. ENS as a credibility
> signal."

*(Point at the `owner_ens` column when you read the three names.)*

---

**[2:02 – 2:17]  Click "Find Agents", type the example**

> "The sixth tab is search — powered by Vertex AI Gemini. Watch:
> 'agents with at least five reviews and high reputation.' Gemini
> parses that sentence into structured filters, and BigQuery returns
> the result."

*(Type the sentence at human pace, press Enter, let the results
render.)*

---

**[2:17 – 2:29]  Closing insight — mainnet vs L2**

> "One thing worth flagging: this is Ethereum mainnet. x402 is
> Base-native, and a lot of these cards advertise multi-chain
> support. So mainnet is where agents plant their flag — Base and
> other L2s are where they actually work. Extending this same
> pipeline there is the natural next step."

---

**[2:29 – 2:42]  Stack close (back on the first screen, or on architecture)**

> "Under the hood: BigQuery for the data, Cloud Run for the app,
> Vertex AI Gemini for search, ENS for identity — all through one
> GCP service account. No API keys, no secret files. It's open
> source. The repo and live demo are linked below. Thanks for
> watching."

---

## 90-second cut (booth + backup)

Same framing as the 2-minute cut, tighter. Use this if the submission
upload fails or a judge asks for the short version.

**[0:00 – 0:12]  Open**

> "I'm Young, working on data science at AmEx. ERC 8004 Reality Check
> opens the box on the agent registry — the first analytics dashboard
> built straight from Google's Web3 ERC-8004 dataset. Not a top-line
> counter; in-depth analytics on how the registry is actually used."

---

**[0:12 – 0:22]  Tab 1 — Funnel**

> "First tab is the funnel. Every step is a strict subset of the one
> above it, all the way down to the wallets that actually received a
> USDC payment. The chain confirming the claim."

---

**[0:22 – 0:35]  Tab 2 — Owners**

> "Second tab: who registered all this. Owner Pareto, bot-farm hosts
> (one wallet running many cards under one domain), and a drill-down
> on the single biggest registrant. The ENS column right next to the
> address turns anonymous wallets into real identities where the
> owner has set one."

---

**[0:35 – 0:48]  Tab 3 — Agents**

> "Third tab opens the agent cards. What shape are the registrations?
> Empty, NFT wrapper, test spam, functional with a real endpoint —
> all classified. The headline here is x402 claim versus reality:
> a `token_transfers` JOIN that checks who actually accepts payment."

---

**[0:48 – 1:01]  Tab 4 — Reputation**

> "Fourth tab is reputation. The standard Sybil filter that every
> other scanner uses is here, but you'll also find what it misses —
> feedbackURI hash collisions that catch coordinated wash campaigns,
> and a drill-down on clients that only ever hand out perfect scores."

---

**[1:01 – 1:15]  Tab 5 — Trustworthy + Payable**

> "Fifth tab is the answer. Intersect every filter — Sybil bar, score,
> x402 claim, real USDC — and the registry collapses to a handful of
> agents. The ENS column shows the credibility signal: the largest
> anonymous registrants have no ENS, the real ones do."

---

**[1:15 – 1:25]  Tab 6 — Search**

> "Sixth tab is search — free text powered by Vertex AI Gemini, same
> service account as BigQuery and ENS. No API key, no secrets."

---

**[1:25 – 1:30]  Close**

> "BigQuery, Cloud Run, Vertex AI Gemini, ENS. Open source. Repo and
> live demo linked."

---

## 30-second booth cut

For walking judges through the framing in one breath.

> "I'm Young, working on data science at AmEx. ERC 8004 Reality Check
> opens the box on the registry — the first in-depth analytics
> dashboard built straight from Google's Web3 ERC-8004 dataset. Six
> tabs that walk you from who registered, to what they actually are,
> to which ones got paid, to a Gemini-powered natural-language search.
> Same service account does BigQuery, Cloud Run, Vertex AI, and ENS —
> no API key anywhere. Open source, live demo linked."

---

## Final checklist (run through 30 min before recording)

1. **Cloud Run redeploy** — make sure the live URL serves the latest
   commit. From the repo root:
   ```bash
   gcloud run deploy erc8004-reality-check \
     --source=. --region=us-central1 --project="$PROJECT" \
     --service-account="$NEW_SA_EMAIL" --allow-unauthenticated \
     --memory=1Gi --cpu=1 --min-instances=0 --max-instances=2
   ```
   Wait for "Service URL" in the output before recording.
2. **Open the live URL in a clean browser window** — incognito if your
   normal window has extensions or login prompts that might pop in.
3. **Pre-warm the cache** — click through every tab once so subsequent
   loads are instant; the recording shouldn't include a 5-second
   spinner.
4. **Theme = Light** (Streamlit `⋮` → Settings → Light) — the red
   primary color reads cleanly against white.
5. **Window size = 1280×800** so the seven nav links sit on a single
   row and screenshot proportions match GitHub previews.
6. **Mic check** — 10-second test, listen back, adjust input gain.
7. **Close any apps that play notification sounds** (Slack, Mail,
   iMessage). Set Mac to Do Not Disturb.
8. **Practice once silently** (mouse moves only), then once with audio,
   then record the take. Three takes is plenty.

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
