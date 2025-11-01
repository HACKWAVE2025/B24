# FIGMENT - Anti-Scam UPI Transaction Protector

A multi-agent AI system that analyzes UPI transactions in real-time to detect potential scams before users complete payments. Built for hackathon demonstration with explainable AI agents.

## 🎯 Project Overview

FIGMENT uses **4 specialized AI agents** to analyze each transaction from different perspectives:
- **Pattern Agent** 🕵️ - Detects scam text patterns using ML
- **Network Agent** 🕸️ - Checks receiver ID against community scam reports
- **Behavior Agent** 🔍 - Identifies unusual user behavior patterns using anomaly detection
- **Biometric Agent** 🎭 - Monitors typing patterns for signs of pressure

Each agent provides a **risk score with detailed explanations**, and the system combines these scores to give users a clear, actionable warning before completing potentially fraudulent transactions.

---

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- React + Create React App
- TailwindCSS for styling
- Framer Motion for animations
- shadcn/ui components
- Axios for API calls
- React Router DOM for navigation
- Sonner for toast notifications

**Backend:**
- Flask (Python)
- Flask-CORS for cross-origin requests
- MongoDB for data storage
- scikit-learn for ML models
- joblib for model loading

**ML Models:**
- Pattern Agent: sklearn Pipeline (TF-IDF + Logistic Regression)
- Behavior Agent: sklearn IsolationForest (Anomaly Detection)

---

## 📁 Project Structure

```
antiscam/
├── Frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # UI components
│   │   │   ├── ui/          # shadcn/ui components
│   │   │   ├── AgentCard.js
│   │   │   ├── ResultsModal.js
│   │   │   ├── PINEntry.js
│   │   │   ├── FeedbackModal.js
│   │   │   └── ...
│   │   ├── pages/           # Page components
│   │   │   ├── DemoPage.js  # Main transaction demo
│   │   │   ├── DashboardPage.js
│   │   │   └── ...
│   │   ├── services/        # API service layer
│   │   │   └── api.js       # Centralized API calls
│   │   └── ...
│   └── package.json
│
├── Backend/                  # Flask backend API
│   ├── agents/              # AI agent implementations
│   │   ├── pattern_agent.py      # Text pattern detection
│   │   ├── network_agent.py       # Community reports check
│   │   ├── behavior_agent.py      # Anomaly detection
│   │   └── biometric_agent.py     # Typing pattern analysis
│   ├── database/
│   │   └── db.py            # MongoDB connection
│   ├── models/              # Trained ML models
│   │   ├── pattern_agent_tiny.pkl
│   │   └── behavior_iforest.pkl
│   ├── utils/
│   │   └── score_aggregator.py   # Combines agent scores
│   ├── app.py               # Flask application & API routes
│   └── requirements.txt
│
└── README.md                # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v16+)
- **Python** (3.8+)
- **MongoDB Atlas account** (or local MongoDB)

### 1. Backend Setup

```bash
cd Backend

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Add your MongoDB connection string:
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
DB_NAME=AntiScam
```

**Place ML Models:**
- Download trained models from Colab
- Place `pattern_agent_tiny.pkl` and `behavior_iforest.pkl` in `Backend/models/`

**Seed Sample Scam Data (Optional):**
You can manually add scam reports through the `/api/report` endpoint or by directly inserting into MongoDB `scam_reports` collection.

**Start Backend:**
```bash
python app.py
```
Backend runs on `http://localhost:5000`

### 2. Frontend Setup

```bash
cd Frontend

# Install dependencies
npm install

# Start development server
npm start
```
Frontend runs on `http://localhost:3000`

---

## 🤖 AI Agents Explained

### 1. Pattern Agent 🕵️
**Purpose:** Detects known scam text patterns in transaction messages

**How it works:**
- Uses TF-IDF vectorization + Logistic Regression
- Trained on scam text datasets
- Analyzes: transaction reason/message + receiver UPI ID
- Returns: Risk score (0-100%) with detected patterns

**Model:** `pattern_agent_tiny.pkl` (sklearn Pipeline)

---

### 2. Network Agent 🕸️
**Purpose:** Checks if receiver ID has been reported as a scammer

**How it works:**
- Queries MongoDB `scam_reports` collection
- Uses crowd-sourced intelligence from user reports
- Risk calculation based on report count:
  - 10+ reports → 95% risk
  - 5-9 reports → 80% risk
  - 2-4 reports → 60% risk
  - 1 report → 40% risk
  - 0 reports → 10% risk

**No ML Model Required** - Pure database queries

---

### 3. Behavior Agent 🔍
**Purpose:** Detects anomalies in user's transaction behavior

**How it works:**
- Uses IsolationForest anomaly detection
- Analyzes 5 features:
  - `amount` - Transaction amount
  - `hour` - Hour of day (0-23)
  - `frequency` - Transaction frequency
  - `day_of_week` - Day of week (0-6)
  - `delta_hours` - Hours since last transaction
- Learns user's normal patterns
- Flags unusual transactions

**Model:** `behavior_iforest.pkl` (sklearn IsolationForest)

---

### 4. Biometric Agent 🎭
**Purpose:** Monitors typing patterns for signs of pressure/rushing

**How it works:**
- Analyzes typing speed (WPM)
- Tracks hesitation/correction count
- Detects rapid input (scammer pressure)
- Detects excessive hesitation (uncertainty)

**No ML Model Required** - Rule-based analysis

---

## 📊 Score Aggregation

The system combines all 4 agent scores:
- **Weighted Average:** Different weights for each agent
- **Overall Risk Score:** 0-100%
- **Risk Levels:**
  - 70%+ → High Risk (Red warning)
  - 40-69% → Medium Risk (Orange warning)
  - <40% → Low Risk (Green)

---

## 🔌 API Endpoints

### `POST /api/analyze`
Analyze a transaction through all agents

---

### `POST /api/report`
Report a scammer to the network

---

### `POST /api/complete-transaction`
Save completed transaction to history

---

### `POST /api/feedback`
Submit feedback after transaction


**Note:** If `was_scam: true`, increments scam count in network database

---

### `GET /api/history/<user_id>`
Get transaction history for a user

---

### `GET /health`
Health check endpoint

---

---

## 🎨 User Flow

1. **User enters transaction details:**
   - UPI ID (receiver)
   - Amount
   - Message/Reason
   - Optional: Time, typing speed

2. **System analyzes through 4 agents:**
   - Pattern Agent checks text
   - Network Agent queries database
   - Behavior Agent checks user patterns
   - Biometric Agent analyzes input behavior

3. **Results displayed:**
   - Overall risk score
   - Individual agent scores
   - Detailed explanations
   - Evidence for each agent

4. **User decides:**
   - **Cancel** → Transaction cancelled
   - **Proceed Anyway** → Warning dialog → PIN entry → Transaction completes

5. **After completion (if risk ≥ 40%):**
   - Feedback modal appears
   - User confirms if it was actually a scam
   - If yes → Scam count incremented in database

---

## 🔧 Configuration

### Backend Environment Variables

Create `Backend/.env`:
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
DB_NAME=figment
```

### Frontend Environment Variables

Create `Frontend/.env` (optional):
```env
REACT_APP_API_URL=http://localhost:5000
```

---

## 📝 Key Features

✅ **Multi-Agent AI System** - 4 specialized agents analyzing different aspects
✅ **Explainable AI** - Each agent provides detailed reasoning
✅ **Real-Time Analysis** - Instant risk assessment before payment
✅ **Community Intelligence** - Crowd-sourced scam database
✅ **Behavior Learning** - Adapts to user's normal patterns
✅ **Feedback Loop** - Users help improve the system
✅ **PIN Confirmation** - Extra step for high-risk transactions
✅ **Transaction History** - Track all analyzed transactions

---

## 🎯 Use Cases

- **Prevent Loan Scams** - Detect fake loan offers
- **Stop Phishing** - Identify suspicious payment requests
- **Catch Impersonation** - Flag fake customer support
- **Block Ponzi Schemes** - Detect investment scams
- **Warn on Unusual Activity** - Alert on abnormal transactions

---

## 🛠️ Development

### Backend Development
```bash
cd Backend
python app.py  # Runs on http://localhost:5000
```

### Frontend Development
```bash
cd Frontend
npm start  # Runs on http://localhost:3000
```
---

## 📄 License

Built for hackathon demonstration purposes.

---

## 👥 Team

**Project:** FIGMENT - Anti-Scam UPI Transaction Protector  
**Event:** Hackathon 2024  
**Stack:** React + Flask + MongoDB + ML

---

## 🚨 Important Notes

- **Demo Purpose:** This is a prototype for hackathon demonstration
- **ML Models:** Requires trained models placed in `Backend/models/`
- **MongoDB:** Requires connection string in `.env` file
- **Fallback Systems:** All agents have rule-based fallbacks if models unavailable

---

## 📚 Additional Resources

- **Models:** Place trained `.pkl` files in `Backend/models/`
- **Database:** Run `seed_scam_data.py` to populate sample scam data
- **API Docs:** See inline comments in `Backend/app.py`
- **Frontend Docs:** See `Frontend/src/services/api.js`

---

**Ready to demo!** 🚀

