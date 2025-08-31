from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Post, BlogCategory, Comment, Newsletter, BlogSeries
from .forms import CommentForm, NewsletterForm


class PostListView(ListView):
    """List view for blog posts"""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Post.objects.filter(status='published')
        
        # Search functionality
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        # Category filtering
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Author filtering
        author = self.request.GET.get('author')
        if author:
            queryset = queryset.filter(author__username=author)
        
        # Tag filtering
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        # Sorting
        sort = self.request.GET.get('sort', '-published_at')
        if sort in ['-published_at', 'published_at', '-views', 'views', 'title', '-title']:
            queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogCategory.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['current_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '-published_at')
        
        # Featured posts
        context['featured_posts'] = Post.objects.filter(
            status='published',
            is_featured=True
        ).order_by('-published_at')[:3]
        
        return context


class PostDetailView(DetailView):
    """Detail view for individual blog posts"""
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Post.objects.filter(status='published')
    
    def get_object(self):
        obj = super().get_object()
        # Increment view count
        obj.views += 1
        obj.save(update_fields=['views'])
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Get comments
        comments = Comment.objects.filter(
            post=post,
            is_approved=True,
            parent=None
        ).order_by('created_at')
        
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        
        # Get related posts
        related_posts = Post.objects.filter(
            status='published'
        ).exclude(pk=post.pk)
        
        if post.category:
            related_posts = related_posts.filter(category=post.category)
        
        context['related_posts'] = related_posts[:4]
        
        # Check if user has liked this post
        if self.request.user.is_authenticated:
            context['user_has_liked'] = post.likes.filter(
                pk=self.request.user.pk
            ).exists()
        
        # Series information
        if post.series:
            context['series_posts'] = post.series.posts.filter(
                status='published'
            ).order_by('series_order')
        
        return context


def blog_home(request):
    """Blog homepage"""
    # Featured posts
    featured_posts = Post.objects.filter(
        status='published',
        is_featured=True
    ).order_by('-published_at')[:3]
    
    # Recent posts
    recent_posts = Post.objects.filter(
        status='published'
    ).order_by('-published_at')[:6]
    
    # Popular posts (by views)
    popular_posts = Post.objects.filter(
        status='published'
    ).order_by('-views')[:5]
    
    # Categories with post counts
    categories = BlogCategory.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0)[:8]
    
    # Blog series
    blog_series = BlogSeries.objects.filter(
        posts__status='published'
    ).distinct().order_by('-created_at')[:4]
    
    context = {
        'featured_posts': featured_posts,
        'recent_posts': recent_posts,
        'popular_posts': popular_posts,
        'categories': categories,
        'blog_series': blog_series,
        'newsletter_form': NewsletterForm(),
    }
    return render(request, 'blog/blog_home.html', context)


def category_detail(request, slug):
    """Category detail view"""
    category = get_object_or_404(BlogCategory, slug=slug)
    posts = Post.objects.filter(
        category=category,
        status='published'
    ).order_by('-published_at')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'posts': page_obj,
    }
    return render(request, 'blog/category_detail.html', context)


def series_detail(request, slug):
    """Blog series detail view"""
    series = get_object_or_404(BlogSeries, slug=slug)
    posts = series.posts.filter(
        status='published'
    ).order_by('series_order')
    
    context = {
        'series': series,
        'posts': posts,
    }
    return render(request, 'blog/series_detail.html', context)


@login_required
def add_comment(request, slug):
    """Add comment to blog post"""
    post = get_object_or_404(Post, slug=slug, status='published')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            
            # Handle reply to another comment
            parent_id = request.POST.get('parent_id')
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent = parent_comment
            
            comment.save()
            messages.success(request, 'Your comment has been added successfully!')
        else:
            messages.error(request, 'Please correct the errors in your comment.')
    
    return redirect('blog:post_detail', slug=slug)


@login_required
def like_post(request):
    """AJAX view to like/unlike blog posts"""
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        
        if post.likes.filter(pk=request.user.pk).exists():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'like_count': post.like_count
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def subscribe_newsletter(request):
    """Newsletter subscription"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data.get('name', '')
            
            newsletter, created = Newsletter.objects.get_or_create(
                email=email,
                defaults={'name': name}
            )
            
            if created:
                messages.success(request, 'Thank you for subscribing to our newsletter!')
            else:
                messages.info(request, 'You are already subscribed to our newsletter.')
        else:
            messages.error(request, 'Please provide a valid email address.')
    
    return redirect('blog:blog_home')


def search(request):
    """Blog search functionality"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    posts = Post.objects.filter(status='published')
    
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query)
        )
    
    if category:
        posts = posts.filter(category__slug=category)
    
    posts = posts.order_by('-published_at')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'categories': BlogCategory.objects.all(),
        'current_category': category,
        'total_results': posts.count(),
    }
    return render(request, 'blog/search_results.html', context)


def archive(request, year=None, month=None):
    """Blog archive by date"""
    posts = Post.objects.filter(status='published')
    
    if year:
        posts = posts.filter(published_at__year=year)
        if month:
            posts = posts.filter(published_at__month=month)
    
    posts = posts.order_by('-published_at')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'year': year,
        'month': month,
    }
    return render(request, 'blog/archive.html', context)
