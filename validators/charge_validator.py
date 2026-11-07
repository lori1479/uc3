import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CHARGES_FILE = BASE_DIR / "data" / "charges.json"
REQUIREMENTS_FILE = BASE_DIR / "data" / "charge_requirements.json"

# Fields scanned for uncertain wording. Edit this list to tune the check.
# entry_event / entry_time_or_place are only present if your report supplies them.
AMBIGUITY_FIELDS = [
    "entry_event",
    "entry_time_or_place",
    "entry_without_inspection",
    "previous_denial_or_removal",
    "entry_or_attempt",
    "officer_observations",
    "inspection_findings",
]

UNCERTAINTY_PHRASES = [
    "unknown",
    "unclear",
    "uncertain",
    "may have",
    "might have",
    "could not confirm",
    "not confirmed",
    "possibly"
]


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def _is_blank(value):
    """True for None, blank strings, and empty lists/dicts."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    return False


def get_evidence_reference(report, field_name):
    """
    Return the source reference for a report field.

    The report can provide sentence IDs and excerpts
    in an evidence_references dictionary.
    """
    references = report.get("evidence_references") or {}
    reference = references.get(field_name) or {}

    return {
        "field": field_name,
        "sentence_id": reference.get("sentence_id"),
        "excerpt": reference.get("excerpt")
    }


def check_contradictions(report):
    contradictions = []

    # Compare two structured fields describing the same event.
    reported_location = report.get("entry_location")
    verified_location = report.get("verified_entry_location")

    if (
        isinstance(reported_location, str)
        and isinstance(verified_location, str)
        and reported_location.strip()
        and verified_location.strip()
        and reported_location.strip().casefold()
        != verified_location.strip().casefold()
    ):
        contradictions.append({
            "type": "possible_contradiction",
            "field": "entry_location",
            "conflicting_field": "verified_entry_location",
            "message": "Two location fields contain different values.",
            "evidence": {
                "entry_location": {
                    "value": reported_location,
                    "reference": get_evidence_reference(
                        report, "entry_location"
                    )
                },
                "verified_entry_location": {
                    "value": verified_location,
                    "reference": get_evidence_reference(
                        report, "verified_entry_location"
                    )
                }
            },
            "review_required": True
        })

    return contradictions


def check_ambiguity(report):
    flags = []

    for field_name in AMBIGUITY_FIELDS:
        value = report.get(field_name)

        if not isinstance(value, str):
            continue

        if any(phrase in value.lower() for phrase in UNCERTAINTY_PHRASES):
            flags.append({
                "type": "ambiguous_information",
                "field": field_name,
                "message": f"Uncertain information detected in {field_name}.",
                "evidence_reference": get_evidence_reference(
                    report, field_name
                ),
                "review_required": True
            })

    return flags


def _review_result(flag_type, message, selected_charge=None):
    """Early-return result using the same flag shape as the normal path."""
    return {
        "selected_charge": selected_charge,
        "status": "human_review_required",
        "flags": [{
            "type": flag_type,
            "message": message,
            "review_required": True
        }]
    }


def validate_charge(report):
    charges_data = load_json(CHARGES_FILE)
    requirements_data = load_json(REQUIREMENTS_FILE)

    selected_charge = report.get("charge_code")

    if not selected_charge:
        return _review_result("no_charge", "No charge was selected.")

    charge = next(
        (
            item for item in charges_data["charges"]
            if item["charge_id"] == selected_charge
        ),
        None
    )

    if charge is None:
        return _review_result(
            "unknown_charge",
            "Selected charge is not in the charge catalog.",
            selected_charge,
        )

    applicable_requirements = [
        item
        for item in requirements_data["requirements"]
        if item["charge_id"] == selected_charge
    ]

    if not applicable_requirements:
        return _review_result(
            "no_requirements",
            "No documentation requirements are configured for this charge.",
            selected_charge,
        )

    flags = []

    for requirement in applicable_requirements:
        field_name = requirement["report_field"]
        field_value = report.get(field_name)

        if _is_blank(field_value):
            flags.append({
                "type": "missing_documentation",
                "requirement_id": requirement["requirement_id"],
                "field": field_name,
                "message": (
                    f"Missing documentation for: {requirement['description']}"
                ),
                "evidence_reference": get_evidence_reference(
                    report, field_name
                ),
                "review_required": True
            })

    flags.extend(check_contradictions(report))
    flags.extend(check_ambiguity(report))

    return {
        "selected_charge": selected_charge,
        "status": "human_review_required",
        "flags": flags,
        "message": (
            "Preliminary documentation check only. "
            "Legal requirements remain pending review; "
            "this result does not establish charge sufficiency."
        )
    }


if __name__ == "__main__":
    sample_report = {
        "charge_code": "8_USC_1325",
        "entry_event": "The individual may have attempted entry.",
        "entry_time_or_place": "Location documented in the report",
        "entry_location": "Location A",
        "verified_entry_location": "Location B",

        "evidence_references": {
            "entry_event": {
                "sentence_id": "S1",
                "excerpt": "The individual may have attempted entry."
            },
            "entry_time_or_place": {
                "sentence_id": "S2",
                "excerpt": "The attempted entry occurred at Location A."
            },
            "entry_location": {
                "sentence_id": "S2",
                "excerpt": "The attempted entry occurred at Location A."
            },
            "verified_entry_location": {
                "sentence_id": "S5",
                "excerpt": "The verified location was Location B."
            }
        }
    }

    result = validate_charge(sample_report)

    print(json.dumps(result, indent=4))
