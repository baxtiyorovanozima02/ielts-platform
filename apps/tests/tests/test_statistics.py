from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Section, Test, UserTestResult, SpeakingResult

User = get_user_model()


class StatisticsTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)

        self.section = Section.objects.create(name='writing', description='Writing')
        self.speaking_section = Section.objects.create(name='speaking', description='Speaking')

        self.test = Test.objects.create(
            title='Writing Test',
            section=self.section,
            is_active=True
        )
        self.speaking_test = Test.objects.create(
            title='Speaking Test',
            section=self.speaking_section,
            is_active=True
        )

        UserTestResult.objects.create(
            user=self.user, test=self.test,
            essay_text='Essay 1', band_score=6.0
        )
        UserTestResult.objects.create(
            user=self.user, test=self.test,
            essay_text='Essay 2', band_score=7.0
        )
        SpeakingResult.objects.create(
            user=self.user, test=self.speaking_test,
            transcript='Speaking 1', band_score=5.5
        )

    def test_band_score_history(self):
        url = reverse('band-score-history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('writing', response.data)
        self.assertIn('speaking', response.data)
        self.assertEqual(len(response.data['writing']), 2)
        self.assertEqual(len(response.data['speaking']), 1)

    def test_overall_progress(self):
        url = reverse('overall-progress')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['writing']['average_band_score'], 6.5)
        self.assertEqual(response.data['writing']['total_tests'], 2)
        self.assertEqual(response.data['speaking']['average_band_score'], 5.5)

    def test_weak_areas(self):
        url = reverse('weak-areas')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('weak_areas', response.data)
        self.assertIn('all_areas', response.data)
        weak_sections = [a['section'] for a in response.data['weak_areas']]
        self.assertIn('speaking', weak_sections)

    def test_unauthenticated(self):
        self.client.logout()
        url = reverse('band-score-history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_overall_only_own(self):
        other_user = User.objects.create_user(username='other', password='pass123!')
        UserTestResult.objects.create(
            user=other_user, test=self.test,
            essay_text='Other', band_score=9.0
        )
        url = reverse('overall-progress')
        response = self.client.get(url)
        self.assertEqual(response.data['writing']['average_band_score'], 6.5)