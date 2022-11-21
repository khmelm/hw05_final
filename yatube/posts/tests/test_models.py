from django.test import TestCase

from ..models import Comments, Follow, Group, Post, User

NUM_OF_SYMBOLS = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.comment = Comments.objects.create(
            post=cls.post,
            author=cls.author,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.author
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.group.title, str(self.group))
        self.assertEqual(self.post.text[:NUM_OF_SYMBOLS], str(self.post))
        self.assertEqual(self.comment.text, str(self.comment))
        self.assertEqual(
            self.follow.PHRASE_FOLLOW.format(key_user=self.follower,
                                             key_author=self.author),
            str(self.follow))
