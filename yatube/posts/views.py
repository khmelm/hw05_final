from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Comment, Group, Follow, Post, User

NUM_OF_POSTS: int = 10


def paginator(posts, page, num_of_posts=NUM_OF_POSTS):
    paginator = Paginator(posts, num_of_posts)
    page_obj = paginator.get_page(page)
    return page_obj


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = paginator(post_list, request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    page_obj = paginator(posts, request.GET.get('page'))
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    posts_count = posts.count()
    page_obj = paginator(posts, request.GET.get('page'))
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=user).exists()
    )
    context = {
        'author': user,
        'page_obj': page_obj,
        'posts_count': posts_count,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    author_post = post.author.posts.count()
    context = {
        'post': post,
        'author_post': author_post,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if request.method == 'POST':
        if not form.is_valid():
            return render(request, template, {'form': form})
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
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
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(posts, request.GET.get('page'))
    context = {
        'page_obj': page_obj,
        'following': True
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
