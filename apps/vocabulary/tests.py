from datetime import datetime, timezone, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Word, WordReview

User = get_user_model()


class VocabularyTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        self.word = Word.objects.create(
            user=self.user,
            word='ubiquitous',
            translation='hamma joyda mavjud',
            example='Technology is ubiquitous in modern life.'
        )

    def test_word_list(self):
        url = reverse('word-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_word_create(self):
        url = reverse('word-list')
        response = self.client.post(url, {
            'word': 'ambiguous',
            'translation': 'noaniq',
            'example': 'The answer was ambiguous.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Word.objects.filter(user=self.user).count(), 2)

    def test_word_detail(self):
        url = reverse('word-detail', kwargs={'pk': self.word.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['word'], 'ubiquitous')

    def test_word_delete(self):
        url = reverse('word-detail', kwargs={'pk': self.word.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_word_only_own(self):
        other_user = User.objects.create_user(username='other', password='pass123!')
        Word.objects.create(user=other_user, word='test', translation='test')
        url = reverse('word-list')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_due_words_empty(self):
        WordReview.objects.create(
            user=self.user,
            word=self.word,
            quality=3,
            next_review=datetime.now(timezone.utc) + timedelta(days=5),
            interval=5
        )
        url = reverse('due-words')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_due_words_has_due(self):
        WordReview.objects.create(
            user=self.user,
            word=self.word,
            quality=1,
            next_review=datetime.now(timezone.utc) - timedelta(days=1),
            interval=1
        )
        url = reverse('due-words')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_word_review_success(self):
        url = reverse('word-review')
        response = self.client.post(url, {'word_id': self.word.id, 'quality': 3})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('next_review', response.data)

    def test_word_review_invalid_quality(self):
        url = reverse('word-review')
        response = self.client.post(url, {'word_id': self.word.id, 'quality': 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated(self):
        self.client.logout()
        url = reverse('word-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)