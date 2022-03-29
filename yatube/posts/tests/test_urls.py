from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Post, Group


User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='testboy')
        cls.notauthor_user = User.objects.create_user(username='notauthor')
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.notauthor_client = Client()
        self.authorized_client.force_login(PostsURLTests.author_user)
        self.notauthor_client.force_login(PostsURLTests.notauthor_user)
        self.urls = [
            '/',
            '/group/test-slug/',
            '/profile/testboy/',
            '/posts/1/',
            '/create/',
            '/posts/1/edit/',
        ]

    def test_urls_use_correct_template(self):
        """ Проверка использования адресами правильных шаблонов. """
        url_templates_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/testboy/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }

        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_available_for_unauthorized_user(self):
        """
        Проверка доступности адресов '/', /group/<slug>/,
        /profile/<username>/ и /posts/<post_id>/ для
        неавторизированного пользователя.
        """
        urls_for_unauthorized = [
            '/',
            '/group/test-slug/',
            '/profile/testboy/',
            '/posts/1/',
        ]
        for address in urls_for_unauthorized:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_urls_available_for_authorized_user(self):
        """
        Проверка доступности адресов для
        авторизированного пользователя.
        """
        for address in self.urls:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_create_unauthorized_redirect(self):
        """
        Проверка редиректа для неавторизированного
        пользователя по адресу /create/.
        """
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_post_edit_not_author_redirect(self):
        """
        Проверка редиректа для пользователя,
        который не является автором изменяемого поста.
        """
        guest_response = self.guest_client.get(self.urls[5])
        self.assertRedirects(
            guest_response, ('/auth/login/?next=/posts/1/edit/'))
        nonauthor_response = self.notauthor_client.get(self.urls[5])
        self.assertRedirects(nonauthor_response, ('/posts/1/'))

    def test_404_on_nonexistent_page(self):
        """ Проверка, что несуществующий адрес выдает 404 ошибку. """
        response = self.guest_client.get('/no/')
        self.assertEqual(response.status_code, 404)

    def test_comment_create_redirects_if_not_logged_in(self):
        """
        Проверка, что незарегистрированный пользователь
        не может оставлять комментарии.
        """
        guest_response = self.guest_client.get('/posts/1/comment/')
        self.assertRedirects(
            guest_response, ('/auth/login/?next=/posts/1/comment/'))
