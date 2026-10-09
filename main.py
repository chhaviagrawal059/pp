from datetime import datetime, timezone
from itertools import count
from typing import Literal
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Jharkhand Societal Innovation Portal API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Category = Literal["Education", "Healthcare", "Agriculture", "Water resources", "Environment", "Renewable energy", "Rural livelihoods", "Accessibility", "Urban infrastructure", "Public administration", "Other"]

class ChallengeCreate(BaseModel):
    title: str = Field(min_length=8, max_length=140)
    description: str = Field(min_length=20, max_length=4000)
    district: str = Field(min_length=2, max_length=80)
    category: Category | None = None
    severity: int = Field(default=3, ge=1, le=5)
    urgency: int = Field(default=3, ge=1, le=5)
    affected_population: int = Field(default=100, ge=1, le=10000000)

class Challenge(ChallengeCreate):
    id: int
    category: Category
    priority_score: int
    status: str = "Submitted"
    created_at: str
    demo: bool = False

ids = count(4)
challenges: list[dict] = [
    {"id": 1, "title": "Reliable drinking water access in remote villages", "description": "Community members report seasonal shortages of safe drinking water and long travel distances to functioning sources.", "district": "West Singhbhum", "category": "Water resources", "severity": 5, "urgency": 5, "affected_population": 1800, "priority_score": 94, "status": "Validated", "created_at": "2026-09-18T09:00:00+00:00", "demo": True},
    {"id": 2, "title": "Low-cost soil moisture monitoring for small farms", "description": "Smallholder farmers need an affordable way to decide when fields require irrigation and reduce avoidable water use.", "district": "Dumka", "category": "Agriculture", "severity": 3, "urgency": 3, "affected_population": 620, "priority_score": 61, "status": "Assigned to University", "created_at": "2026-09-21T10:30:00+00:00", "demo": True},
    {"id": 3, "title": "Accessible learning resources for rural schools", "description": "Several schools need offline-first learning materials that work with limited connectivity and support different learning needs.", "district": "Latehar", "category": "Education", "severity": 4, "urgency": 3, "affected_population": 950, "priority_score": 68, "status": "Under Review", "created_at": "2026-09-25T11:15:00+00:00", "demo": True},
]

KEYWORDS: dict[str, list[str]] = {
    "Education": ["school", "student", "learning", "education", "teacher", "classroom"],
    "Healthcare": ["health", "hospital", "clinic", "medicine", "patient", "medical"],
    "Agriculture": ["farm", "farmer", "crop", "soil", "irrigation", "agriculture"],
    "Water resources": ["water", "drinking", "well", "river", "shortage", "sanitation"],
    "Environment": ["waste", "pollution", "forest", "environment", "plastic", "wildlife"],
    "Renewable energy": ["solar", "energy", "electricity", "power", "renewable", "grid"],
    "Rural livelihoods": ["livelihood", "income", "artisan", "employment", "self-help", "market"],
    "Accessibility": ["accessible", "disability", "wheelchair", "blind", "inclusive"],
    "Urban infrastructure": ["road", "streetlight", "drainage", "traffic", "bridge", "transport"],
    "Public administration": ["government", "certificate", "public service", "document", "office"],
}

def classify(text: str) -> str:
    lowered = text.lower()
    scores = {category: sum(1 for word in words if re.search(r"\b" + re.escape(word) + r"\b", lowered)) for category, words in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "Other"

def priority(severity: int, urgency: int, population: int, description: str) -> int:
    # Explainable demo heuristic, not an ML prediction.
    population_score = min(5, max(1, round(population / 500)))
    safety_bonus = 1 if any(w in description.lower() for w in ["unsafe", "contaminated", "injury", "life-threatening", "disease"]) else 0
    return min(100, round(((severity * 0.35 + urgency * 0.30 + population_score * 0.25) / 5) * 100 + safety_bonus * 5))

@app.get("/")
def root():
    return {"name": "Jharkhand Societal Innovation Portal API", "status": "running", "docs": "/docs"}

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "mode": "demo-in-memory"}

@app.get("/api/challenges", response_model=list[Challenge])
def list_challenges():
    return challenges

@app.post("/api/challenges", response_model=Challenge, status_code=201)
def create_challenge(payload: ChallengeCreate):
    combined = f"{payload.title} {payload.description}"
    category = payload.category or classify(combined)
    item = {
        **payload.model_dump(),
        "id": next(ids),
        "category": category,
        "priority_score": priority(payload.severity, payload.urgency, payload.affected_population, payload.description),
        "status": "Submitted",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "demo": False,
    }
    # Human review is required; similarity only warns and does not auto-delete.
    words = set(re.findall(r"[a-z]{4,}", combined.lower()))
    matches = []
    for existing in challenges:
        old_words = set(re.findall(r"[a-z]{4,}", f"{existing['title']} {existing['description']}".lower()))
        similarity = len(words & old_words) / max(1, len(words | old_words))
        if similarity >= 0.16:
            matches.append({"id": existing["id"], "title": existing["title"], "similarity": round(similarity, 2)})
    item["possible_duplicates"] = matches
    challenges.insert(0, item)
    return item

@app.get("/api/analytics")
def analytics():
    return {
        "total": len(challenges),
        "awaiting_review": sum(1 for c in challenges if c["status"] in ["Submitted", "Under Review"]),
        "validated": sum(1 for c in challenges if c["status"] in ["Validated", "Assigned to University"]),
        "districts": len({c["district"] for c in challenges}),
        "categories": {category: sum(1 for c in challenges if c["category"] == category) for category in sorted({c["category"] for c in challenges})},
        "demo_records_included": sum(1 for c in challenges if c.get("demo", False)),
    }

@app.patch("/api/challenges/{challenge_id}/status")
def update_status(challenge_id: int, status: str):
    allowed = {"Under Review", "Validated", "Rejected", "Assigned to University", "Proposal Submitted", "In Progress", "Completed", "Paused"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported status")
    for challenge in challenges:
        if challenge["id"] == challenge_id:
            challenge["status"] = status
            return challenge
    raise HTTPException(status_code=404, detail="Challenge not found")
