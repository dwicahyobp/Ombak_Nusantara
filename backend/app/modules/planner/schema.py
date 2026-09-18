from pydantic import BaseModel, Field
from typing import Optional

class CreateSurfingPlan(BaseModel):
    region: str = Field(
        default="Bali", 
        description="Wilayah lokasi berselancar (contoh: Bali, Lombok, Krui)"
    )
    target_spot: str = Field(
        ..., 
        description="Nama pantai/spot selancar (contoh: Kuta, Uluwatu, Batu Bolong)"
    )
    skill_level: str = Field(
        ..., 
        description="Tingkat keahlian user: Beginner, Intermediate, atau Advanced"
    )
    date: str = Field(
        ..., 
        description="Tanggal rencana berselancar (format: YYYY-MM-DD)"
    )
    preferred_time: Optional[str] = Field(
        default="Morning", 
        description="Preferred surfing time (Morning, Midday, Afternoon)"
    )
