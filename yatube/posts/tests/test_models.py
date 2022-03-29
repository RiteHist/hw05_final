from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        group = PostModelTest.group
        post = PostModelTest.post
        group_string = group.__str__()
        post_string = post.__str__()
        self.assertEqual(group_string,
                         'Тестовая группа',
                         'group.__str__() не работает'
                         )

        self.assertEqual(post_string,
                         'Тестовый пост',
                         'post.__str__() не работает'
                         )

        post.text = 'Тестовый пост размером больше 15 символов'
        post.save()
        post_string = post.__str__()
        result_string = 'Тестовый пост размером больше 15 символов'
        self.assertEqual(post_string,
                         result_string[:15],
                         'post.__str__() не работает с более чем 15 символами'
                         )
