def validate_fields(data):
    """
    Checks for missing mandatory fields in the extracted data.
    Returns a list of missing field names.
    """
    mandatory_fields = [
        'policy_number',
        'policyholder_name',
        'incident_date',
        'description',
        'claim_type',
        'estimated_damage' # We can fallback to initial_estimate if this is missing, but for now strict check
    ]

    missing = []
    
    # Check simple fields
    for field in mandatory_fields:
        if not data.get(field):
            # Special case: check if estimated_damage is missing but initial_estimate exists
            if field == 'estimated_damage' and data.get('initial_estimate'):
                continue
            missing.append(field)
            
    return missing
