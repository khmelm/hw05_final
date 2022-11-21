from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


NUM_OF_POSTS: int = 13


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2',
        )
        for cls.new_post in range(NUM_OF_POSTS):
            cls.post = Post.objects.create(
                text=f'Тестовый пост {cls.new_post}',
                group=cls.group,
                author=cls.user,
            )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostCreateFormTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateFormTests.group.id,
            ).exists()
        )

    def test_post_edit(self):
        form_data = {
            'text': 'Измененный пост',
            'group': self.group2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,)),
        )
        self.post = Post.objects.get(id=self.post.id)
        self.assertEqual(self.post.text, 'Измененный пост')
        self.assertEqual(self.post.group.title, 'Тестовая группа 2')

    def test_post_is_not_created_by_user(self):
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create',)
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)
