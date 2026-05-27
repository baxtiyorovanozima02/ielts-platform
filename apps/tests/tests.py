from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Section, Test, Question, Answer, UserTestResult, SpeakingResult

User = get_user_model()


class BaseTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.client.force_authenticate(user=self.user)

        self.section = Section.objects.create(
            name='writing',
            description='Writing section'
        )
        self.speaking_section = Section.objects.create(
            name='speaking',
            description='Speaking section'
        )
        self.test = Test.objects.create(
            title='Writing Test 1',
            section=self.section,
            duration_minutes=60,
            is_active=True
        )
        self.speaking_test = Test.objects.create(
            title='Speaking Test 1',
            section=self.speaking_section,
            duration_minutes=15,
            is_active=True
        )


class SectionListViewTest(BaseTestCase):

    def test_section_list_authenticated(self):
        url = reverse('section-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_section_list_unauthenticated(self):
        self.client.logout()
        url = reverse('section-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestListViewTest(BaseTestCase):

    def test_test_list(self):
        url = reverse('test-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_test_list_filter_by_section(self):
        url = reverse('test-list') + '?section=writing'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_inactive_test_not_shown(self):
        Test.objects.create(
            title='Inactive Test',
            section=self.section,
            is_active=False
        )
        url = reverse('test-list')
        response = self.client.get(url)
        titles = [t['title'] for t in response.data]
        self.assertNotIn('Inactive Test', titles)

    def test_test_detail(self):
        url = reverse('test-detail', kwargs={'pk': self.test.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_test_detail_not_found(self):
        url = reverse('test-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WritingEvaluationViewTest(BaseTestCase):

    def _mock_response(self, band_score=7.0):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'choices': [{
                'message': {
                    'content': f'Band Score: {band_score}\nFeedback: Good essay.'
                }
            }]
        }
        return mock_resp

    @patch('apps.tests.views.requests.post')
    def test_writing_evaluation_success(self, mock_post):
        mock_post.return_value = self._mock_response(7.0)
        url = reverse('writing-evaluate', kwargs={'test_id': self.test.pk})
        response = self.client.post(url, {'essay_text': 'Climate change is a serious issue.'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['band_score'], 7.0)

    def test_writing_evaluation_missing_essay(self):
        url = reverse('writing-evaluate', kwargs={'test_id': self.test.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_writing_evaluation_test_not_found(self):
        url = reverse('writing-evaluate', kwargs={'test_id': 9999})
        response = self.client.post(url, {'essay_text': 'Some text'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.tests.views.requests.post')
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


class SpeakingEvaluationViewTest(BaseTestCase):

    def _mock_response(self, band_score=6.5):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'choices': [{
                'message': {
                    'content': f'Band Score: {band_score}\nFeedback: Good speaking.'
                }
            }]
        }
        return mock_resp

    @patch('apps.tests.views.requests.post')
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

    @patch('apps.tests.views.requests.post')
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