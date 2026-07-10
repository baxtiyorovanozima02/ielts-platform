from django.conf import settings
from django.db import models


class Section(models.Model):
    SECTION_CHOICES = [
        ('reading', 'Reading'),
        ('listening', 'Listening'),
        ('writing', 'Writing'),
        ('speaking', 'Speaking'),
    ]
    name = models.CharField(max_length=20, choices=SECTION_CHOICES, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Test(models.Model):
    title = models.CharField(max_length=200)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='tests')
    duration_minutes = models.IntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    audio_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('essay', 'Essay'),
    ]

    SPEAKING_PART_CHOICES = [
        (1, 'Part 1 - Introduction & Interview'),
        (2, 'Part 2 - Cue Card'),
        (3, 'Part 3 - Discussion'),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    text = models.TextField()
    order = models.IntegerField(default=0)

    part = models.IntegerField(
        choices=SPEAKING_PART_CHOICES,
        null=True,
        blank=True,
        help_text="Faqat speaking testlar uchun to'ldiriladi (1, 2 yoki 3)."
    )
    prep_seconds = models.IntegerField(
        default=0,
        help_text="Tayyorlanish vaqti (soniya). Part 2 uchun odatda 60."
    )
    answer_seconds = models.IntegerField(
        default=120,
        help_text="Javob berish uchun ajratilgan vaqt (soniya)."
    )
    cue_card_points = models.TextField(
        blank=True,
        help_text="Part 2 cue card punktlari. Har birini yangi qatordan yozing."
    )

    class Meta:
        ordering = ['test', 'part', 'order']

    def __str__(self):
        return f"{self.test.title} - Q{self.order}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class UserTestResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='results')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results')
    essay_text = models.TextField()
    ai_feedback = models.TextField(blank=True)
    band_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.title}"


class ExaminerVoice(models.Model):
    """Foydalanuvchi mock speaking testni boshlashdan oldin tanlaydigan 'examiner' ovozi."""

    GENDER_CHOICES = [
        ('male', 'Erkak'),
        ('female', 'Ayol'),
    ]
    ACCENT_CHOICES = [
        ('british', 'British'),
        ('american', 'American'),
        ('australian', 'Australian'),
    ]

    name = models.CharField(max_length=50, help_text="Masalan: 'Emma (British)'")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    accent = models.CharField(max_length=20, choices=ACCENT_CHOICES)
    tts_voice_id = models.CharField(
        max_length=100,
        help_text="TTS provayderdagi ovoz identifikatori (masalan, ElevenLabs voice_id)."
    )
    avatar_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Avatar provayderdagi (masalan, HeyGen) avatar identifikatori. Bo'sh bo'lsa standart avatar ishlatiladi."
    )
    preview_audio_url = models.URLField(
        blank=True, null=True,
        help_text="Foydalanuvchi tanlashdan oldin eshitib ko'radigan namuna audio."
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_gender_display()}, {self.get_accent_display()})"


class SpeakingSession(models.Model):
    """Bitta to'liq mock speaking imtihon urinishi: Part1 -> Part2 -> Part3 holatini saqlaydi."""

    STATUS_CHOICES = [
        ('in_progress', 'Davom etmoqda'),
        ('completed', 'Tugallangan'),
        ('abandoned', 'Tashlab ketilgan'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='speaking_sessions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='speaking_sessions')
    voice = models.ForeignKey(
        ExaminerVoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions'
    )

    current_part = models.IntegerField(default=1)
    current_question_order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.title} - {self.get_status_display()}"


class SpeakingSessionAnswer(models.Model):
    """Session ichidagi har bir savolga foydalanuvchi bergan alohida javob (audio + transkript)."""

    session = models.ForeignKey(SpeakingSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='speaking_answers')
    audio_file = models.FileField(upload_to='speaking_session_audio/', null=True, blank=True)
    transcript = models.TextField(blank=True)
    duration_seconds = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'answered_at']

    def __str__(self):
        return f"Session {self.session_id} - Q{self.question_id}"


class SpeakingResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='speaking_results')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='speaking_results')
    session = models.ForeignKey(
        SpeakingSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='results',
        help_text="Agar bu natija to'liq Part1-3 mock sessiyasidan bo'lsa, shu sessiyaga bog'lanadi."
    )
    audio_file = models.FileField(upload_to='speaking_audio/', null=True, blank=True)
    transcript = models.TextField(blank=True)
    ai_feedback = models.TextField(blank=True)
    band_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Speaking - {self.test.title}"


class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='progress')
    average_band_score = models.FloatField(default=0.0)
    total_tests_taken = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'section')

    def __str__(self):
        return f"{self.user.username} - {self.section.name} - {self.average_band_score}"


class DailyPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_plans')
    date = models.DateField(auto_now_add=True)
    plan_text = models.TextField()
    ai_generated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} - {self.date}"