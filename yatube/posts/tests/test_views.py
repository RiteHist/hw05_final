import tempfile
import shutil
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from ..models import Post, Group, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testboy')
        cls.second_user = User.objects.create_user(username='testierboy')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.form = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField
        }
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
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
            image=image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.client.force_login(PostsViewTests.user)

    def test_pages_use_correct_templates(self):
        """ Проверка, что страницы используют правильные шаблоны"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': PostsViewTests.group.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': PostsViewTests.user.username}):
                        'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': PostsViewTests.post.id}):
                        'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsViewTests.post.id}):
                        'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for address, template in templates_pages_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_have_correct_paginator(self):
        """ Проверка, что на страницах правильно работает паджинатор. """
        posts = (Post(text=f'Тестовый пост {i}',
                      group=PostsViewTests.group,
                      author=PostsViewTests.user) for i in range(12))
        Post.objects.bulk_create(posts)
        address_names = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': PostsViewTests.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostsViewTests.user.username})
        ]
        for address in address_names:
            with self.subTest(address=address):
                posts_max = 10
                posts_second_page = 3
                response = self.client.get(address)
                self.assertEqual(len(response.context['page_obj']), posts_max)
                response = self.client.get(address + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 posts_second_page)

    def test_index_has_correct_context(self):
        """ Проверка контекста у index'a. """
        response = self.client.get(reverse('posts:index'))
        self.assertTrue(response.context.get('page_obj'))
        post = response.context.get('page_obj').object_list[0]
        self.assertEqual(post.id, PostsViewTests.post.id)
        self.assertEqual(post.image, PostsViewTests.post.image)

    def test_group_list_has_correct_context(self):
        """ Проверка контекста у страницы постов группы. """
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostsViewTests.group.slug}))
        self.assertTrue(response.context.get('group'))
        self.assertTrue(response.context.get('page_obj'))
        post = response.context.get('page_obj').object_list[0]
        self.assertEqual(post.image, PostsViewTests.post.image)

    def test_profile_has_correct_context(self):
        """ Проверка контекста у страницы постов автора. """
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': PostsViewTests.user.username}))
        self.assertTrue(response.context.get('page_obj'))
        self.assertTrue(response.context.get('author'))
        post = response.context.get('page_obj').object_list[0]
        self.assertEqual(post.image, PostsViewTests.post.image)

    def test_post_detail_has_correct_context(self):
        """ Проверка контекста у страницы информации о посте. """
        response = self.client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostsViewTests.post.id}))
        self.assertTrue(response.context.get('post'))
        self.assertTrue(response.context.get('post_name'))
        self.assertTrue(response.context.get('num_posts'))
        post = response.context.get('post')
        self.assertEqual(post.id, PostsViewTests.post.id)
        self.assertEqual(post.image, PostsViewTests.post.image)

    def test_create_and_edit_post_have_correct_form(self):
        """
        Проверка, что страницы создания и редактирования поста
        используют корректную форму.
        """
        path_names = [
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsViewTests.post.id})
        ]
        for path in path_names:
            response = self.client.get(path)
            for field, expected in PostsViewTests.form.items():
                with self.subTest(field=field):
                    response_field = (response.context.
                                      get('form').fields.get(field))
                    self.assertIsInstance(response_field, expected)

    def test_edit_post_has_correct_context(self):
        """ Проверка контекста страницы редактирования поста. """
        response = self.client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsViewTests.post.id}))
        self.assertTrue(response.context.get('is_edit'))
        self.assertTrue(response.context.get('form'))
        self.assertTrue(response.context.get('post'))

    def test_post_existence(self):
        """ Проверка правильности создания поста. """
        Post.objects.create(
            author=PostsViewTests.user,
            group=PostsViewTests.group,
            text='Тест создания поста'
        )
        paths = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': PostsViewTests.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostsViewTests.user.username})
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                post = response.context.get('page_obj').object_list[0]
                self.assertEqual(post.text, 'Тест создания поста')

        """
        Создание дополнительных объектов для теста того,
        что созданный пост не отображается в других группах.
        """
        second_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        Post.objects.create(
            author=PostsViewTests.user,
            group=second_group,
            text='Тестовый пост другой группы'
        )
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': second_group.slug}))

        post = response.context.get('page_obj').object_list[0]
        self.assertNotEqual(post.text, 'Тест создания поста')

    def test_index_is_cached(self):
        """ Проверка, что индекс кэшируется. """
        key = make_template_fragment_key('index_page')
        first_cache_post = Post.objects.create(
            author=PostsViewTests.user,
            group=PostsViewTests.group,
            text='Тест кэша 1'
        )
        first_response = self.client.get(reverse('posts:index'))
        post_exists = first_response.content
        first_cache_post.delete()
        second_response = self.client.get(reverse('posts:index'))
        post_in_cache = second_response.content
        self.assertEqual(post_exists, post_in_cache)
        cache.delete(key)
        final_response = self.client.get(reverse('posts:index'))
        posts_in_final = final_response.content
        self.assertNotEqual(post_exists, posts_in_final)

    def test_logged_user_can_follow_author(self):
        """ Проверка, что пользователь может подписываться на автора. """
        username_param = {'username': PostsViewTests.second_user.username}
        response = self.client.get(reverse('posts:profile_follow',
                                           kwargs=username_param))

        self.assertRedirects(response,
                             reverse('posts:profile', kwargs=username_param))

        follow_pair = PostsViewTests.user.follower.get(
            author=PostsViewTests.second_user)
        self.assertTrue(follow_pair)

    def test_logged_user_can_unfollow(self):
        """ Проверка, что пользователь может отписаться от автора. """
        username_param = {'username': PostsViewTests.second_user.username}
        response = self.client.get(reverse('posts:profile_unfollow',
                                           kwargs=username_param))

        self.assertEqual(response.status_code, 404)

        follow_pair = Follow.objects.filter(
            author=PostsViewTests.second_user,
            user=PostsViewTests.user
        )
        self.assertFalse(follow_pair)

    def test_post_is_visible_to_following_user(self):
        """
        Проверка, что новый пост виден только
        для подписанного на автора пользователя.
        """
        username_param = {'username': PostsViewTests.second_user.username}
        self.client.get(reverse('posts:profile_follow',
                                kwargs=username_param))
        new_post = Post.objects.create(
            author=PostsViewTests.second_user,
            text='Тест подписки'
        )
        response = self.client.get(reverse('posts:follow_index'))
        post_in_follow = response.context.get('page_obj').object_list[0]
        self.assertEqual(new_post, post_in_follow)
        third_user = User.objects.create_user(username='thetestiestboy')
        new_client = Client()
        new_client.force_login(third_user)
        new_client_response = new_client.get(reverse('posts:follow_index'))
        posts = new_client_response.context.get('page_obj').object_list
        self.assertFalse(posts)
