# FIGMENT - AI-Powered UPI Fraud Detection System

## Problem Statement

UPI (Unified Payments Interface) transactions have become increasingly popular in India, but this growth has also led to a rise in fraudulent activities. Users often fall victim to scams during transactions, resulting in financial losses. The challenge is to detect and prevent these fraudulent transactions in real-time before they are completed.

Current solutions lack:
- Real-time fraud detection capabilities
- Multi-factor analysis of transaction patterns
- User behavior monitoring
- Immediate intervention mechanisms

## Our Solution

FIGMENT is a multi-agent AI system designed to detect potential scams during UPI transactions in real time. Our approach combines multiple specialized AI agents that analyze different aspects of a transaction:

1. **Pattern Agent**: Analyzes transaction messages using Machine Learning (TF-IDF + Logistic Regression)
2. **Network Agent**: Checks receiver UPI against a crowd-reported scam database in MongoDB
3. **Behavior Agent**: Detects anomalies in user behavior using Isolation Forest algorithms
4. **Biometric Agent**: Monitors typing patterns (speed, corrections) for signs of coercion

The system aggregates results from all agents into an overall risk score. For high-risk transactions (>40% risk), the system requires PIN confirmation before proceeding.

Additionally, Gemini AI generates human-readable explanations for why a transaction was flagged, helping users understand the risks.

## Implementation Approaches

We have developed FIGMENT using two different approaches:

### 1. Web Application
A full-featured web application built with React and Flask that provides a comprehensive dashboard for monitoring transactions and viewing fraud analysis.

**Technology Stack:**
- Frontend: React, TailwindCSS, Framer Motion, shadcn/ui
- Backend: Flask, MongoDB, scikit-learn
- AI Integration: Google Generative AI (Gemini)

### 2. Mobile Application
A mobile-first implementation designed for on-the-go transaction monitoring and immediate fraud alerts.

## Getting Started

For detailed instructions on setting up and running each version, please refer to the respective README files:
- [Web Application README](README.md)