from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Profile, Post, Comment, Like, Follow


def home(request):
    posts = Post.objects.select_related('user').prefetch_related(
        'comments', 'likes'
    ).order_by('-created_at')

    return render(request, 'social/home.html', {
        'posts': posts
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('register')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Profile.objects.create(user=user)

        messages.success(request, 'Account created successfully. Please login.')
        return redirect('login')

    return render(request, 'social/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            Profile.objects.get_or_create(user=user)
            return redirect('home')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'social/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.POST.get('image', '').strip()

        if content:
            Post.objects.create(
                user=request.user,
                content=content,
                image=image
            )
            messages.success(request, 'Post created successfully.')
        else:
            messages.error(request, 'Post cannot be empty.')

    return redirect('home')


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.user == request.user:
        post.delete()
        messages.success(request, 'Post deleted successfully.')

    return redirect('home')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()

        if content:
            Comment.objects.create(
                user=request.user,
                post=post,
                content=content
            )

    return redirect('home')


@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like = Like.objects.filter(
        user=request.user,
        post=post
    ).first()

    if like:
        like.delete()
    else:
        Like.objects.create(
            user=request.user,
            post=post
        )

    return redirect('home')


@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)

    user_profile, created = Profile.objects.get_or_create(user=user)

    posts = Post.objects.filter(
        user=user
    ).order_by('-created_at')

    followers_count = Follow.objects.filter(
        following=user
    ).count()

    following_count = Follow.objects.filter(
        follower=user
    ).count()

    is_following = False

    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()

    return render(request, 'social/profile.html', {
        'profile_user': user,
        'user_profile': user_profile,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
    })


@login_required
def edit_profile(request):
    user_profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        bio = request.POST.get('bio', '').strip()
        profile_image = request.POST.get('profile_image', '').strip()

        user_profile.bio = bio
        user_profile.profile_image = profile_image
        user_profile.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('profile', username=request.user.username)

    return render(request, 'social/edit_profile.html', {
        'user_profile': user_profile
    })


@login_required
def toggle_follow(request, username):
    target_user = get_object_or_404(User, username=username)

    if target_user == request.user:
        messages.error(request, 'You cannot follow yourself.')
        return redirect('profile', username=username)

    follow = Follow.objects.filter(
        follower=request.user,
        following=target_user
    ).first()

    if follow:
        follow.delete()
    else:
        Follow.objects.create(
            follower=request.user,
            following=target_user
        )

    return redirect('profile', username=username)