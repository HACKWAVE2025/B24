# Dynamic Threat Clustering System

## Overview

The Dynamic Threat Clustering System is an advanced, self-learning feature that automatically discovers and groups similar scam patterns in real-time. Unlike static rule-based categorization, this system uses machine learning embeddings and clustering algorithms to identify emerging scam trends organically, helping security teams stay ahead of evolving threats.

## Table of Contents

1. [What is Dynamic Clustering?](#what-is-dynamic-clustering)
2. [How It Works](#how-it-works)
3. [Key Features](#key-features)
4. [Technical Architecture](#technical-architecture)
5. [Impact on AI Agents](#impact-on-ai-agents)
6. [Configuration](#configuration)
7. [API Endpoints](#api-endpoints)
8. [Best Practices](#best-practices)

---

## What is Dynamic Clustering?

Dynamic clustering automatically groups scam transactions that share similar patterns, messages, or characteristics into **clusters**. Each cluster represents a distinct scam type or campaign, such as:

- **Loan Scams**: "Urgent loan with 0% interest", "Instant loan approval"
- **OTP Scams**: "Verify your account with OTP", "KYC verification required"
- **Fake Job Scams**: "Work from home opportunity", "High salary job offer"
- **Investment Scams**: "Invest in crypto, get high returns", "Stock trading opportunity"

### Why Dynamic?

- **Self-Learning**: Discovers new scam patterns without manual rules
- **Adaptive**: Automatically adjusts as new scam types emerge
- **Pattern Recognition**: Groups scams by semantic similarity, not just keywords
- **Real-Time**: Updates clusters as new transactions are analyzed

---

## How It Works

### 1. Data Collection

Every time a transaction is analyzed by the AI agents, the system records:
- **Transaction message/reason**: The text content of the transaction
- **Pattern flags**: Keywords detected by the Pattern Agent (e.g., "loan", "urgent", "verify")
- **Agent risk scores**: Scores from all 4 AI agents (Pattern, Network, Behavior, Biometric)
- **Receiver UPI ID**: The destination account
- **Threat score**: Overall risk assessment

### 2. Feature Vector Generation

For each transaction, the system creates a **feature vector** (~520 dimensions) combining:

```
Feature Vector = [Text Embedding] + [Pattern Keywords] + [Agent Scores]
```

- **Text Embedding** (~384 dims): Uses `BAAI/bge-small-en-v1.5` model to convert transaction messages into semantic vectors
- **Pattern Keywords** (128 dims): Hash-based encoding of detected scam keywords
- **Agent Scores** (8 dims): Normalized risk scores from all agents

### 3. Clustering Algorithm

Uses **Agglomerative Hierarchical Clustering** with:
- **Distance Threshold**: 4.0 (clusters within this distance are merged)
- **Minimum Cluster Size**: 3 receivers (prevents noise from single reports)
- **Linkage Method**: Ward (minimizes variance within clusters)

### 4. Cluster Naming

Automatically generates human-readable names using **TF-IDF** (Term Frequency-Inverse Document Frequency):
- Extracts most distinctive keywords from cluster members
- Creates names like "Urgent / Loan / Upi" or "Otp / Account / Verify"

### 5. Smart Merging

The system intelligently merges similar clusters to prevent duplicates:

#### Payment Keyword Normalization
- Treats payment-related terms as equivalent: `upi`, `emi`, `paytm`, `pay`, `payment`
- Example: "Loan/Urgent/UPI" and "Loan/Urgent/EMI" merge into one cluster

#### Multi-Pass Merging
1. **First Pass**: Merges clusters with identical normalized keywords
2. **Second Pass**: Merges clusters with ≥40% keyword overlap or ≥70% centroid similarity
3. **Final Pass**: Catches any remaining similar clusters after merging new and existing data

#### Merge Criteria
- **Identical keywords** (100% match) → Always merge
- **High similarity** (≥40% keyword overlap OR ≥70% centroid similarity) → Merge
- **Core scam keywords** (≥2 shared keywords like "loan" + "urgent") → Merge
- **Name similarity** (≥67% name word overlap with keyword match) → Merge

### 6. Lifecycle Management

Clusters are automatically managed:
- **Active**: Clusters with ≥3 receivers and updated within 30 days
- **Inactive**: Clusters that are too small or haven't been updated recently
- **Emerging**: Large groups of noise samples that may become new clusters

---

## Key Features

### 🎯 Pattern-Based Grouping
Clusters are formed based on **message content and patterns**, not just receiver IDs. This means:
- Different receivers using the same scam script are grouped together
- Same organization's scam campaigns are automatically identified
- New scam variations are detected even with different wording

### 🔄 Automatic Updates
- Clusters refresh automatically after every 10 new transactions
- Can be force-refreshed via API or service method
- Only top 5 clusters (by average threat score) are shown in the frontend

### 📊 Trending Analysis
- Tracks which scam types are most active
- Shows average threat scores per cluster
- Displays receiver counts and top keywords

### 🧹 Duplicate Prevention
- Prevents duplicate clusters with same/similar patterns
- Merges clusters across different refresh cycles
- Maintains cluster stability while allowing evolution

---

## Technical Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│           Threat Intelligence Service                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Dynamic Cluster Engine                          │  │
│  │  - Feature Vector Generation                     │  │
│  │  - Agglomerative Clustering                      │  │
│  │  - Cluster Naming (TF-IDF)                       │  │
│  │  - Smart Merging Logic                           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Data Sources                                     │  │
│  │  - threat_intel_events (transaction history)     │  │
│  │  - threat_intel (receiver snapshots)             │  │
│  │  - dynamic_clusters (cluster storage)            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Transaction Analysis** → AI agents analyze transaction
2. **Event Recording** → Stored in `threat_intel_events` collection
3. **Threshold Check** → After 10 events, trigger cluster refresh
4. **Feature Extraction** → Generate vectors from last 600 events
5. **Clustering** → Run Agglomerative clustering algorithm
6. **Merging** → Merge similar clusters (3 passes)
7. **Storage** → Save to `dynamic_clusters` collection
8. **API Exposure** → Frontend displays top 5 clusters

### Database Collections

- **`threat_intel_events`**: Raw transaction analysis results with agent outputs
- **`threat_intel`**: Aggregated threat scores per receiver
- **`dynamic_clusters`**: Generated scam clusters with metadata

---

## Impact on AI Agents

### ✅ Positive Impacts

#### 1. **Network Agent Enhancement**
The Network Agent uses cluster data to improve threat detection:

```python
# Network Agent checks cluster context
cti_score = threat_intel_service.get_receiver_threat_score(receiver)
```

**How it helps:**
- If a receiver belongs to a known scam cluster, the Network Agent can boost its risk score
- Provides context about scam type (loan, OTP, etc.) for better decision-making
- Helps identify new receivers that match existing scam patterns
- Uses trending threats data (top 5 receivers with ≥5 reports)

#### 2. **Real-Time Alert System**
Clusters enable intelligent alerting:

- **Trending Threat Alerts**: When receiver is in top trending threats (≥5 reports)
- **Cluster Member Alerts**: When receiver is part of a known scam cluster
- **Pattern Match Alerts**: When transaction message matches a cluster pattern (70% similarity threshold with keyword fallback)

**Alert Priority:**
1. Trending Threat (highest priority - red alert)
2. Cluster Member (orange alert)
3. Pattern Match (orange alert, only if not already a member)

#### 3. **Gemini AI Integration**
Clusters provide context for AI-generated explanations:

- Gemini receives threat intelligence data in prompts
- Explains why receiver is trending or part of a cluster
- Mentions pattern matches and historical report counts
- Makes explanations more informative and actionable

#### 4. **Pattern Recognition Feedback Loop**
- Clusters reveal which patterns are most common
- Helps agents learn which keywords/patterns are most indicative of scams
- Can inform future pattern detection improvements

#### 5. **Threat Score Aggregation**
- Cluster average scores provide baseline threat levels
- Individual transactions can be compared against cluster norms
- Helps identify outliers and emerging threats

### ⚠️ Important Notes

#### **No Direct Agent Modification**
- Clusters **do not directly modify** agent behavior or training
- Agents continue to work independently based on their own models
- Clustering is a **post-analysis** feature for threat intelligence

#### **Indirect Benefits**
- **Better Context**: Agents can reference cluster data for additional context
- **Real-Time Alerts**: Users get immediate warnings about known threats
- **Trend Analysis**: Helps identify which scam types are trending
- **User Education**: Frontend shows users which scam types are active
- **Enhanced Explanations**: Gemini AI includes threat intel in explanations

#### **Current Integration**
- ✅ Alert system uses clusters for real-time warnings
- ✅ Gemini AI receives cluster data in prompts
- ✅ Network Agent uses trending threats data
- ✅ Frontend displays cluster information in results modal

---

## Configuration

### Environment Variables

No special environment variables required. The system uses:
- MongoDB connection from `MONGODB_URI`
- Default database name: `AntiScam`

### Tuning Parameters

In `DynamicClusterEngine.__init__()`:

```python
min_cluster_size: int = 3          # Minimum receivers per cluster
similarity_threshold: float = 0.85  # For merging existing clusters
distance_threshold: float = 4.0     # Agglomerative clustering threshold
```

In `ThreatIntelService.__init__()`:

```python
cluster_refresh_threshold: int = 10  # Refresh after N transactions
```

### Embedding Model

- **Model**: `BAAI/bge-small-en-v1.5`
- **Size**: ~90MB (downloads on first use)
- **Purpose**: Converts transaction text to semantic vectors
- **Language**: English-optimized

---

## API Endpoints

### Get All Clusters (Top 5)

```http
GET /api/threat-intel/clusters
Authorization: Bearer <token>
```

**Response:**
```json
{
  "clusters": [
    {
      "clusterId": "uuid",
      "name": "Urgent / Loan / Upi",
      "members": ["receiver1@upi", "receiver2@paytm"],
      "avgScore": 65.5,
      "count": 12,
      "topKeywords": ["urgent", "loan", "upi"],
      "active": true,
      "updatedAt": "2025-11-17T10:00:00Z"
    }
  ]
}
```

### Get Global Threat Intel (Includes Clusters)

```http
GET /api/threat-intel/global
Authorization: Bearer <token>
```

**Response:**
```json
{
  "trending": [...],
  "clusters": [...]
}
```

### Force Cluster Refresh (Internal)

```python
from services.threat_intel_service import ThreatIntelService

service = ThreatIntelService()
service.refresh_dynamic_clusters(force=True)
```

---

## Best Practices

### 1. **Monitor Cluster Quality**
- Check that clusters make semantic sense
- Verify that similar scams are grouped together
- Review cluster names for accuracy

### 2. **Regular Refresh**
- Clusters auto-refresh after 10 transactions
- Force refresh after bulk data imports
- Monitor cluster counts to ensure proper merging

### 3. **Keyword Normalization**
- Payment keywords (UPI/EMI) are automatically normalized
- Add new equivalent terms to `payment_keywords` set if needed
- Core scam keywords are prioritized in merging logic

### 4. **Performance Considerations**
- Clustering runs on last 600 events (configurable)
- Embedding model loads once and stays in memory
- Refresh is triggered asynchronously to avoid blocking

### 5. **Frontend Display**
- Only top 5 clusters are shown (sorted by avgScore)
- Inactive clusters are filtered out
- Use cluster keywords for filtering/search

---

## Example Use Cases

### Use Case 1: Identifying Scam Campaigns
**Scenario**: Multiple users report different UPI IDs with similar loan scam messages.

**Result**: System automatically groups them into "Loan / Urgent / Upi" cluster, revealing it's the same campaign.

### Use Case 2: Detecting Pattern Variations
**Scenario**: Scammers slightly change wording but keep same pattern.

**Result**: Embedding-based clustering groups variations together even with different exact words.

### Use Case 3: Trend Analysis
**Scenario**: Security team wants to know which scam types are most active.

**Result**: Clusters show top 5 scam types with receiver counts and average threat scores.

---

## Troubleshooting

### Clusters Not Appearing
- **Check**: At least 3 receivers with similar patterns required
- **Check**: Clusters refresh after 10 transactions
- **Solution**: Force refresh with `refresh_dynamic_clusters(force=True)`

### Duplicate Clusters
- **Check**: Merge logic should prevent duplicates
- **Solution**: Verify payment keyword normalization is working
- **Solution**: Check that final merge pass is executing

### Low Cluster Quality
- **Check**: Embedding model is loaded correctly
- **Check**: Transaction messages contain meaningful text
- **Solution**: Adjust `distance_threshold` for tighter/looser clustering

---

## Future Enhancements

Potential improvements:
- **Real-time clustering**: Update clusters on every transaction (not just every 10)
- **Agent feedback**: Use cluster patterns to retrain Pattern Agent
- **Cluster evolution tracking**: Monitor how clusters change over time
- **Multi-language support**: Extend to other languages beyond English
- **Anomaly detection**: Flag clusters that deviate from normal patterns

---

## Summary

The Dynamic Threat Clustering System is a powerful, self-learning feature that:
- ✅ Automatically discovers scam patterns without manual rules
- ✅ Groups similar scams together for better threat intelligence
- ✅ Provides context to AI agents for improved detection
- ✅ Adapts to new scam types as they emerge
- ✅ Prevents duplicate clusters through smart merging
- ✅ Shows only the most relevant clusters (top 5) to users

**Key Takeaway**: While clustering doesn't directly modify agent behavior, it provides valuable context and intelligence that enhances the overall threat detection system.

---

*Last Updated: November 2025*

