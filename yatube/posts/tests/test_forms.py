import tempfile
import shutil
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import Post, Group, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testboy')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.client.force_login(PostsFormTests.user)

    def test_can_create_new_post(self):
        """ Проверка, что post_create создает новый пост. """
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image = SimpleUploadedFile(
            name='test.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form = {
            'text': 'Тест создания поста',
            'group': PostsFormTests.group.id,
            'image': image
        }
        response = self.client.post(reverse('posts:post_create'),
                                    form, follow=True)
        username = PostsFormTests.user.username
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': username}))
        self.assertTrue(
            Post.objects.filter(
                text='Тест создания поста',
                group=PostsFormTests.group,
                author=PostsFormTests.user,
                image='posts/test.gif'
            ).exists()
        )

    def test_can_edit_existing_post(self):
        """ Проверка, что post_edit редактирует существующий пост"""
        form = {
            'text': 'Тест изменения поста',
            'group': PostsFormTests.group.id
        }
        post_id = PostsFormTests.post.id
        response = (self.client.post(reverse('posts:post_edit',
                                             kwargs={'post_id': post_id}),
                                     form,
                                     follow=True,
                                     kwargs={'post_id': post_id}))

        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        self.assertTrue(
            Post.objects.filter(
                pk=1,
                text='Тест изменения поста',
                group=PostsFormTests.group,
                author=PostsFormTests.user
            ).exists()
        )

    def test_can_create_comment(self):
        """
        Проверка, что комментарий появляется
        на странице поста после отправки.
        """
        form = {
            'text': "Тестовый комментарий",
        }
        post_id = PostsFormTests.post.id
        response = (self.client.post(reverse('posts:add_comment',
                                             kwargs={'post_id': post_id}),
                                     form,
                                     follow=True,
                                     kwargs={'post_id': post_id}))

        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        self.assertTrue(
            Comment.objects.filter(
                pk=1,
                text='Тестовый комментарий',
                author=PostsFormTests.user,
                post=PostsFormTests.post
            ).exists()
        )
