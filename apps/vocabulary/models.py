from django.conf import settings
from django.db import models


class Word(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='words')
    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=200)
    example = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word


class WordReview(models.Model):
    QUALITY_CHOICES = [
        (0, 'Umuman bilmadim'),
        (1, 'Qiyin bo\'ldi'),
        (2, 'Esladim'),
        (3, 'Oson bo\'ldi'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='word_reviews')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='reviews')
    quality = models.IntegerField(choices=QUALITY_CHOICES)
    next_review = models.DateTimeField()
    interval = models.IntegerField(default=1)
    repetitions = models.IntegerField(default=0)
    ease_factor = models.FloatField(default=2.5)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.word.word}"