import re

ACORD_LABELS = {
    "INSURED", "CONTACT", "OWNER", "PHONE", "CELL", "HOME", "BUS",
    "PRIMARY", "SECONDARY", "ADDRESS", "FAX", "MODEL", "MAKE", "TYPE",
    "YEAR", "BODY", "STATE", "PLATE", "VEH", "V.I.N", "VIN",
    "LINE", "BUSINESS", "REPORT", "NUMBER", "AGENCY",
    "REPORTED", "CARRIER", "LOSS", "NAME", "DESCRIBE",
    "WHEN", "TO", "ACORD", "LOCATION", "CITY", "COUNTRY"
}


def clean_value(v):
    if not v:
        return None
    v = v.replace("\n", " ").strip()
    parts = v.split()
    cleaned = [p for p in parts if p.upper() not in ACORD_LABELS]
    out = " ".join(cleaned).strip()
    return out if out else None


def extract_fields(text):
    print("from extractor!!")
    data = {}

    def find(pattern):
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return clean_value(m.group(1)) if m else None

    # ------------------------------------------------------------
    # POLICY NUMBER
    # ------------------------------------------------------------
    pn = find(r"POLICY\s+NUMBER[: ]*([A-Z0-9\-]+)")
    data["policy_number"] = pn if pn and re.search(r"\d", pn) else None

    # ------------------------------------------------------------
    # POLICYHOLDER NAME
    # ------------------------------------------------------------
    m = re.search(r"NAME\s+OF\s+INSURED.*?\n(.+)", text, re.IGNORECASE)
    ph = clean_value(m.group(1)) if m else None
    data["policyholder_name"] = ph

    # ------------------------------------------------------------
    # EFFECTIVE DATES
    # ------------------------------------------------------------
    data["effective_dates"] = find(r"(?:EFFECTIVE\s+DATES|POLICY\s+PERIOD).*?([0-9\/\-\s]+)")

    # ------------------------------------------------------------
    # INCIDENT DATE
    # ------------------------------------------------------------
    date1 = find(r"DATE\s+OF\s+LOSS.*?([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})")

    if not date1:
        m = re.search(r"\b([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})\b", text)
        date1 = m.group(1) if m else None

    data["incident_date"] = date1

    # ------------------------------------------------------------
    # INCIDENT TIME
    # ------------------------------------------------------------
    time_raw = find(r"([0-9]{1,2}[:\.][0-9]{2}\s*(?:AM|PM)?)")
    if time_raw:
        t = time_raw.replace(".", ":")
        if not re.search(r"AM|PM", t, re.IGNORECASE):
            t += " AM"
        data["incident_time"] = t
    else:
        data["incident_time"] = None

    # ------------------------------------------------------------
    # LOCATION OF LOSS (ACORD structured block)
    # ------------------------------------------------------------
    loc = re.search(
        r"LOCATION OF LOSS.*?STREET:(.*?)\n.*?"
        r"CITY,.*?ZIP:(.*?)\n.*?"
        r"COUNTRY:(.*?)\n",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if loc:
        street = clean_value(loc.group(1))
        cityzip = clean_value(re.split(r"REPORT", loc.group(2))[0])
        country = clean_value(loc.group(3))
        data["incident_location"] = ", ".join([p for p in [street, cityzip, country] if p])
    else:
        data["incident_location"] = None

    # ------------------------------------------------------------
    # DESCRIPTION OF ACCIDENT
    # ------------------------------------------------------------
    desc = find(r"DESCRIPTION\s+OF\s+ACCIDENT.*?\n([^\n]+)")
    data["description"] = desc

    # ------------------------------------------------------------
    # CLAIMANT
    # ------------------------------------------------------------
    claimant = find(r"REPORTED BY\s*\n([^\n]+)")
    if not claimant:
        claimant = ph
    data["claimant"] = claimant

    # ------------------------------------------------------------
    # CONTACT DETAILS
    # ------------------------------------------------------------
    contact_name = find(r"NAME\s+OF\s+CONTACT.*?\n([^\n]+)")
    if contact_name and contact_name.upper() in ACORD_LABELS:
        contact_name = None

    emails = list(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)))
    phones = list(set(re.findall(r"\b[0-9]{10}\b", text)))

    data["contact_details"] = {
        "name": contact_name,
        "emails": sorted(emails),
        "phones": sorted(phones)
    } if (contact_name or emails or phones) else None

    # ------------------------------------------------------------
    # THIRD PARTIES (Witnesses)
    # ------------------------------------------------------------
    third = []
    lines = text.splitlines()
    collecting = False

    for line in lines:
        l = line.strip()

        if "WITNESSES" in l.upper():
            collecting = True
            continue

        if collecting:
            if "REPORTED BY" in l.upper() or "OTHER VEH" in l.upper():
                break

            m = re.match(r"(.+?)\s+([0-9]{10})", l)
            if m:
                name = clean_value(m.group(1))
                phone = m.group(2)
                third.append({"name": name, "phone": phone})

    data["third_parties"] = third if third else None

    # ------------------------------------------------------------
    # VEHICLE DETAILS
    # ------------------------------------------------------------
    model = find(r"MODEL[: ]*([A-Za-z0-9 ]+)")
    make = find(r"MAKE[: ]*([A-Za-z0-9 ]+)")
    vin = find(r"V\.?I\.?N\.?:?\s*([A-Za-z0-9]+)")

    def reject_bad(v):
        if not v:
            return None
        bad = ["YEARVEH", "VEH", "MODEL", "MAKE", "TYPE"]
        return None if any(b in v.upper() for b in bad) else v

    data["asset_model"] = reject_bad(model)
    data["asset_make"] = reject_bad(make)
    data["asset_id"] = vin
    data["asset_year"] = find(r"YEAR\s+([0-9]{4})")
    data["asset_type"] = "Vehicle" if vin else None

    # ------------------------------------------------------------
    # DAMAGE AMOUNTS (multiple ESTIMATE AMOUNT lines)
    # ------------------------------------------------------------
    est_matches = re.findall(r"ESTIMATE\s+AMOUNT[: ]*\n?([0-9,]+)", text)

    clean_nums = []
    for e in est_matches:
        v = re.sub(r"[^\d]", "", e)
        if v:
            clean_nums.append(int(v))

    if len(clean_nums) >= 2:
        data["initial_estimate"] = min(clean_nums)
        data["estimated_damage"] = max(clean_nums)
    elif len(clean_nums) == 1:
        data["initial_estimate"] = clean_nums[0]
        data["estimated_damage"] = clean_nums[0]
    else:
        data["initial_estimate"] = None
        data["estimated_damage"] = None

    # ------------------------------------------------------------
    # CLAIM TYPE (fallback for ACORD forms)
    # ------------------------------------------------------------
    ct = find(r"CLAIM\s+TYPE[: ]*([^\n]+)")
    if not ct and "AUTOMOBILE LOSS NOTICE" in text.upper():
        ct = "Automobile"
    data["claim_type"] = ct

    # ------------------------------------------------------------
    # ATTACHMENTS
    # ------------------------------------------------------------
    data["attachments"] = find(r"ATTACHMENTS[: ]*([^\n]+)")

    return data
