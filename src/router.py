def determine_route(data, missing_fields):
    """
    Determines the routing and classification of the claim based on extracted data and missing fields.
    Returns (route_name, reason).
    """
    
    # 1. Check for Missing Information
    if missing_fields:
        return "Manual Review", f"Missing mandatory fields: {', '.join(missing_fields)}"

    description = data.get('description', '').lower()
    claim_type = data.get('claim_type', '').lower()
    damage = data.get('estimated_damage') or data.get('initial_estimate') or 0

    # 2. Check for Fraud Indicators
    fraud_keywords = ['fraud', 'inconsistent', 'staged']
    if any(keyword in description for keyword in fraud_keywords):
        return "Investigation Flag", "Potential fraud indicators deteced in description."

    # 3. Check for Injury (Specialist)
    if 'injury' in claim_type:
        return "Specialist Queue", "Claim involves personal injury."

    # 4. Check Value Threshold
    if damage < 25000:
        return "Fast-track", f"Damage estimate (${damage}) is below the $25,000 threshold."
    else:
        return "Manual Review", f"Damage estimate (${damage}) exceeds the fast-track limit."
