from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import JSON
from backend.database import Base


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, default=None)
    status = Column(Enum("in_progress", "completed", "abandoned", name="exam_status"), nullable=False, default="in_progress")
    score = Column(Integer, default=None)
    level = Column(Enum("junior", "senior", "master", "legendary", name="exam_level"), default=None)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exam_session_id = Column(Integer, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    correct_index = Column(Integer, nullable=False)
    difficulty = Column(Enum("facile", "moyen", "difficile", "legendaire", name="question_difficulty"), nullable=False)
    category = Column(String(50), default=None)
    created_at = Column(DateTime, server_default=func.now())


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    selected_index = Column(Integer, nullable=False)
    is_correct = Column(Integer, nullable=False)
    answered_at = Column(DateTime, server_default=func.now())
