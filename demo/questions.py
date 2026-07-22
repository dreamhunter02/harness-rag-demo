from __future__ import annotations

import json
from functools import lru_cache

from demo.config import ROOT
from demo.models import Question


QUESTIONS_PATH = ROOT / "fixtures" / "questions.json"


@lru_cache(maxsize=1)
def load_questions() -> list[Question]:
    return [Question.model_validate(item) for item in json.loads(QUESTIONS_PATH.read_text())]


def get_question(question_id: str) -> Question:
    for question in load_questions():
        if question.id == question_id:
            return question
    raise KeyError(question_id)
