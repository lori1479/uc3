from pydantic import BaseModel
from typing import Optional

class Report(BaseModel):
    officer_id: Optional[str] = None
    officer_name: Optional[str] = None

    report_date: Optional[str] = None
    encounter_time: Optional[str] = None
    port_of_entry: Optional[str] = None
    incident_date: Optional[str] = None

    traveler_name: Optional[str] = None
    nationality: Optional[str] = None
    citizenship: Optional[str] = None

    passport_number: Optional[str] = None
    claimed_status: Optional[str] = None

    travel_documents: Optional[str] = None
    purpose_of_travel: Optional[str] = None
    arrival_method: Optional[str] = None

    traveler_statements: Optional[str] = None
    officer_observations: Optional[str] = None
    inspection_findings: Optional[str] = None

    charge_code: Optional[str] = None
    ina_section: Optional[str] = None
    inadmissibility_explanation: Optional[str] = None

    traveler_response: Optional[str] = None
    officer_analysis_of_response: Optional[str] = None

    disposition: Optional[str] = None
    forms_used: Optional[str] = None
    supervisory_review: Optional[str] = None
    service_acknowledgement: Optional[str] = None

    narrative: Optional[str] = None
    evidence: Optional[str] = None
