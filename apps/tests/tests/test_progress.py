from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Section, Test, UserProgress, DailyPlan

User = get_user_model()


class UserProgressViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        self.section = Section.objects.create(name='writing', description='Writing section')

    def test_progress_list_empty(self):
        url = reverse('user-progress')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_progress_list(self):
        UserProgress.objects.create(
            user=self.user,
            section=self.section,
            average_band_score=6.5,
            total_tests_taken=3
        )
        url = reverse('user-progress')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['average_band_score'], 6.5)

    def test_progress_only_own(self):
        other_user = User.objects.create_user(username='other', password='pass123!')
        UserProgress.objects.create(
            user=other_user,
            section=self.section,
            average_band_score=5.0,
            total_tests_taken=1
        )
        url = reverse('user-progress')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)

    def test_unauthenticated_cannot_access(self):
        self.client.logout()
        url = reverse('user-progress')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DailyPlanViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        self.section = Section.objects.create(name='writing', description='Writing section')

    def test_daily_plan_no_progress(self):
        url = reverse('daily-plan')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_daily_plan_existing(self):
        from datetime import date
        DailyPlan.objects.create(
            user=self.user,
            plan_text='Study writing for 1 hour.',
            ai_generated=True
        )
        url = reverse('daily-plan')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('plan_text', response.data)

    @patch('apps.tests.views.progress.requests.post')
    def test_daily_plan_generated(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'choices': [{'message': {'content': 'Study writing for 1 hour. Practice speaking for 30 minutes.'}}]
        }
        mock_post.return_value = mock_resp

        UserProgress.objects.create(
            user=self.user,
            section=self.section,
            average_band_score=6.0,
            total_tests_taken=2
        )
        url = reverse('daily-plan')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('plan_text', response.data)