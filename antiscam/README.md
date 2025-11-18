# FIGMENT - Anti-Scam UPI Transaction Protector

A multi-agent AI system that analyzes UPI transactions in real-time to detect potential scams before users complete payments. Built for hackathon demonstration with explainable AI agents.

## 🎯 Project Overview

FIGMENT uses **4 specialized AI agents** to analyze each transaction from different perspectives:
- **Pattern Agent** 🕵️ - Detects scam text patterns using ML
- **Network Agent** 🕸️ - Checks receiver ID against community scam reports
- **Behavior Agent** 🔍 - Identifies unusual user behavior patterns using anomaly detection
- **Biometric Agent** 🎭 - Monitors typing patterns for signs of pressure

Each agent provides a **risk score with detailed explanations**, and the system combines these scores to give users a clear, actionable warning before completing potentially fraudulent transactions.

## ✨ Recent Enhancements

- **Dynamic Threat Clustering** - Automatically groups similar scam patterns using ML embeddings and clustering algorithms
- **Intelligent Alert System** - Real-time alerts for trending threats, cluster members, and pattern matches
- **Gemini AI Integration** - Generates human-readable explanations with threat intelligence context
- **Real-time Dashboard** - Shows analytics with data from MongoDB, refreshes every 5 minutes
- **WebSocket Updates** - Real-time transaction analysis results and threat alerts
- **Improved Dark Mode** - Consistent styling across all components

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
- Google Generative AI for Gemini integration

**ML Models:**
- Pattern Agent: sklearn Pipeline (TF-IDF + Logistic Regression)
- Behavior Agent: sklearn IsolationForest (Anomaly Detection)

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
# Add your MongoDB connection string and Gemini API key:
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
DB_NAME=AntiScam
GEMINI_API_KEY=your_gemini_api_key_here
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

## 🧠 Gemini AI Integration

**Purpose:** Generates 2-3 human-readable summaries explaining why a transaction was flagged as a scam

**How it works:**
- Receives transaction details and individual agent scores
- **Includes threat intelligence data** (trending threats, cluster matches, historical reports)
- Creates contextual prompts for Gemini with full threat context
- Returns simple, actionable explanations that mention threat intelligence when available
- Falls back gracefully if API key is not configured

**Threat Intelligence Context:**
- If receiver is in trending threats → Explains report count and threat score
- If receiver is in a known cluster → Mentions cluster name and pattern
- If message matches a scam pattern → Describes pattern similarity and history

---

## 📊 Real-time Dashboard

**Features:**
- Real analytics data from MongoDB
- Auto-refresh every 5 minutes
- Transaction history tracking
- Scam prevention metrics
- Risk distribution visualization
- **Threat Intelligence Hub** - Shows top 5 scam clusters and trending threats

---

## 🔌 API Endpoints

### `POST /api/analyze`
Analyze a transaction through all agents

**Response includes:**
- Individual agent scores
- Overall risk assessment
- AI-generated explanation (Gemini)
- **Threat intelligence data** (trending threats, cluster matches, cluster members)

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

### `GET /api/user-analytics`
Get user analytics data

---

### `GET /api/global-analytics`
Get global analytics data

---

### `GET /api/threat-intel/global`
Get trending threats and scam clusters

**Response:**
- Top 5 trending threats (receivers with ≥5 reports)
- Top 5 active scam clusters

---

### `GET /api/threat-intel/clusters`
Get all active scam clusters (top 5 by average threat score)

---

### `GET /health`
Health check endpoint

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

3. **Threat Intelligence Check:**
   - Checks if receiver is in trending threats
   - Checks if receiver is a cluster member
   - Checks if message matches a known scam pattern
   - Sends real-time alerts via WebSocket

4. **Gemini AI generates explanation:**
   - Human-readable summary of risk factors
   - **Includes threat intelligence context** (trending threats, clusters, patterns)
   - Simple language for non-technical users

5. **Results displayed:**
   - Overall risk score
   - Individual agent scores
   - Detailed explanations
   - Evidence for each agent
   - AI-generated summary
   - **Threat intelligence alerts** (if applicable):
     - 🚨 Trending threat detected
     - ⚠️ Known scam cluster member
     - ⚠️ Scam pattern match

6. **User decides:**
   - **Cancel** → Transaction cancelled
   - **Proceed Anyway** → Warning dialog → PIN entry → Transaction completes

7. **After completion:**
   - Feedback modal appears (always shown, regardless of risk)
   - User confirms if it was actually a scam
   - If yes → Scam count incremented in database
   - Transaction data used to update threat intelligence and clusters

---

## 🔧 Configuration

### Backend Environment Variables

Create `Backend/.env`:
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
DB_NAME=figment
GEMINI_API_KEY=your_gemini_api_key_here
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
✅ **Dynamic Threat Clustering** - Automatically groups similar scam patterns using ML
✅ **Intelligent Alert System** - Real-time alerts for trending threats and cluster matches
✅ **Gemini AI Explanations** - Human-readable fraud summaries with threat intelligence context
✅ **Real-Time Analysis** - Instant risk assessment before payment
✅ **Community Intelligence** - Crowd-sourced scam database
✅ **Behavior Learning** - Adapts to user's normal patterns
✅ **Feedback Loop** - Users help improve the system
✅ **PIN Confirmation** - Extra step for high-risk transactions
✅ **Transaction History** - Track all analyzed transactions
✅ **Real-time Dashboard** - Live analytics with MongoDB data
✅ **Threat Intelligence Hub** - View trending threats and scam clusters

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
- **Gemini AI:** Requires API key for fraud explanations
- **Fallback Systems:** All agents have rule-based fallbacks if models unavailable

---

## 📚 Additional Resources

- **Models:** Place trained `.pkl` files in `Backend/models/`
- **Database:** Run `seed_scam_data.py` to populate sample scam data
- **API Docs:** See inline comments in `Backend/app.py`
- **Frontend Docs:** See `Frontend/src/services/api.js`

---

**Ready to demo!** 🚀