from django.db import models
from django.conf import settings

from apps.tests.models import Test, ExaminerVoice


class LiveSpeakingSession(models.Model):
    """AI avatar bilan real-vaqt ovozli suhbat sessiyasi (Part 1-3 kabi emas, erkin suhbat)."""

    STATUS_CHOICES = [
        ('connecting', 'Ulanmoqda'),
        ('active', 'Faol'),
        ('ended', 'Tugagan'),
        ('error', 'Xatolik'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='live_speaking_sessions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='live_speaking_sessions', null=True, blank=True)
    voice = models.ForeignKey(ExaminerVoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='live_sessions')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='connecting')

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} - Live session #{self.pk} - {self.get_status_display()}"


class LiveSpeakingMessage(models.Model):
    """Suhbatdagi har bir alohida xabar: yoki foydalanuvchi (user), yoki AI examiner (assistant)."""

    ROLE_CHOICES = [
        ('user', 'Foydalanuvchi'),
        ('assistant', 'AI Examiner'),
    ]

    session = models.ForeignKey(LiveSpeakingSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    text = models.TextField(blank=True, help_text="STT natijasi (user uchun) yoki LLM javobi (assistant uchun)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Session {self.session_id} - {self.role} - {self.created_at:%H:%M:%S}"