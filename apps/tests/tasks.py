from celery import shared_task
from django.conf import settings
import requests


@shared_task
def evaluate_writing_task(result_id):
    from .models import UserTestResult
    try:
        result = UserTestResult.objects.get(id=result_id)
    except UserTestResult.DoesNotExist:
        return

    prompt = f"""
    You are an IELTS examiner. Evaluate the following essay and provide:
    1. Band score (0-9)
    2. Task Achievement feedback
    3. Coherence and Cohesion feedback
    4. Lexical Resource feedback
    5. Grammatical Range feedback

    Essay: {result.essay_text}

    Respond in this format:
    Band Score: X
    Feedback: ...
    """

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    response_data = response.json()
    ai_feedback = response_data['choices'][0]['message']['content']

    band_line = ai_feedback.split('\n')[0]
    try:
        band_score = float(band_line.split(':')[1].strip())
    except Exception:
        band_score = None

    result.ai_feedback = ai_feedback
    result.band_score = band_score
    result.save()


@shared_task
def evaluate_speaking_task(result_id):
    from .models import SpeakingResult
    try:
        result = SpeakingResult.objects.get(id=result_id)
    except SpeakingResult.DoesNotExist:
        return

    prompt = f"""
    You are an IELTS examiner. Evaluate the following speaking transcript and provide:
    1. Band score (0-9)
    2. Fluency and Coherence feedback
    3. Lexical Resource feedback
    4. Grammatical Range and Accuracy feedback
    5. Pronunciation feedback

    Transcript: {result.transcript}

    Respond in this format:
    Band Score: X
    Feedback: ...
    """

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    response_data = response.json()
    ai_feedback = response_data['choices'][0]['message']['content']

    band_line = ai_feedback.split('\n')[0]
    try:
        band_score = float(band_line.split(':')[1].strip())
    except Exception:
        band_score = None

    result.ai_feedback = ai_feedback
    result.band_score = band_score
    result.save()


@shared_task
def generate_daily_plan_task(user_id):
    from django.contrib.auth import get_user_model
    from .models import UserProgress, DailyPlan
    from datetime import date

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    progress = UserProgress.objects.filter(user=user).select_related('section')
    if not progress.exists():
        return

    progress_text = "\n".join([
        f"{p.section.name}: average band score {p.average_band_score}, total tests {p.total_tests_taken}"
        for p in progress
    ])

    prompt = f"""
    You are an IELTS coach. Based on the student's progress below, create a personalized daily study plan for today.

    Student Progress:
    {progress_text}

    Create a specific, actionable daily plan with time allocations for each skill.
    Focus more on weaker areas. Keep it concise and motivating.
    """

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    response_data = response.json()
    plan_text = response_data['choices'][0]['message']['content']

    DailyPlan.objects.update_or_create(
        user=user,
        date=date.today(),
        defaults={'plan_text': plan_text, 'ai_generated': True}
    )