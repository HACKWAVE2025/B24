# FIGMENT – Internal Systems Guide

This document is the internal-facing reference for engineers maintaining the FIGMENT Anti-Scam stack. It complements the public-facing `README.md` with lower-level architecture notes, deployment requirements, and the complete API surface (REST + WebSocket).

---

## 1. Tech Stack & Dependencies

**Frontend**
- React (CRA), React Router DOM, TailwindCSS, shadcn/ui, Framer Motion
- State helpers: custom hooks + Context, Axios for HTTP, Socket.IO client for realtime alerts
- Build tooling: Vite-style scripts via CRA, ESLint + Prettier

**Backend**
- Python 3.10+, Flask + Flask-CORS, Flask-SocketIO (threading mode)
- MongoDB via `pymongo`
- Agents:
  - Pattern Agent → sklearn Pipeline (TF-IDF + LogisticRegression, fallback keywords)
  - Network Agent → Mongo-backed heuristics (scam report counts + CTIH fusion)
  - Behavior Agent → sklearn IsolationForest
  - Biometric Agent → rule-based (typing speed + hesitation)
- Background services: `AlertService` (trending/cluster alerts), `TransactionService`, `ThreatIntelService` (CTIH + dynamic clustering), `GeminiService` (with threat intel context)
- Serialization: `joblib`, `pickle`

**Infra & Tooling**
- MongoDB Atlas (or local Mongo) database `AntiScam`
- `.env` driven config via `python-dotenv`
- Model artifacts stored under `Backend/models/`
- Feedback datasets stored under `Backend/data/`
- Optional Google OAuth (Client ID/Secret + redirect URI)

---

## 2. Repository Layout

```
B24/antiscam/
├── Backend/
│   ├── agents/                # ML + rule-based agents + retrain scripts
│   ├── data/                  # CSV datasets, counters, feedback logs
│   ├── database/              # Mongo connector helper
│   ├── routes/                # Auth + threat intel blueprints
│   ├── services/              # Alert, Gemini, transaction analytics, CTIH
│   ├── utils/                 # Auth helpers, score aggregation
│   └── app.py                 # Flask + Socket.IO entrypoint
├── Frontend/                  # React client (dashboard + capture form)
└── README.md                  # Public overview
```

---

## 3. Runtime Architecture

1. **Auth layer** issues JWTs (`utils.auth`) and exposes email/password plus Google OAuth routes via `routes/auth.py`.
2. **Flask app** (`Backend/app.py`) boots all four agents, Mongo connection, background services, the new Central Threat Intelligence Hub (CTIH), and Socket.IO server.
3. **Transaction intake** hits `/api/analyze`, invokes each agent with the enriched transaction payload, feeds outputs into CTIH, checks for trending threats/cluster matches, sends alerts, aggregates scores, and optionally asks Gemini for natural-language explanations (with threat intel context).
4. **CTIH fusion** (`ThreatIntelService`) normalizes agent outputs, updates the `threat_intel` collection, produces receiver-level threat scores, refreshes clusters, and shares the intel payload with the response + sockets.
5. **Real-time UX**: `TransactionService` broadcasts analyses and alerts to the requesting user’s private Socket.IO room; `AlertService` streams generic safety alerts plus CTIH-driven `threat_intel_alert` pushes.
6. **Feedback loop**: `/api/feedback` stores user confirmations, appends CSV rows, and triggers automatic retraining once CSV rows ≥ 10 for either Behavior or Pattern agents.
7. **Analytics + history** endpoints query Mongo collections and cached aggregates to power the dashboard views.

---

## 4. Central Threat Intelligence Hub (CTIH)

- Implemented in `services/threat_intel_service.py`.
- Aggregates every agent response + transaction metadata, storing normalized metrics such as `avg_agent_risk`, `velocity_score`, and `pattern_flags` inside the `threat_intel` collection.
- Persists raw agent outputs per transaction in `threat_intel_events` to enable historical timelines.
- **Dynamic Clustering**: Automatically groups similar scam patterns using ML embeddings and Agglomerative clustering (see `DYNAMIC_CLUSTERING_README.md`).
- Maintains derived scam clusters inside `dynamic_clusters` collection (replaces `threat_clusters`).
- Provides helper APIs for `/api/analyze`, the Network Agent, AlertService, and the new threat-intel REST endpoints.
- **Alert Detection**: Checks for trending threats, cluster members, and pattern matches during analysis.
- Weighted threat score (0-100) feeds back into the main risk output (`overallRisk` now blends 70% agent aggregate + 30% CTIH score).
- Emits structured intel (`threatIntel` object) in every analysis response and socket payload, including:
  - `trendingThreat`: If receiver is in top trending threats (≥5 reports)
  - `clusterMember`: If receiver is part of a known cluster
  - `clusterMatch`: If transaction message matches a cluster pattern

---

## 4. Agents & Retraining

| Agent | Source | Core Inputs | Detection Logic | Retraining |
|-------|--------|-------------|-----------------|------------|
| Pattern (`agents/pattern_agent.py`) | Text (reason + receiver) | TF-IDF + LogisticRegression pipeline; fallback keyword list | Manual via `agents/retrain_pattern_manual.py`, dataset `data/pattern_data.csv` |
| Network (`agents/network_agent.py`) | Mongo `scam_reports` + CTIH | Counts of reports per receiver, heuristics for risk scaling, max fusion with CTIH score. Uses trending threats data (top 5 with ≥5 reports). | No ML; live counts |
| Behavior (`agents/behavior_agent.py`) | Numeric features (amount, hour, frequency, day_of_week, delta_hours) | IsolationForest anomaly scoring, rule-based fallback | Auto when `data/behavior_feedback.csv` ≥ 10 rows via `_retrain_from_csv`; manual via `agents/retrain_behavior_manual.py` |
| Biometric (`agents/biometric_agent.py`) | Typing speed, hesitation count | Rule set for pressure or hesitation anomalies | Not ML |

**Feedback data flow**
- `/api/feedback` ➜ Mongo `feedback` collection (for audit) + CSV appenders (`behavior_feedback.csv`, `pattern_feedback.csv`) using file locks.
- Counter ≥ 10 ➜ executes respective retrain helper, overwriting `models/behavior_iforest.pkl` or `models/pattern_agent_tiny.pkl`.
- `BehaviorAgent.reload_model()` utility is available if hot-reload is required without restarting Flask.

---

## 5. Configuration & Secrets

Create `Backend/.env`:

```
MONGODB_URI=mongodb+srv://...
DB_NAME=AntiScam
GEMINI_API_KEY=...
JWT_SECRET=...
FRONTEND_URL=http://localhost:3000
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
```

Frontend optional `Frontend/.env`:

```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_SOCKET_URL=http://localhost:5000
```

---

## 6. REST API Surface

### Authentication (`routes/auth.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/signup` | ❌ | Email/password signup, stores hashed password |
| POST | `/api/auth/login` | ❌ | Email/password login, returns JWT |
| GET  | `/api/auth/google/redirect` | ❌ | Initiate Google OAuth |
| GET  | `/api/auth/google/callback` | ❌ | OAuth callback, issues JWT + redirects to frontend |
| GET  | `/api/auth/me` | ✅ | Return profile for JWT subject |
| POST | `/api/auth/verify` | ❌ | Validate JWT payload |

### Core Transaction Flow (`Backend/app.py`)

| Method | Path | Auth | Handler | Notes |
|--------|------|------|---------|-------|
| POST | `/api/analyze` | ✅ | `analyze_transaction` | Requires `receiver`, `amount`. Runs all agents, returns per-agent breakdown + overall risk + optional Gemini explanation. Emits Socket.IO event via `TransactionService`. |
| POST | `/api/report` | ✅ | `report_scam` | Crowd-sourced receiver report; increments Mongo `scam_reports` with reason + reporter IDs. |
| GET  | `/api/history` | ✅ | `get_history` | Latest 20 transactions for the caller (legacy). |
| POST | `/api/complete-transaction` | ✅ | `complete_transaction` | Persists finalized transaction with risk context. |
| POST | `/api/feedback` | ✅ | `submit_feedback` | Records user feedback, drives retraining CSVs (behavior + pattern). |
| GET  | `/api/transaction-history` | ✅ | `get_transaction_history` | Same as `/api/history` but supports `limit` query param. |
| GET  | `/api/user-analytics` | ✅ | `get_user_analytics` | Returns personalized metrics from `TransactionService`. |
| GET  | `/api/global-analytics` | ❌ | `get_global_analytics` | Aggregated metrics (system-wide). |
| GET  | `/health` | ❌ | `health` | Simple readiness probe. |

> **JWT notes:** `token_required` decorator injects `request.current_user` and short-circuits with `401` when missing or invalid.

### Threat Intelligence Hub (`routes/threat_intel.py`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/threat-intel/receiver/<receiver>` | ✅ | Snapshot + history for a receiver, powered by CTIH. |
| GET | `/api/threat-intel/global` | ✅ | Returns top 5 trending receivers (≥5 reports) + top 5 active scam clusters. |
| GET | `/api/threat-intel/clusters` | ✅ | Returns top 5 active clusters sorted by average threat score. |

### Supporting Data Collections

- `users` – auth records (email/password hash, google_id, metadata)
- `transactions` – persisted analyzed/completed transactions
- `scam_reports` – receiver report counts for Network Agent
- `feedback` – structured user feedback (scam confirmation + comments)
- `user_behavior` – maintained per-user behavior stats for Behavior Agent feature extraction
- `threat_intel` – CTIH receiver scores + aggregates
- `threat_intel_events` – agent output history for CTIH forensic timelines
- `dynamic_clusters` – ML-generated scam clusters (replaces `threat_clusters`)

---

## 7. WebSocket Events (Socket.IO)

| Event | Direction | Payload | Purpose |
|-------|-----------|---------|---------|
| `connect` | Server ➜ Client | `{ status: 'connected' }` | Confirmation + triggers initial alert |
| `request_alerts` | Client ➜ Server | `{}` | Forces server to emit first alert immediately |
| `alerts_enabled` | Server ➜ Client | `{ status: 'enabled' }` | Confirms alert channel |
| `join_user_room` | Client ➜ Server | `{ user_id }` | Subscribes to private `user_{id}` room for realtime transaction updates |
| `leave_user_room` | Client ➜ Server | `{ user_id }` | Unsubscribes |
| `request_recent_transactions` | Client ➜ Server | `{ user_id, limit? }` | Asks for recent transactions (server replies with `recent_transactions`) |
| `recent_transactions` | Server ➜ Client | `{ transactions: [...] }` | Snapshot for dashboard ticker |
| `analysis_result` *(emitted via `TransactionService`)* | Server ➜ User room | `{ overallRisk, aiExplanation, agents, threatIntel, transaction }` | Mirrors `/api/analyze` response for realtime UI |
| `threat_intel_alert` *(via `AlertService.push_threat_alerts`)* | Server ➜ All | `{ type: 'threat_intel', threats: [...] }` | Broadcasts trending receivers & pattern flags from CTIH. |
| `trending_threat_alert` *(via `AlertService.send_trending_threat_alert`)* | Server ➜ All | `{ type: 'trending_threat', trending: {...}, message: '...' }` | Alert when receiver is in top trending threats (≥5 reports). |
| `cluster_member_alert` *(via `AlertService.send_cluster_member_alert`)* | Server ➜ All | `{ type: 'cluster_member', cluster: {...}, message: '...' }` | Alert when receiver is a member of a known scam cluster. |
| `cluster_match_alert` *(via `AlertService.send_cluster_match_alert`)* | Server ➜ All | `{ type: 'cluster_match', cluster: {...}, message: '...' }` | Alert when transaction message matches a known scam pattern. |

`AlertService` also streams generic scam-awareness alerts on an interval once `start()` is called during Flask boot, and can proactively push CTIH-driven alerts when high threat scores surface.

---

## 8. Development & Maintenance Tips

- **Initial setup**
  - Install Python deps: `pip install -r Backend/requirements.txt`
  - Install frontend deps: `npm install` inside `Frontend`
  - Seed Mongo with minimal `users`, `scam_reports` if needed (scripts under `Backend/scripts/`)
- **Hot reloading agents**: restart Flask or call the agent’s `reload_model()` after copying new `.pkl`.
- **Manual retraining**
  - Behavior: `python Backend/agents/retrain_behavior_manual.py`
  - Pattern:  `python Backend/agents/retrain_pattern_manual.py`
- **CSV hygiene**: corrupted CSVs trigger `_fix_corrupted_csv` which backs up `.backup` files before cleanup.
- **Realtime debugging**: run backend with `socketio.run(..., debug=True)` (default). Frontend listens on `window.env.REACT_APP_SOCKET_URL`.
- **Threat Intel dashboard (optional)**: expose CTIH metrics in the dashboard via a “Threat Intelligence Hub” section using the new REST endpoints and Socket.IO `threat_intel_alert` stream.

---

## 9. Future Hardening Ideas

- Persist model metadata (train timestamp, dataset size) in Mongo for observability.
- Promote `/api/history` and `/api/transaction-history` into a single versioned endpoint.
- Add automated pattern-agent retraining via scheduler instead of CSV thresholds only.
- Expand analytics endpoints with pagination + caching.

---

For any updates, keep this file synchronized with code changes so internal teams always have a single source of truth for operational details.

