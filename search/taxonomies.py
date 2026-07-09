"""
Diccionarios estructurados del dominio.
Fuente de verdad para roles, seniority y señales de experiencia.
"""

# ──────────────────────────────────────────────────────────────
#  ROLES — grupos semánticos con términos de búsqueda alternativos
# ──────────────────────────────────────────────────────────────
ROLE_GROUPS: dict[str, dict] = {
    "machine_learning": {
        "terms": [
            "machine learning", "ml engineer", "deep learning", "neural network",
            "nlp", "llm", "large language model", "computer vision", "cv engineer",
            "ai engineer", "artificial intelligence", "research engineer",
            "data scientist", "mlops", "model training", "pytorch", "tensorflow",
        ],
        "api_queries": ["machine learning", "artificial intelligence", "data scientist AI"],
    },
    "data": {
        "terms": [
            "data engineer", "data analyst", "analytics engineer", "etl",
            "data pipeline", "spark", "airflow", "dbt", "sql", "bigquery",
            "snowflake", "databricks", "business intelligence", "bi developer",
        ],
        "api_queries": ["data engineer", "data analyst"],
    },
    "backend": {
        "terms": [
            "backend", "back-end", "back end", "python developer", "java developer",
            "node.js", "nodejs", "django", "fastapi", "spring boot", "golang",
            "go developer", "rust developer", "php developer", "ruby on rails",
            "api developer", "microservices", "software engineer",
        ],
        "api_queries": ["backend developer", "software engineer"],
    },
    "frontend": {
        "terms": [
            "frontend", "front-end", "front end", "react", "vue", "angular",
            "javascript developer", "typescript developer", "ui developer",
            "web developer", "next.js", "svelte", "html css",
        ],
        "api_queries": ["frontend developer", "react developer"],
    },
    "fullstack": {
        "terms": [
            "fullstack", "full stack", "full-stack", "mern", "mean stack",
            "django react", "rails react",
        ],
        "api_queries": ["fullstack developer"],
    },
    "devops": {
        "terms": [
            "devops", "sre", "site reliability", "cloud engineer", "aws", "gcp",
            "azure", "kubernetes", "k8s", "docker", "terraform", "infrastructure",
            "platform engineer", "ci/cd",
        ],
        "api_queries": ["devops engineer", "cloud engineer"],
    },
    "mobile": {
        "terms": [
            "ios developer", "android developer", "mobile developer", "swift",
            "kotlin", "react native", "flutter",
        ],
        "api_queries": ["mobile developer"],
    },
    "design": {
        "terms": [
            "ux designer", "ui designer", "product designer", "figma",
            "user experience", "user interface", "graphic designer",
        ],
        "api_queries": ["ux designer", "product designer"],
    },
    "product": {
        "terms": [
            "product manager", "product owner", "pm", "scrum master",
            "agile coach", "project manager",
        ],
        "api_queries": ["product manager"],
    },
    "security": {
        "terms": [
            "cybersecurity", "security engineer", "penetration testing", "pentester",
            "soc analyst", "devsecops",
        ],
        "api_queries": ["cybersecurity engineer"],
    },
}

# ──────────────────────────────────────────────────────────────
#  SENIORITY — niveles con sus señales
# ──────────────────────────────────────────────────────────────
SENIORITY_LEVELS: dict[str, dict] = {
    "internship": {
        "title_keywords": [
            "intern", "internship", "becario", "becaria", "prácticas", "practica",
            "trainee", "werkstudent", "praktikant", "stage", "stagiaire",
        ],
        "desc_keywords": [
            "internship program", "prácticas", "becario", "prakti",
            "student position", "posición de prácticas",
        ],
        "positive_signals": [
            "no experience required", "no experience needed", "sin experiencia",
            "recent graduate", "recién graduado", "students welcome",
            "university student", "estudiante universitario", "tfg", "tfm",
            "final de grado", "final de máster", "joven talento",
            "first job", "primer empleo", "0 years", "entry level",
            "0-1 year", "less than 1 year", "menos de 1 año",
        ],
        "score_base": 100,
    },
    "junior": {
        "title_keywords": [
            "junior", "jr.", " jr ", "entry level", "entry-level",
            "graduate", "associate", "júnior",
        ],
        "desc_keywords": [
            "junior developer", "junior engineer", "entry level",
        ],
        "positive_signals": [
            "0-2 years", "0-3 years", "1-2 years", "up to 2 years",
            "less than 2 years", "menos de 2 años", "hasta 2 años",
            "recent graduate", "new grad", "recién graduado",
        ],
        "score_base": 80,
    },
    "mid": {
        "title_keywords": [],
        "desc_keywords": [],
        "positive_signals": [
            "2-4 years", "2-5 years", "3-5 years", "3+ years",
            "some experience", "alguna experiencia",
        ],
        "score_base": 50,
    },
    "senior": {
        "title_keywords": [
            "senior", "sr.", " sr ", "experienced", "experto",
        ],
        "desc_keywords": [],
        "positive_signals": [
            "5+ years", "5 years", "7+ years", "7 years", "10 years",
            "extensive experience", "amplia experiencia",
        ],
        "score_base": 20,
    },
    "lead": {
        "title_keywords": [
            "lead", "principal", "staff", "architect", "manager",
            "director", "head of", "vp ", "chief", "cto", "cpo",
        ],
        "desc_keywords": [
            "manage a team", "manage team", "lead a team", "lead the team",
            "dirección de equipo", "gestión de equipo",
        ],
        "positive_signals": [
            "10+ years", "team management", "people management",
            "managing engineers", "hire and mentor",
        ],
        "score_base": 5,
    },
}

# Señales negativas que bajan el seniority percibido
NEGATIVE_SENIORITY_SIGNALS = [
    "ownership of", "own the", "production systems at scale",
    "multiple teams", "org-wide", "company-wide strategy",
    "budget responsibility", "p&l",
]

# Patrones de años de experiencia (regex)
YEARS_REQUIRED_PATTERNS = [
    r"(\d+)\+?\s*(?:years?|años?)\s*(?:of\s*)?(?:experience|experiencia)",
    r"(?:experience|experiencia)\s*(?:of\s*)?(\d+)\+?\s*(?:years?|años?)",
    r"(\d+)\s*-\s*\d+\s*(?:years?|años?)",
    r"al menos\s*(\d+)\s*(?:años?)",
    r"minimum\s*(\d+)\s*(?:years?)",
    r"mínimo\s*(\d+)\s*(?:años?)",
]
