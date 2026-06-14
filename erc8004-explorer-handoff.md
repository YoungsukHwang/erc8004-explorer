# ERC-8004 Agent Explorer — 빌드 핸드오프 (v3)

> **이걸 새 챗(Opus)에 통째로 붙이고 "여기서부터 빌드 시작, JSON 파싱부터"라고 하면 됨.**
> EthGlobal NY 2026 / 토요일 밤, 일요일 아침 GCP 부스 심사 / 스택: BigQuery + Streamlit
> ⚠️ 아래 스키마·숫자는 전부 BigQuery 실쿼리로 검증됨(추정 아님). **이 문서 정보만 신뢰.**

---

## ▶ 지금 당장 할 일 (다음 액션)

1. GCP 프로젝트 ID + 인증 상태 확인 (`gcloud auth application-default login` 했는지).
2. **Streamlit 골격 생성**: BigQuery 연결 + 아래 4개 뷰 탭.
3. **JSON 파싱 뷰부터** 채우기 (아래 §B 1순위 — deep-dive 핵심).

빌더: Young — 데이터 사이언스 컨설턴트(AmEx, CCAR/리스크), Columbia MS&E, SQL/대시보드/x402 강함(RiskLens로 EasyA Miami 파이널리스트). 한국어 소통, 기술용어 영어. 구체적·복붙 가능한 코드 선호. 토요일 컨디션 안 좋았음 → 작동하는 MVP 우선, 무리 X.

---

## ▶ 목표 & 차별화 (한 단락)

**GCP "Best On-Chain Agent Economy Application" 트랙($5,000 현금)** 단일 타깃. (ETHGlobal finalist는 별개 라인이고 스코프상 안 노림.) 발표자가 "아직 아무도 좋은 analytics explorer를 안 만들었다, 그게 $5K 주는 이유"라고 직접 말함 — 경쟁 공백.

경쟁 스캐너 4개(8004scan, trust8004, agentscan, 8004agents)는 전부 **멀티체인 "수십만 agents" 숫자 자랑 + "등록=존재" 카운트 + registry logs만 읽음 + Sybil/wash 미검증**. 차별화 = 그 숫자 **안을 deep-dive해 폭로**. **리스크 모델 만들지 말 것 — "관찰과 폭로"만.** trust8004이 푸터에 "We index the noise. You filter the signal"이라 써둠 → 그 filter가 곧 이 프로젝트.

**헤드라인 스토리:** "등록 46K, 진짜 평가받은 건 ~105개(0.2%). 그 평판마저 소수 지갑이 도배."

---

## ▶ A. 검증된 디코딩 스키마 (RAW로 확정 — 절대 헷갈리지 말 것)

**핵심 함정: Identity와 Reputation은 topic 레이아웃이 다르다.**

```
데이터셋:  bigquery-public-data.goog_blockchain_ethereum_mainnet_us.logs
           (crypto_ethereum 아님! 같은 데이터셋에 transactions, token_transfers,
            traces, decoded_events, accounts, accounts_state 등 12개 테이블 존재)

IdentityRegistry:    0x8004a169fb4a3325136eb29fa0ceb6d2e539a432
ReputationRegistry:  0x8004baa17c55a88189ae136b182e5fda19de9b63
ValidationRegistry:  mainnet 주소 없음 (스펙 미완성 → "데이터 없음"으로 표기 = 그 자체로 인사이트)

Registered  sig: 0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a
NewFeedback sig: 0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc
파티션 컷:  block_timestamp >= TIMESTAMP '2026-01-28'   (mainnet 2026-01-29 라이브)
인증: gcloud auth application-default login (ADC)
```

### Identity — Registered  (indexed 2개 → num_topics=3)
| 위치 | 필드 | 디코딩 |
|---|---|---|
| topics[0] | 시그니처 | 필터용 |
| topics[1] | **agent_id** | `SAFE_CAST(topics[SAFE_OFFSET(1)] AS INT64)` |
| topics[2] | **owner** | `CONCAT('0x', SUBSTR(topics[SAFE_OFFSET(2)], 27))` |
| data | **agent_uri** | 아래 디코딩 식 |

- agent_id 등록 1회 = **중복 없음(검증됨)** → 단순 카운트 OK, ROW_NUMBER 불필요.
- agent_uri 형태: `data:application/json;base64,...`(온체인 인라인, 다수·진짜) / `https://...` / `ipfs://...`

### Reputation — NewFeedback  (indexed 3개 → num_topics=4)
| 위치 | 필드 | 디코딩 |
|---|---|---|
| topics[0] | 시그니처 | 필터용 |
| topics[1] | **agent_id** (피평가) | `SAFE_CAST(topics[SAFE_OFFSET(1)] AS INT64)` |
| topics[2] | **client** (평가자) | `CONCAT('0x', SUBSTR(topics[SAFE_OFFSET(2)], 27))` |
| topics[3] | **feedbackURI hash** | 32바이트 해시 — **wash 탐지 골드 (아래 §데이터)** |
| data | score + tags + feedbackURI(평문) + agent card | 아래 |

- score = `SAFE_CAST(CONCAT('0x',SUBSTR(data,67,64)) AS INT64) / POW(10, SAFE_CAST(CONCAT('0x',SUBSTR(data,131,64)) AS INT64))`
- 음수 스킵: `SUBSTR(data,67,1) != 'f'`
- ⚠️ ReputationRegistry에 NewFeedback 외 이벤트 **4종 더 있음**(시그니처 분포에서 5종 확인). 정확한 카운트 시 시그니처 필터 필수.

### agent_uri 디코딩 식 (공통)
```sql
-- data 필드 → 문자열
SAFE_CONVERT_BYTES_TO_STRING(FROM_HEX(SUBSTR(
  data, 131, 2 * SAFE_CAST(CONCAT('0x', SUBSTR(data, 67, 64)) AS INT64))))
-- 온체인 base64 → JSON
SAFE_CONVERT_BYTES_TO_STRING(SAFE.FROM_BASE64(
  SUBSTR(agent_uri, LENGTH('data:application/json;base64,') + 1)))
```

---

## ▶ B. 빌드 계획

### 스택
BigQuery(`google-cloud-bigquery`) + Streamlit. 파티션 컷으로 무료 1TB/월 안에서 충분.

### 1순위 — agent_uri JSON 파싱 (deep-dive 광맥, 여기부터)
온체인 base64(9,520개) 파싱 → 카테고리/스킬/가격/프로토콜 분포 + 분류. **규칙 기반, 모델 불필요.** SQL 안에서 `SAFE.FROM_BASE64`+`JSON_VALUE`/`JSON_QUERY`.
JSON 필드: name, description, **services**(엔드포인트+프로토콜 MCP/A2A/OASF/web/custom), **skills**(OASF 분류), domains, **x402support**, 가격.
분류 초안: services 비고 desc가 PFP류→`NFT/PFP` / name+desc에 'test'→`test_spam` / services에 엔드포인트→`functional` / uri 없음→`no_uri`.

### 뷰 4개
1. **The Real Numbers (헤드라인)** — funnel: 46K 등록 → ~105 평가받음 → payable. 단계별 급감.
2. **Who's Behind It** — owner 집중도(상위 지갑) + 등록 유형 3분류 + agent_class.
3. **What Agents Actually Do** — JSON 파싱 분포(카테고리/스킬/가격/프로토콜).
4. **Reputation, Real or Fake** — client별 피드백 지배도(0x668add) + **feedbackURI 해시 중복**으로 "독립 평가 vs 공유 출처" 폭로 (gist도 못 잡는 차별화).

### 검증된 쿼리 (복붙용)
- **Q1 Adoption**: Identity Registered 일별 COUNT(시그니처 필터 + 파티션 컷).
- **Q2 Decode/Classify**: 위 디코딩 식 + base64 JSON 파싱 + agent_class CASE.
- **Q3 Leaderboard (gist 그대로)**: client=topics[2], score=data, `GROUP BY agent_id HAVING COUNT(DISTINCT client)>=3 ORDER BY avg_score DESC`.
- **Q-client 지배도 (wash 헤드라인)**:
```sql
SELECT
  CONCAT('0x', SUBSTR(topics[SAFE_OFFSET(2)], 27)) AS client,
  COUNT(*) AS feedbacks_given,
  COUNT(DISTINCT SAFE_CAST(topics[SAFE_OFFSET(1)] AS INT64)) AS agents_rated,
  COUNT(DISTINCT topics[SAFE_OFFSET(3)]) AS distinct_feedback_uris
FROM `bigquery-public-data.goog_blockchain_ethereum_mainnet_us.logs`
WHERE address = '0x8004baa17c55a88189ae136b182e5fda19de9b63'
  AND topics[SAFE_OFFSET(0)] = '0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc'
  AND block_timestamp >= TIMESTAMP '2026-01-28'
GROUP BY client ORDER BY feedbacks_given DESC LIMIT 20;
```
- **Q-x402**: Identity base64에서 `JSON_VALUE(json, '$.x402support')` + 분포.

### 나중에 (시간 남으면)
`token_transfers` 조인(x402 주장 vs 실제 결제) / `transactions` 조인(owner liveness=죽은 봇) / `decoded_events`로 손디코딩 대체 가능한지 / Reputation 나머지 4개 이벤트 정체 / https·ipfs uri 오프체인 fetch.

### 제출 체크리스트
BigQuery 코어 ✓(구조상) · EF 주소 ✓ · 경량 프론트=Streamlit ✓ · 데모 영상 · public GitHub+README · 일요일 아침 GCP 부스 + $1K 쿠폰.

---

## ▶ C. 검증된 데이터 인사이트 (= 빌드 스토리, 이미 확정)

- **등록 ~46,000**(Q1 합). 런치 3일 22,695 폭발(1/29:13,446 / 1/30:8,090 / 1/31:1,159)=적체+봇. 이후 baseline 하루 한 자리~수십.
- **owner 집중**: 1위 `0xd5d6d96fa23455ec5e3c00633f85f364d3f5a291` 혼자 **9,967개(21%)**. 2위 1,473 / 3위 779. 상위 20 ≈ 절반.
- **등록 url 3유형**: 봇농장(api.normies.art 1,171/owner1, api.freaks.one 267, exquisites.es 201) / 플랫폼(ag0.xyz 1,985/owner438) / 자체 base64(9,520/owner4,302, 가장 진짜) / null(2,286).
- **agent 다수가 비실체**: PFP NFT(게임 몬스터), `test` 스팸(동일 description 다수), "안전장치 없는 truth machine" 카피 클러스터.
- **funnel**: 46K 등록 → feedback 받은 것 수백 → unique_clients≥3 통과 **~105행(0.2%)** → payable은 그중 일부.
- **x402**: true 10~20% / false 5~10% / **null 70~85%**.
- **wash/Sybil 스모킹건 (RAW 확인)**:
  - client `0x668add9213985e7fd613aec87767c892f4b9df1c`가 수많은 agent에 **전부 score=100** 도배, 그 피드백들의 **feedbackURI 해시 동일**(`0xd2d827af...`).
  - 여러 지갑이 같은 agent(22771)에 몰리며 **feedbackURI 해시 공유**(`0xd6be4ef8...`) = 진짜 Sybil 캠페인.
  - → gist Sybil 배리어(unique_clients≥3)는 **이걸 못 잡음.** 차별화 = **topics[3] 해시 중복 분석**("독립처럼 보이는 평가 중 같은 출처 공유 비율").

---

## ▶ D. 경쟁 스캐너 (8004.org 등재, 전부 확인)

| 스캐너 | 정체성 | 빈틈 |
|---|---|---|
| 8004scan.io (AltLayer) | 소비자 discovery 앱 | 245K 자랑, 품질검증 0 |
| trust8004.xyz | "trust signal" 인덱서(가장 근접) | trust score 얕음(리뷰 1개=100점), analytics는 roadmap |
| agentscan.info (Alias) | OASF taxonomy | discovery 중심, liveness 미검증 |
| 8004agents.ai | explorer+news | 가장 단순 |

공통 약점=빈 칸: 큰 숫자 자랑 / "등록=존재" / logs만 읽음(transactions·token_transfers 미조인) / Sybil·wash 미검증.

---

## ▶ E. 주의 (이전 세션 교훈)
- 과거 오류: (a) 다른 이벤트(openagents) 정보 혼입, (b) Identity/Reputation topic 레이아웃 혼동. → **이 문서 스키마만 신뢰**(전부 raw 검증). 새 사실은 실쿼리/공식 소스로 확인 후 반영.
- 모델: 빌드/코드/SQL은 Opus 충분. 막히는 설계 난제만 Fable 5.
