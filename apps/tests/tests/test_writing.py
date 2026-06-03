from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Section, Test, UserTestResult

User = get_user_model()


class WritingEvaluationViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)
        self.section = Section.objects.create(name='writing', description='Writing section')
        self.test = Test.objects.create(
            title='Writing Test 1',
            section=self.section,
            duration_minutes=60,
            is_active=True
        )

    def _mock_response(self, band_score=7.0):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'choices': [{'message': {'content': f'Band Score: {band_score}\nFeedback: Good essay.'}}]
        }
        return mock_resp

    @patch('apps.tests.views.writing.requests.post')
    def test_writing_evaluation_success(self, mock_post):
        mock_post.return_value = self._mock_response(7.0)
        url = reverse('writing-evaluate', kwargs={'test_id': self.test.pk})
        response = self.client.post(url, {'essay_text': 'Climate change is a serious issue.'})
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('message', response.data)

    def test_writing_evaluation_missing_essay(self):
        url = reverse('writing-evaluate', kwargs={'test_id': self.test.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_writing_evaluation_test_not_found(self):
        url = reverse('writing-evaluate', kwargs={'test_id': 9999})
        response = self.client.post(url, {'essay_text': 'Some text'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.tests.views.writing.requests.post')
    def test_writing_result_saved_to_db(self, mock_post):
        mock_post.return_value = self._mock_response(6.5)
        url = reverse('writing-evaluate', kwargs={'test_id': self.test.pk})
        self.client.post(url, {'essay_text': 'Test essay.'})
        self.assertEqual(UserTestResult.objects.filter(user=self.user).count(), 1)

    def test_writing_results_list(self):
        UserTestResult.objects.create(
            user=self.user, test=self.test,
            essay_text='Sample', ai_feedback='Good', band_score=6.5
        )
        url = reverse('writing-results')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_writing_results_only_own(self):
        other_user = User.objects.create_user(username='other', password='pass123!')
        UserTestResult.objects.create(
            user=other_user, test=self.test,
            essay_text='Other', ai_feedback='OK', band_score=5.0
        )
        url = reverse('writing-results')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)