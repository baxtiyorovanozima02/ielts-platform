from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Section, Test, Question, Answer

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