import json
import logging
import random
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.quiz import ExamSession, QuizQuestion, UserAnswer
from backend.services.gemini_service import gemini_quiz
from backend.security import limiter, get_current_user

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])
logger = logging.getLogger(__name__)


# --- Schémas ---

class QuestionOut(BaseModel):
    id: int
    question: str
    options: List[str]
    difficulty: str
    category: Optional[str] = None


class StartResponse(BaseModel):
    session_id: int
    questions: List[QuestionOut]


class SubmitRequest(BaseModel):
    session_id: int
    answers: List[int] = Field(..., min_length=10, max_length=10)


class SubmitResponse(BaseModel):
    score: int
    level: str
    total: int
    correct: int
    details: List[dict]


class CongratulateRequest(BaseModel):
    username: str
    level: str
    score: int


# --- Chargement des questions depuis le fichier JSON ---

_FALLBACK_QUESTIONS = [
    {"question": "Dans Naruto, quel est le nom du démon scellé en Naruto ?", "options": ["Kurama", "Shukaku", "Matatabi", "Saiken"], "correct_index": 0, "difficulty": "Junior Otaku", "category": "Naruto"},
    {"question": "Dans One Piece, quel est le rêve de Luffy ?", "options": ["Devenir Hokage", "Trouver le One Piece et devenir Roi des Pirates", "Devenir l'épéiste le plus fort", "Dessiner le meilleur manga"], "correct_index": 1, "difficulty": "Junior Otaku", "category": "One Piece"},
    {"question": "Quel est le nom du protagoniste d'Attack on Titan ?", "options": ["Eren Yeager", "Levi Ackerman", "Mikasa Ackerman", "Armin Arlelt"], "correct_index": 0, "difficulty": "Junior Otaku", "category": "Attack on Titan"},
    {"question": "Dans Naruto, quel Sharingan évolue en Rinnegan ?", "options": ["Sharingan de Sasuke", "Sharingan d'Itachi", "Sharingan de Madara", "Sharingan de Kakashi"], "correct_index": 2, "difficulty": "Senior Otaku", "category": "Naruto"},
    {"question": "Dans Demon Slayer, quel est le niveau le plus élevé des pourfendeurs ?", "options": ["Hashira", "Kinoe", "Kototo", "Hinoe"], "correct_index": 0, "difficulty": "Senior Otaku", "category": "Demon Slayer"},
    {"question": "Dans JoJo's Bizarre Adventure, quel est le nom du stand de Dio ?", "options": ["The World", "Star Platinum", "King Crimson", "Gold Experience"], "correct_index": 0, "difficulty": "Senior Otaku", "category": "JoJo"},
    {"question": "Quel est le nom du Super Saiyan divin ?", "options": ["Super Saiyan God", "Super Saiyan 4", "Super Saiyan Blue", "Ultra Instinct"], "correct_index": 0, "difficulty": "Master Otaku", "category": "Dragon Ball"},
    {"question": "Dans Jujutsu Kaisen, quel est le nom du roi des fléaux ?", "options": ["Ryomen Sukuna", "Mahito", "Geto", "Kenjaku"], "correct_index": 0, "difficulty": "Master Otaku", "category": "Jujutsu Kaisen"},
    {"question": "Quel est le nom du vrai ennemi de Madara ?", "options": ["Kaguya Otsutsuki", "Hagoromo Otsutsuki", "Zetsu", "Indra Otsutsuki"], "correct_index": 0, "difficulty": "Otaku Legendaire", "category": "Naruto"},
    {"question": "Dans Dragon Ball, quel est le nom de la transformation la plus puissante ?", "options": ["Ultra Instinct", "Super Saiyan 4", "Super Saiyan God", "Super Saiyan Blue"], "correct_index": 0, "difficulty": "Otaku Legendaire", "category": "Dragon Ball"},
]

_QUESTIONS_FILE = Path(__file__).resolve().parent.parent.parent / "json" / "anime_quiz_questions.json"

_ALL_QUESTIONS: list[dict] = []
if _QUESTIONS_FILE.exists():
    try:
        with open(_QUESTIONS_FILE, encoding="utf-8") as f:
            _ALL_QUESTIONS = json.load(f)["questions"]
        logger.info("Chargé %d questions depuis %s", len(_ALL_QUESTIONS), _QUESTIONS_FILE)
    except Exception as e:
        logger.warning("Erreur chargement JSON: %s", e)

if not _ALL_QUESTIONS:
    _ALL_QUESTIONS = _FALLBACK_QUESTIONS
    logger.warning("Utilisation du fallback de %d questions", len(_FALLBACK_QUESTIONS))

DIFFICULTY_POINTS = {
    "Junior Otaku": 5,
    "Senior Otaku": 10,
    "Master Otaku": 15,
    "Otaku Legendaire": 20,
}

LEVEL_THRESHOLDS = [
    (90, "legendary"),
    (75, "master"),
    (55, "senior"),
    (0, "junior"),
]


def _generate_questions_data(theme: Optional[str] = None):
    pool = _ALL_QUESTIONS
    if theme:
        pool = [q for q in pool if q.get("category", "").lower() == theme.lower()]
        if not pool:
            pool = _ALL_QUESTIONS
    count = min(10, len(pool))
    questions = random.sample(pool, count) if count > 0 else []
    return questions


def _score_to_level(pct: int) -> str:
    for threshold, level in LEVEL_THRESHOLDS:
        if pct >= threshold:
            return level
    return "junior"


# --- Routes ---

@router.post("/start", response_model=StartResponse)
def start_quiz(
    theme: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions_data = _generate_questions_data(theme)

    session = ExamSession(user_id=user.id, status="in_progress")
    db.add(session)
    db.flush()

    created = []
    for q in questions_data:
        qq = QuizQuestion(
            exam_session_id=session.id,
            question_text=q["question"],
            options=q["options"],
            correct_index=q["correct_index"],
            difficulty=q["difficulty"],
            category=q.get("category"),
        )
        db.add(qq)
        created.append(qq)
    db.flush()

    return StartResponse(
        session_id=session.id,
        questions=[
            QuestionOut(
                id=q.id,
                question=q.question_text,
                options=q.options,
                difficulty=q.difficulty,
                category=q.category,
            )
            for q in created
        ],
    )


@router.get("/current/{session_id}", response_model=StartResponse)
def get_current_quiz(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ExamSession).filter(
        ExamSession.id == session_id,
        ExamSession.user_id == user.id,
        ExamSession.status == "in_progress",
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable ou déjà terminée")

    questions = db.query(QuizQuestion).filter(
        QuizQuestion.exam_session_id == session_id
    ).all()

    return StartResponse(
        session_id=session.id,
        questions=[
            QuestionOut(
                id=q.id,
                question=q.question_text,
                options=q.options,
                difficulty=q.difficulty,
                category=q.category,
            )
            for q in questions
        ],
    )


@router.post("/submit", response_model=SubmitResponse)
def submit_quiz(
    req: SubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ExamSession).filter(
        ExamSession.id == req.session_id,
        ExamSession.user_id == user.id,
        ExamSession.status == "in_progress",
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable ou déjà terminée")

    questions = db.query(QuizQuestion).filter(
        QuizQuestion.exam_session_id == req.session_id
    ).all()

    if len(questions) != len(req.answers):
        raise HTTPException(status_code=400, detail="Nombre de réponses incorrect")

    total_points = 0
    earned_points = 0
    details = []

    for q, ans in zip(questions, req.answers):
        pts = DIFFICULTY_POINTS.get(q.difficulty, 10)
        total_points += pts
        is_correct = q.correct_index == ans

        ua = UserAnswer(
            user_id=user.id,
            question_id=q.id,
            selected_index=ans,
            is_correct=1 if is_correct else 0,
        )
        db.add(ua)

        if is_correct:
            earned_points += pts

        details.append({
            "question_id": q.id,
            "correct": q.correct_index,
            "selected": ans,
            "is_correct": is_correct,
            "difficulty": q.difficulty,
        })

    score_pct = round((earned_points / total_points) * 100) if total_points > 0 else 0
    level = _score_to_level(score_pct)
    correct_count = sum(1 for d in details if d["is_correct"])

    session.status = "completed"
    session.completed_at = None
    session.score = score_pct
    session.level = level

    return SubmitResponse(
        score=score_pct,
        level=level,
        total=len(questions),
        correct=correct_count,
        details=details,
    )


@router.post("/congratulate")
def congratulate(
    req: CongratulateRequest,
    user: User = Depends(get_current_user),
):
    try:
        message = gemini_quiz.generate_congratulation(req.username, req.level, req.score)
    except Exception:
        message = (
            f"Félicitations {req.username} ! Tu as obtenu le niveau {req.level} avec {req.score}% !\n\n"
            f"Système d'Évaluation Autonome BNC-Otaku v2.0.\n"
            f"Protocole d'examen régi par les standards de performance établis par la Direction de Djousse Tech Evolution.\n"
            f"Ce certificat atteste de la validation des acquis conformément aux directives de qualité édictées par BeauteGar, Directeur.\n\n"
            f"Document émis par Djousse Tech Evolution — Validé par BeauteGar, Directeur."
        )

    return {"message": message}
