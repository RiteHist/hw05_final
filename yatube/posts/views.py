from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import Follow, Post, Group
from .forms import PostForm, CommentForm
from .utils import objects_to_paginator


User = get_user_model()


def index(request):
    """ Главная страница. """
    posts = (Post.objects
             .select_related('author', 'group'))
    page_obj = objects_to_paginator(request, posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """ Все посты группы. """
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = objects_to_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """ Профиль пользователя. """
    user = get_object_or_404(User, username=username)
    """ Проверка, что пользователь подписан на автора"""
    following = False
    if request.user.is_authenticated:
        current_user = get_object_or_404(User, username=request.user.username)
        following = current_user.follower.filter(author__exact=user).exists()

    posts = user.posts.all()
    page_obj = objects_to_paginator(request, posts)

    context = {
        'page_obj': page_obj,
        'author': user,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """ Подробная информация о посте. """
    post = get_object_or_404(Post, pk=post_id)
    user = get_object_or_404(User, username=post.author)
    form = CommentForm()
    comments = post.comments.all()
    num_posts = user.posts.count()
    post_name = post.text[0:30]
    context = {
        'post': post,
        'post_name': post_name,
        'num_posts': num_posts,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """ Создание поста. """
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        user = request.user
        post_object = form.save(commit=False)
        post_object.author = user
        post_object.save()
        return redirect('posts:profile', user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """ Редактирование поста. """
    post = get_object_or_404(Post, pk=post_id)
    if not post.author == request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'is_edit': True,
        'form': form,
        'post': post
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """ Добавление комментария к посту. """
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """ Все посты авторов, на которых подписан пользователь. """
    follower = get_object_or_404(User, username=request.user.username)
    follows = follower.follower.all().values('author')
    posts = Post.objects.filter(author__in=follows)
    page_obj = objects_to_paginator(request, posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """ Подписка на автора. """
    follower = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    if follower == author:
        return redirect('posts:profile', username)
    follow_exists = follower.follower.filter(author__exact=author).exists()
    if follow_exists:
        return redirect('posts:profile', username)
    new_following = Follow(user=follower, author=author)
    new_following.save()
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """ Отписка от автора. """
    follower = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    follow_link = get_object_or_404(Follow,
                                    author=author,
                                    user=follower)
    follow_link.delete()
    return redirect('posts:profile', username)
