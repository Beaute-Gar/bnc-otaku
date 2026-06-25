"""
Module 1 - Moteur de Quiz IA (Gemini)
======================================
Génère des questions de quiz anime inédites avec niveaux de difficulté.
Utilise google-genai SDK (gemini-2.0-flash) avec fallback.
AUCUNE clé API en dur - tout vient du .env.
"""

import json
import re
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.config import settings

# Import google-genai (nouveau SDK)
try:
    from google import genai
    from google.genai import types as genai_types
    _HAS_GENAI = True
except ImportError:
    _HAS_GENAI = False

# Fallback vers l'ancien SDK
try:
    import google.generativeai as genai_legacy
    _HAS_LEGACY = True
except ImportError:
    _HAS_LEGACY = False

if not _HAS_GENAI and not _HAS_LEGACY:
    raise ImportError("Aucun SDK Google Generative AI trouvé. Installez google-genai ou google-generativeai.")


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


class GeminiQuizGenerator:
    """Générateur de quiz via Gemini AI."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self._client = None
        if self.api_key:
            self._init_client()

    def _ensure_client(self):
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY non configurée dans .env. Configure-la dans le fichier .env")
        if not self._client:
            self._init_client()

    def _init_client(self):
        if _HAS_GENAI:
            self._client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-2.0-flash"
            self._generate = self._generate_new
        else:
            genai_legacy.configure(api_key=self.api_key)
            self._client = genai_legacy.GenerativeModel("gemini-1.5-flash")
            self._generate = self._generate_legacy

    def _generate_new(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.9,
                top_p=0.95,
                max_output_tokens=4096,
            ),
        )
        return response.text

    def _generate_legacy(self, prompt: str) -> str:
        import os, sys
        # Timeout de sécurité via thread : 30s max
        import threading
        result = []
        exception = []

        def worker():
            try:
                r = self._client.generate_content(prompt)
                result.append(r.text)
            except Exception as e:
                exception.append(e)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        t.join(timeout=30)
        if t.is_alive():
            raise TimeoutError("Gemini API timeout (30s)")
        if exception:
            raise exception[0]
        return result[0]

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
