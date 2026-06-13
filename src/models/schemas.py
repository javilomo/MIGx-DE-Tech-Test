import pandas as pd
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional

class ClinicalTrialSchema(BaseModel):
    """
    Defines the data contract and validation rules for a single clinical trial record.
    Maps messy raw CSV column names to standardized pythonic snake_case fields.
    """
    trial_id: str = Field(..., alias="NCT Number")
    condition: str = Field(..., alias="Condition")
    phase: Optional[str] = Field("Unknown", alias="Phases")
    status: str = Field(..., alias="Status")
    enrollment: int = Field(default=0, alias="Enrollment")
    start_date: Optional[date] = Field(None, alias="Start Date")

    @field_validator('enrollment', mode='before')
    @classmethod
    def clean_enrollment(cls, v):
        """
        Handles missing, empty, or float-formatted strings (e.g., '150.0') 
        commonly found in raw data exports to prevent parsing errors.
        """
        if v is None or v == '' or pd.isna(v):
            return 0
        return int(float(v))