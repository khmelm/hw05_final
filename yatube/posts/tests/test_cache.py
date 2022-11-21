from django.core.cache import cache
from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Comments, Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            image=cls.uploaded
        )
        cls.comment = Comments.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Проверяем, что кэш работает_1"""
        response_1 = self.authorized_client.get(reverse("posts:index"))
        response_1_context = response_1.content
        Post.objects.all().delete
        response_2 = self.authorized_client.get(reverse("posts:index"))
        response_2_context = response_2.content
        self.assertEqual(response_1_context, response_2_context)

    def test_cashe_02(self):
        """ Проверяем, что кэш работает_2 """
        response_1 = self.client.get(reverse("posts:index"))
        response_1_context = response_1.content
        Post.objects.all().delete
        cache.clear()
        response_2 = self.authorized_client.get(reverse("posts:index"))
        response_2_context = response_2.content
        self.assertNotEqual(response_1_context, response_2_context)
