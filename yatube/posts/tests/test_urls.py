from http import HTTPStatus
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='post_author')
        cls.user_not_author = User.objects.create(username='Test_not_author')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

        cls.templates_user_URLs_names = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user.username}/',
            f'/posts/{cls.post.id}/',
        ]

        cls.templates_not_author_URLs_names = [
            '/create/',
        ]

        cls.templates_author_URLs_names = [
            f'/posts/{cls.post.id}/edit/',
        ]

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

    def test_user_urls_at_desired_location(self):
        for url in self.templates_user_URLs_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_author_urls_at_desired_location(self):
        merged_list = (self.templates_user_URLs_names + (
            self.templates_not_author_URLs_names))
        for url in merged_list:
            with self.subTest(url=url):
                response = self.authorized_client_not_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_urls_at_desired_location(self):
        merged_list = (self.templates_user_URLs_names + (
            self.templates_not_author_URLs_names + (
                self.templates_author_URLs_names)))
        for url in merged_list:
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect(self):
        new_col = [
            ['/create/', '/auth/login/?next=/create/', self.guest_client],
            [f'/posts/{self.post.id}/edit/',
             '/auth/login/?next=/posts/1/edit/', self.guest_client],
            [f'/posts/{self.post.id}/edit/',
             f'/posts/{self.post.id}/', self.authorized_client_not_author],
            [f'/posts/{self.post.id}/comment/',
             '/auth/login/?next=/posts/1/comment/', self.guest_client]
        ]
        for url, address, loosers in new_col:
            with self.subTest(url=url):
                response = loosers.get(url, follow=True)
                self.assertRedirects(response, address)

    def test_urls_incorrect_name(self):
        """Запрос к несуществующей странице"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client_author.get(url)
                self.assertTemplateUsed(response, template)
