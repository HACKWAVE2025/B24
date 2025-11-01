def aggregate_scores(agents):
    """
    Aggregate risk scores from all agents into overall risk score.
    
    Args:
        agents: List of dicts, each with keys:
            - 'agent_name': str (e.g., 'Pattern Agent')
            - 'risk_score': float (0-100)
    
    Returns:
        float: Overall risk score (0-100)
    """
    if not agents:
        return 0.0

    # Extract only valid risk scores
    scores = {agent['agent_name']: agent['risk_score'] 
               for agent in agents if 'risk_score' in agent}

    if not scores:
        return 0.0

    # Updated static weights
    weights = {
        'Pattern Agent': 0.40,   # Highest priority
        'Network Agent': 0.25,   # Equal to Behavior
        'Behavior Agent': 0.25,  
        'Biometric Agent': 0.10  # Lowest influence
    }

    # Weighted sum only for available agents
    weighted_sum = 0
    total_weight = 0
    for name, weight in weights.items():
        if name in scores:
            weighted_sum += scores[name] * weight
            total_weight += weight

    overall = weighted_sum / total_weight if total_weight else 0

    # Boost logic for stronger consensus
    high_risk_count = sum(1 for s in scores.values() if s >= 70)
    if high_risk_count >= 2:
        overall = min(overall * 1.15, 100)
    elif high_risk_count == 1 and overall >= 50:
        overall = min(overall * 1.10, 100)
    elif high_risk_count == 1 and overall < 50:
        overall = min(overall * 1.20, 100)

    return round(overall, 1)
