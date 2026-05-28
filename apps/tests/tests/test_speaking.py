from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Section, Test, SpeakingResult

User = get_user_model()


class SpeakingEvaluationViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        self.section = Section.objects.create(name='speaking', description='Speaking section')
        self.speaking_test = Test.objects.create(
            title='Speaking Test 1',
            section=self.section,
            duration_minutes=15,
            is_active=True
        )

    def _mock_response(self, band_score=6.5):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'choices': [{'message': {'content': f'Band Score: {band_score}\nFeedback: Good speaking.'}}]
        }
        return mock_resp

    @patch('apps.tests.views.speaking.requests.post')
    def test_speaking_evaluation_success(self, mock_post):
        mock_post.return_value = self._mock_response(6.5)
        url = reverse('speaking-evaluate', kwargs={'test_id': self.speaking_test.pk})
        response = self.client.post(url, {'transcript': 'Technology is important.'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['band_score'], 6.5)

    def test_speaking_evaluation_no_input(self):
        url = reverse('speaking-evaluate', kwargs={'test_id': self.speaking_test.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_speaking_evaluation_test_not_found(self):
        url = reverse('speaking-evaluate', kwargs={'test_id': 9999})
        response = self.client.post(url, {'transcript': 'Some text'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.tests.views.speaking.requests.post')
    def test_speaking_result_saved_to_db(self, mock_post):
        mock_post.return_value = self._mock_response(7.0)
        url = reverse('speaking-evaluate', kwargs={'test_id': self.speaking_test.pk})
        self.client.post(url, {'transcript': 'Technology helps us.'})
        self.assertEqual(SpeakingResult.objects.filter(user=self.user).count(), 1)

    def test_speaking_results_list(self):
        SpeakingResult.objects.create(
            user=self.user, test=self.speaking_test,
            transcript='Sample', ai_feedback='Well done', band_score=7.0
        )
        url = reverse('speaking-results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_speaking_results_only_own(self):
        other_user = User.objects.create_user(username='other2', password='pass123!')
        SpeakingResult.objects.create(
            user=other_user, test=self.speaking_test,
            transcript='Other', ai_feedback='OK', band_score=5.5
        )
        url = reverse('speaking-results')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)

    def test_unauthenticated_cannot_access(self):
        self.client.logout()
        url = reverse('speaking-evaluate', kwargs={'test_id': self.speaking_test.pk})
        response = self.client.post(url, {'transcript': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)