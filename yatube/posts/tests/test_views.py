import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django import forms
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Comments, Follow, Group, Post, User

NUM_OF_POSTS: int = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='post_author')
        cls.follower = User.objects.create(username='follower')
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
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_for_author_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': self.user}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        response = self.authorized_client.get(reverse("posts:index"))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_list_pages_show_correct_context(self):
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})))
        self.assertEqual(response.context.get(
            'group').title, self.group.title)
        self.assertEqual(response.context.get('group').slug, self.group.slug)

    def test_profile_pages_show_correct_context(self):
        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})))
        self.assertEqual(response.context.get(
            'author').username, 'post_author')
        self.assertEqual(response.context.get('posts_count'), 1)

    def test_post_detail_pages_show_correct_context(self):
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').image, self.post.image)
        self.assertEqual(response.context.get('author_post'), 1)

    def test_post_create_pages_show_correct_context(self):
        response = (self.authorized_client.get(reverse('posts:post_create')))
        form_fields = {
            'group': forms.models.ModelChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_is_correct(self):
        test_post = Post.objects.create(
            author=self.user,
            text='Дополнительный тестовый пост',
            group=Group.objects.get(slug='test_slug')
        )
        list_page_name = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={'username': 'post_author'}),
        )
        for name_page in list_page_name:
            with self.subTest(name_page=name_page):
                response = self.authorized_client.get(name_page)
                first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, test_post)

    def test_authorized_user_follow(self):
        """Проверяем подписку у авторизованного пользователя"""
        follower_post = Post.objects.create(
            author=self.follower,
            text='Тестовый пост фоловера',
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context["page_obj"]), 0)
        # Проверяем подписку на автора поста
        Follow.objects.get_or_create(
            user=self.user, author=self.follower
        )
        response_folowing = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response_folowing.context["page_obj"]), 1)
        self.assertIn(follower_post, response_folowing.context["page_obj"])
        follow_user = Follow.objects.get(author=self.follower, user=self.user)
        self.assertIsNotNone(follow_user, (
            ' Пользователь не может подписаться сам на себя'))

    def test_user_unfollow(self):
        """Отписка"""
        Follow.objects.all().delete()
        response = self.authorized_client.get(
            reverse("posts:follow_index")
        )
        self.assertEqual(len(response.context["page_obj"]), 0)

    def test_user_nofolower(self):
        """Проверям, что новый пост не добавился в избранное у не подписчика"""
        nofollower = User.objects.create(username='test_name4')
        self.authorized_client.force_login(nofollower)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context["page_obj"])

    def test_url_follow(self):
        follow_url = reverse(
            'posts:profile_follow', kwargs={
                'username': self.post.author.username}
        )
        response = self.authorized_client.post(follow_url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_url_unfollow(self):
        unfollow_url = reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.post.author.username})
        response = self.authorized_client.post(unfollow_url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_pages_show_correct_context(self):
        response = (self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context['is_edit'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user2 = User.objects.create_user(username='post_author')
        cls.group2 = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for cls.new_post in range(NUM_OF_POSTS):
            cls.post = Post.objects.create(
                text=f'Тестовый пост {cls.new_post}' * 20,
                group=cls.group2,
                author=cls.user2,
            )
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)
        cls.list_of_pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group2.slug}),
            reverse('posts:profile', kwargs={'username': cls.user2}),
        )

    def test_first_page_contains_ten_records(self):
        for name_page in self.list_of_pages:
            with self.subTest(name_page=name_page):
                response = self.authorized_client2.get(name_page)
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_records(self):
        for name_page in self.list_of_pages:
            with self.subTest(name_page=name_page):
                response = self.authorized_client2.get((name_page) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
