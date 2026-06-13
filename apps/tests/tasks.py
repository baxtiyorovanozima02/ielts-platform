from celery import shared_task
from django.conf import settings
import requests
import re
import logging

logger = logging.getLogger(__name__)

XAI_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-4-fast-reasoning"
REQUEST_TIMEOUT = 60


def _call_openrouter(prompt: str) -> str:
    response = requests.post(
        XAI_URL,
        headers={
            "Authorization": f"Bearer {settings.XAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": XAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _extract_band_score(text: str) -> float | None:
    patterns = [
        r"band\s*score[:\s]+([0-9](?:\.[05])?)",
        r"score[:\s]+([0-9](?:\.[05])?)\s*/\s*9",
        r"\b([0-9](?:\.[05])?)\s*/\s*9\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            if 0 <= score <= 9:
                return score
    return None


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def evaluate_writing_task(self, result_id: int):
    from .models import UserTestResult

    try:
        result = UserTestResult.objects.get(id=result_id)
    except UserTestResult.DoesNotExist:
        logger.error("UserTestResult %s not found", result_id)
        return

    prompt = f"""You are an IELTS examiner. Evaluate the following essay strictly according to official IELTS Writing band descriptors.

Provide your response in this exact format:
Band Score: X.X
Task Achievement: [feedback]
Coherence and Cohesion: [feedback]
Lexical Resource: [feedback]
Grammatical Range and Accuracy: [feedback]
Overall Feedback: [2-3 sentence summary and advice]

Essay:
{result.essay_text}"""

    try:
        ai_feedback = _call_openrouter(prompt)
        band_score = _extract_band_score(ai_feedback)

        result.ai_feedback = ai_feedback
        result.band_score = band_score
        result.save(update_fields=["ai_feedback", "band_score"])

        logger.info("Writing result %s evaluated: band %.1f", result_id, band_score or 0)

    except requests.RequestException as exc:
        logger.warning("OpenRouter request failed for writing %s: %s", result_id, exc)
        raise self.retry(exc=exc)
    except Exception as exc:
        logger.exception("Unexpected error evaluating writing %s: %s", result_id, exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def evaluate_speaking_task(self, result_id: int):
    from .models import SpeakingResult

    try:
        result = SpeakingResult.objects.get(id=result_id)
    except SpeakingResult.DoesNotExist:
        logger.error("SpeakingResult %s not found", result_id)
        return

    prompt = f"""You are an IELTS examiner. Evaluate the following speaking transcript strictly according to official IELTS Speaking band descriptors.

Provide your response in this exact format:
Band Score: X.X
Fluency and Coherence: [feedback]
Lexical Resource: [feedback]
Grammatical Range and Accuracy: [feedback]
Pronunciation: [feedback]
Overall Feedback: [2-3 sentence summary and advice]

Transcript:
{result.transcript}"""

    try:
        ai_feedback = _call_openrouter(prompt)
        band_score = _extract_band_score(ai_feedback)

        result.ai_feedback = ai_feedback
        result.band_score = band_score
        result.save(update_fields=["ai_feedback", "band_score"])

        logger.info("Speaking result %s evaluated: band %.1f", result_id, band_score or 0)

    except requests.RequestException as exc:
        logger.warning("OpenRouter request failed for speaking %s: %s", result_id, exc)
        raise self.retry(exc=exc)
    except Exception as exc:
        logger.exception("Unexpected error evaluating speaking %s: %s", result_id, exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_daily_plan_task(self, user_id: int):
    from django.contrib.auth import get_user_model
    from .models import UserProgress, DailyPlan
    from datetime import date

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("User %s not found for daily plan", user_id)
        return

    progress = UserProgress.objects.filter(user=user).select_related("section")
    if not progress.exists():
        logger.info("No progress for user %s, skipping daily plan", user_id)
        return

    progress_text = "\n".join(
        f"{p.section.name}: band {p.average_band_score:.1f}, {p.total_tests_taken} tests"
        for p in progress
    )

    prompt = f"""You are an expert IELTS coach. Create a concise, personalized daily study plan based on the student's current performance.

Student Progress:
{progress_text}

Requirements:
- Total study time: 2-3 hours
- Prioritize weaker sections
- Include specific practice activities with time allocations
- Be motivating and practical
- Format with clear time blocks (e.g., "09:00-09:30: ...")"""

    try:
        plan_text = _call_openrouter(prompt)

        DailyPlan.objects.update_or_create(
            user=user,
            date=date.today(),
            defaults={"plan_text": plan_text, "ai_generated": True},
        )

        logger.info("Daily plan generated for user %s", user_id)

    except requests.RequestException as exc:
        logger.warning("OpenRouter request failed for daily plan user %s: %s", user_id, exc)
        raise self.retry(exc=exc)
    except Exception as exc:
        logger.exception("Unexpected error generating daily plan for user %s: %s", user_id, exc)