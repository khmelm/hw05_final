from django.test import TestCase
from http import HTTPStatus


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_error_uses_correct_template(self):
        template = 'core/404.html'
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, template)
