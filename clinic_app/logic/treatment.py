def get_age_group(age: int) -> str:
    """Return age group string based on age."""
    if age < 0:
        raise ValueError("Age cannot be negative.")
    if age <= 12:
        return "child"
    if age <= 59:
        return "adult"
    return "old"  # senior / elderly


def get_basic_treatment(age: int, reason: str) -> dict:
    """
    Return a basic treatment plan based on age and reason for visit.
    This is just sample logic for a school/project system (NOT real medical advice).
    """
    reason = reason.lower().strip()
    age_group = get_age_group(age)

    # Standardize reason keywords
    if "check" in reason:
        reason_key = "checkup"
    elif "clean" in reason or "prophy" in reason:
        reason_key = "cleaning"
    elif "braces" in reason or "ortho" in reason:
        reason_key = "braces"
    elif "pain" in reason or "ache" in reason or "toothache" in reason:
        reason_key = "toothache"
    else:
        reason_key = "other"

    treatment = {
        "age": age,
        "age_group": age_group,
        "reason": reason_key,
        "recommended_treatment": "",
        "notes": "",
    }

    if age_group == "child":
        if reason_key == "checkup":
            treatment["recommended_treatment"] = "Oral exam, fluoride application, check if sealants are needed."
            treatment["notes"] = "Focus on prevention and monitoring tooth/jaw development."
        elif reason_key == "cleaning":
            treatment["recommended_treatment"] = "Prophylaxis (cleaning) with fluoride treatment."
            treatment["notes"] = "Teach proper brushing and flossing in a child-friendly way."
        elif reason_key == "toothache":
            treatment["recommended_treatment"] = "Exam, X-ray, filling or pulp therapy for affected baby/permanent tooth."
            treatment["notes"] = "Use child behavior management techniques; involve parents."
        elif reason_key == "braces":
            treatment["recommended_treatment"] = "Orthodontic assessment (crowding, bite, jaw growth)."
            treatment["notes"] = "May schedule full ortho workup if needed."
        else:
            treatment["recommended_treatment"] = "Basic exam, then refer to pediatric dentist if case is complex."
            treatment["notes"] = "Clarify complaint; focus on comfort and reassurance."

    elif age_group == "adult":
        if reason_key == "checkup":
            treatment["recommended_treatment"] = "Comprehensive exam, X-ray as needed, treatment plan discussion."
            treatment["notes"] = "Review dental history, lifestyle, and habits."
        elif reason_key == "cleaning":
            treatment["recommended_treatment"] = "Scaling and polishing; oral hygiene instructions."
            treatment["notes"] = "Check for early gum disease and stains."
        elif reason_key == "toothache":
            treatment["recommended_treatment"] = "Exam, X-ray, possible filling, root canal, or extraction."
            treatment["notes"] = "Explain options, cost, and follow-up visits."
        elif reason_key == "braces":
            treatment["recommended_treatment"] = "Orthodontic consultation (malocclusion, spacing, crowding)."
            treatment["notes"] = "Discuss braces vs clear aligners if available."
        else:
            treatment["recommended_treatment"] = "Initial exam and diagnosis; refer to specialist if needed."
            treatment["notes"] = "May involve endodontist, periodontist, or oral surgeon."

    else:  # age_group == "old"
        if reason_key == "checkup":
            treatment["recommended_treatment"] = "Exam of teeth, gums, dentures/implants; X-ray if needed."
            treatment["notes"] = "Consider medical history and medications (e.g., diabetes, hypertension)."
        elif reason_key == "cleaning":
            treatment["recommended_treatment"] = "Gentle scaling (may be deep cleaning) and polishing."
            treatment["notes"] = "Gums and bone may be fragile; check for periodontal disease."
        elif reason_key == "toothache":
            treatment["recommended_treatment"] = "Exam, X-ray, check old fillings/crowns, treat root or gum problems."
            treatment["notes"] = "Consider pain control, systemic health, and ability to heal."
        elif reason_key == "braces":
            treatment["recommended_treatment"] = "Consultation for bite/teeth alignment and prosthetic planning."
            treatment["notes"] = "More common to adjust dentures/implants than full ortho treatment."
        else:
            treatment["recommended_treatment"] = "Exam plus review of existing dentures/implants and oral hygiene."
            treatment["notes"] = "Focus on comfort, function, and quality of life."

    return treatment
