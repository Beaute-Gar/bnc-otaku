"""
Module 1 - Moteur de Quiz IA (Gemini)
======================================
Génère des questions de quiz anime inédites avec niveaux de difficulté.
Utilise l'API REST Gemini directement (compatible toutes les clés AIzaSy... et AQ...).
"""

import json
import re
import requests
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.config import settings


# --- Constantes ---

QUIZ_SYSTEM_PROMPT = """Tu es un examinateur officiel du Bureau National de Certification Otaku (BNC-Otaku).
Génère des questions de quiz sur la culture anime/manga/japanime.

Règles strictes :
1. Génère EXACTEMENT 10 questions
2. Chaque question doit être unique et intéressante
3. Variété des époques : anime classique (années 90-2000) et moderne
4. 4 niveaux de difficulté : facile, moyen, difficile, legendaire
5. Répartition : 2 faciles, 3 moyens, 3 difficiles, 2 légendaires
6. 4 options par question (A, B, C, D), UNE seule correcte
7. Langue : français
8. Format EXACT (JSON array) :
[
  {
    "question": "Texte de la question",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "difficulty": "facile",
    "category": "Naruto"
  }
]

Ne réponds qu'avec le JSON, rien d'autre."""


DIFFICULTY_MAP = {
    "facile": 5,
    "moyen": 10,
    "difficile": 15,
    "legendaire": 20,
}


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


class GeminiQuizGenerator:
    """Générateur de quiz via Gemini API REST."""

    def __init__(self):
        self.api_key = settings.gemini_api_key

    def _ensure_client(self):
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY non configurée dans .env.")

    def _generate(self, prompt: str) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.9,
                "topP": 0.95,
                "maxOutputTokens": 4096,
            },
        }
        resp = requests.post(
            f"{GEMINI_API_URL}?key={self.api_key}",
            json=payload,
            timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Aucune réponse générée par Gemini")
        return candidates[0]["content"]["parts"][0]["text"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    def generate_questions(self, theme: Optional[str] = None) -> List[Dict]:
        self._ensure_client()
        prompt = QUIZ_SYSTEM_PROMPT
        if theme:
            prompt += f"\nThème spécifique : {theme}"

        raw = self._generate(prompt)

        # Extraction du JSON (l'IA peut ajouter des markdown)
        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not json_match:
            raise ValueError(f"Réponse IA invalide (pas de JSON trouvé) : {raw[:200]}")

        questions = json.loads(json_match.group(0))

        if not isinstance(questions, list) or len(questions) != 10:
            raise ValueError(f"Nombre de questions invalide : {len(questions)}")

        # Validation et normalisation
        for q in questions:
            if not all(k in q for k in ("question", "options", "correct_index", "difficulty")):
                raise ValueError(f"Question mal formée : {q}")
            if len(q["options"]) != 4:
                raise ValueError(f"Nombre d'options invalide : {len(q['options'])}")
            if q["difficulty"] not in DIFFICULTY_MAP:
                q["difficulty"] = "moyen"

        return questions

    def calculate_score(self, questions: List[Dict], answers: List[int]) -> tuple:
        """
        Calcule le score et le niveau.
        Retourne (score_sur_100, niveau).
        """
        total_points = 0
        max_points = 0

        for q, ans in zip(questions, answers):
            pts = DIFFICULTY_MAP.get(q.get("difficulty", "moyen"), 10)
            max_points += pts
            if q["correct_index"] == ans:
                total_points += pts

        score = round((total_points / max_points) * 100) if max_points > 0 else 0

        if score >= 90:
            level = "legendary"
        elif score >= 75:
            level = "master"
        elif score >= 55:
            level = "senior"
        else:
            level = "junior"

        return score, level

    def generate_congratulation(self, username: str, level: str, score: int) -> str:
        self._ensure_client()
        """Génère un message de félicitations personnalisé via Gemini."""
        prompt = f"""Tu es un examinateur officiel du BNC-Otaku. Félicite chaleureusement {username} qui a obtenu le niveau '{level}' avec un score de {score}% à l'examen national otaku.

Style : humoristique, références anime, motivant. 2-3 phrases max. En français."""
        return self._generate(prompt)


# Instance singleton
gemini_quiz = GeminiQuizGenerator()
