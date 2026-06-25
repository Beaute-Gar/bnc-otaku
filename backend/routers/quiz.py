from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.models.quiz import ExamSession, QuizQuestion, UserAnswer
from backend.services.gemini_service import gemini_quiz
from backend.security import limiter, get_current_user

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


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


# --- Questions de secours ---

MOCK_QUESTIONS = [
    {"question": "Quel est le vrai nom de Goku ?", "options": ["Kakarot", "Bardock", "Raditz", "Kakarotto"], "correct_index": 0, "difficulty": "facile", "category": "Dragon Ball"},
    {"question": "Dans One Piece, quel est le rêve de Luffy ?", "options": ["Devenir Hokage", "Trouver le One Piece et devenir Roi des Pirates", "Devenir l'épéiste le plus fort", "Dessiner le meilleur manga"], "correct_index": 1, "difficulty": "facile", "category": "One Piece"},
    {"question": "Quel est le nom du démon-épéiste dans Demon Slayer ?", "options": ["Tanjiro", "Zenitsu", "Inosuke", "Giyu"], "correct_index": 0, "difficulty": "facile", "category": "Demon Slayer"},
    {"question": "Dans Naruto, quel Sharingan évolue en Rinnegan ?", "options": ["Sharingan de Sasuke", "Sharingan d'Itachi", "Sharingan de Madara", "Sharingan de Kakashi"], "correct_index": 2, "difficulty": "moyen", "category": "Naruto"},
    {"question": "Quel animé met en scène un garçon qui contrôle les titans ?", "options": ["Tokyo Ghoul", "Attack on Titan", "Seraph of the End", "Parasyte"], "correct_index": 1, "difficulty": "facile", "category": "Attack on Titan"},
    {"question": "Dans Death Note, quel est le vrai nom de Kira ?", "options": ["L", "Near", "Light Yagami", "Mello"], "correct_index": 2, "difficulty": "facile", "category": "Death Note"},
    {"question": "Qui est le capitaine de la 5e division dans Bleach ?", "options": ["Shinji Hirako", "Sosuke Aizen", "Byakuya Kuchiki", "Toshiro Hitsugaya"], "correct_index": 1, "difficulty": "moyen", "category": "Bleach"},
    {"question": "Dans Fullmetal Alchemist, quel est le nom du frère d'Edward ?", "options": ["Roy Mustang", "Alphonse Elric", "Van Hohenheim", "Scar"], "correct_index": 1, "difficulty": "moyen", "category": "Fullmetal Alchemist"},
    {"question": "Quel animé de studio Ghibli met en scène une fille qui travaille chez sa tante sorcière ?", "options": ["Le Voyage de Chihiro", "Kiki la Petite Sorcière", "Mon Voisin Totoro", "Le Château Ambulant"], "correct_index": 1, "difficulty": "moyen", "category": "Ghibli"},
    {"question": "Dans Hunter x Hunter, quel type de Nen est spécialisé dans la manipulation ?", "options": ["Emission", "Manipulation", "Matérialisation", "Transformation"], "correct_index": 1, "difficulty": "difficile", "category": "Hunter x Hunter"},
    {"question": "Quel est le nom du personnage principal de Cowboy Bebop ?", "options": ["Jet Black", "Spike Spiegel", "Vicious", "Faye Valentine"], "correct_index": 1, "difficulty": "difficile", "category": "Cowboy Bebop"},
    {"question": "Dans Evangelion, quel est le numéro de l'EVA de Shinji ?", "options": ["EVA-00", "EVA-01", "EVA-02", "EVA-03"], "correct_index": 1, "difficulty": "difficile", "category": "Evangelion"},
    {"question": "Quelle technique utilise le Hachimon Tonko no Jin ?", "options": ["Rasengan", "Chidori", "Sharingan", "Byakugan"], "correct_index": 1, "difficulty": "legendaire", "category": "Naruto"},
    {"question": "Dans JoJo's Bizarre Adventure, quel est le Stand de Jotaro ?", "options": ["The World", "Star Platinum", "Gold Experience", "Crazy Diamond"], "correct_index": 1, "difficulty": "legendaire", "category": "JoJo"},
    {"question": "Quel est le véritable nom du héros dans One Punch Man ?", "options": ["Genos", "Saitama", "King", "Mumen Rider"], "correct_index": 1, "difficulty": "difficile", "category": "One Punch Man"},
]

DIFFICULTY_POINTS = {"facile": 5, "moyen": 10, "difficile": 15, "legendaire": 20}

LEVEL_THRESHOLDS = [
    (90, "legendary"),
    (75, "master"),
    (55, "senior"),
    (0, "junior"),
]


def _generate_questions_data(theme: Optional[str] = None):
    try:
        questions = gemini_quiz.generate_questions(theme=theme)
    except Exception:
        import random
        questions = random.sample(MOCK_QUESTIONS, 10)
    return questions


def _score_to_level(pct: int) -> str:
    for threshold, level in LEVEL_THRESHOLDS:
        if pct >= threshold:
            return level
    return "junior"


# --- Routes ---

@router.post("/start", response_model=StartResponse)
async def start_quiz(
    theme: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    questions_data = _generate_questions_data(theme)

    session = ExamSession(user_id=user.id, status="in_progress")
    db.add(session)
    await db.flush()

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
    await db.flush()

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
async def get_current_quiz(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExamSession).where(
            ExamSession.id == session_id,
            ExamSession.user_id == user.id,
            ExamSession.status == "in_progress",
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable ou déjà terminée")

    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.exam_session_id == session_id)
    )
    questions = result.scalars().all()

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
async def submit_quiz(
    req: SubmitRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExamSession).where(
            ExamSession.id == req.session_id,
            ExamSession.user_id == user.id,
            ExamSession.status == "in_progress",
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable ou déjà terminée")

    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.exam_session_id == req.session_id)
    )
    questions = result.scalars().all()

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
async def congratulate(
    req: CongratulateRequest,
    user: User = Depends(get_current_user),
):
    try:
        message = gemini_quiz.generate_congratulation(req.username, req.level, req.score)
    except Exception:
        message = f"Félicitations {req.username} ! Tu as obtenu le niveau {req.level} avec {req.score}% !"

    return {"message": message}
