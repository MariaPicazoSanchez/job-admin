from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Job:
    # Campos base
    title: str
    company: str
    location: str
    url: str
    source: str

    # Salario
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "EUR"

    # Modalidad y descripción
    job_type: str = ""        # remote | hybrid | onsite | ""
    description: str = ""
    posted: str = ""
    tags: list[str] = field(default_factory=list)

    # Metadata inferida por el enricher
    seniority_level: str = "unknown"   # internship | junior | mid | senior | lead | unknown
    seniority_score: float = 40.0      # 0-100, mayor = más junior
    years_required: Optional[int] = None
    role_category: str = "other"       # ml | frontend | backend | devops | data | ...

    @property
    def salary_display(self) -> str:
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,} – {self.salary_max:,} {self.currency}".replace(",", ".")
        if self.salary_min:
            return f"Desde {self.salary_min:,} {self.currency}".replace(",", ".")
        if self.salary_max:
            return f"Hasta {self.salary_max:,} {self.currency}".replace(",", ".")
        return "Salario no indicado"

    @property
    def seniority_label(self) -> str:
        return {
            "internship": "Prácticas",
            "junior":     "Junior",
            "mid":        "Mid",
            "senior":     "Senior",
            "lead":       "Lead",
            "unknown":    "",
        }.get(self.seniority_level, "")
