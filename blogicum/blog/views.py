from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView

from .models import Post, Category, Comment
from .forms import CreationForm, PostForm, CommentForm

User = get_user_model()


# ---------- Функциональные представления ----------
def index(request):
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.author:
        post = get_object_or_404(
            Post.objects.filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            ),
            id=post_id
        )
    
    can_view = (
        post.is_published and 
        post.category.is_published and 
        post.pub_date <= timezone.now()
    ) or (request.user == post.author)
    
    if not can_view:
        return redirect('blog:index')
    
    comments = post.comments.all()
    form = CommentForm(request.POST or None) if request.user.is_authenticated else None
    
    if form and form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)
    
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


# ---------- Классовые представления ----------
class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/registration_form.html'


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        posts = user.posts.annotate(comment_count=Count('comments'))
        
        if self.request.user != user:
            posts = posts.filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )
        
        paginator = Paginator(posts.order_by('-pub_date'), 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['page_obj'] = page_obj
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'registration/profile_form.html'
    fields = ('first_name', 'last_name', 'username', 'email')
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    
    def get_object(self):
        post = super().get_object()
        if post.author != self.request.user:
            raise PermissionDenied
        return post
    
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    
    def get_object(self):
        post = super().get_object()
        if post.author != self.request.user:
            raise PermissionDenied
        return post
    
    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user.username})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    
    def get_object(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        if comment.author != self.request.user:
            raise PermissionDenied
        return comment
    
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.post.id})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    
    def get_object(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        if comment.author != self.request.user:
            raise PermissionDenied
        return comment
    
    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.post.id})