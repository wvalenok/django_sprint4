from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone
from .models import Post


def add_comment_count(queryset):
    return queryset.annotate(comment_count=Count('comments'))


def paginate_queryset(request, queryset, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def get_published_posts(queryset=None, user=None):

    if queryset is None:
        queryset = Post.objects.all()
    
    # Если пользователь указан и хочет видеть свои посты
    if user and user.is_authenticated:
        user_posts = queryset.filter(author=user)
        published_posts = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
        return (user_posts | published_posts).distinct()
    
    # Для неавторизованных или других пользователей
    return queryset.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )