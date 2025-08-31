from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Project, Category, Skill, Experience, Education, Achievement, Testimonial

User = get_user_model()


def home(request):
    """Homepage view"""
    # Get featured projects
    featured_projects = Project.objects.filter(
        is_featured=True, 
        is_published=True
    ).order_by('-created_at')[:6]
    
    # Get recent projects
    recent_projects = Project.objects.filter(
        is_published=True
    ).order_by('-created_at')[:8]
    
    # Get categories with project counts
    categories = Category.objects.annotate(
        project_count=Count('project')
    ).filter(project_count__gt=0)[:6]
    
    # Get featured users/developers
    featured_users = User.objects.filter(
        is_active=True,
        projects__isnull=False
    ).distinct().order_by('-date_joined')[:6]
    
    # Get testimonials
    testimonials = Testimonial.objects.filter(
        is_featured=True
    ).order_by('-created_at')[:5]
    
    context = {
        'featured_projects': featured_projects,
        'recent_projects': recent_projects,
        'categories': categories,
        'featured_users': featured_users,
        'testimonials': testimonials,
    }
    return render(request, 'portfolio/home.html', context)


class ProjectListView(ListView):
    """List view for projects with filtering and search"""
    model = Project
    template_name = 'portfolio/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Project.objects.filter(is_published=True)
        
        # Search functionality
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(technologies__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        # Category filtering
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # User filtering
        username = self.request.GET.get('user')
        if username:
            queryset = queryset.filter(user__username=username)
        
        # Status filtering
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['created_at', '-created_at', 'title', '-title', 'views', '-views']:
            queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['current_query'] = self.request.GET.get('q', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        return context


class ProjectDetailView(DetailView):
    """Detail view for individual projects"""
    model = Project
    template_name = 'portfolio/project_detail.html'
    context_object_name = 'project'
    
    def get_object(self):
        obj = super().get_object()
        # Increment view count
        obj.views += 1
        obj.save(update_fields=['views'])
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Get related projects
        context['related_projects'] = Project.objects.filter(
            category=project.category,
            is_published=True
        ).exclude(pk=project.pk)[:4]
        
        # Get project testimonials
        context['testimonials'] = project.testimonials.all()
        
        # Check if user has liked this project
        if self.request.user.is_authenticated:
            context['user_has_liked'] = project.likes.filter(
                pk=self.request.user.pk
            ).exists()
        
        return context


def category_detail(request, slug):
    """Category detail view showing projects in that category"""
    category = get_object_or_404(Category, slug=slug)
    projects = Project.objects.filter(
        category=category,
        is_published=True
    ).order_by('-created_at')
    
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'projects': page_obj,
    }
    return render(request, 'portfolio/category_detail.html', context)


def user_portfolio(request, username):
    """Individual user portfolio view"""
    user = get_object_or_404(User, username=username)
    
    # Get user's projects
    projects = Project.objects.filter(
        user=user,
        is_published=True
    ).order_by('-created_at')
    
    # Get user's skills
    skills = Skill.objects.filter(user=user).order_by('-percentage')
    
    # Get user's experience
    experience = Experience.objects.filter(user=user)
    
    # Get user's education
    education = Education.objects.filter(user=user)
    
    # Get user's achievements
    achievements = Achievement.objects.filter(user=user)[:5]
    
    # Get user's testimonials
    testimonials = Testimonial.objects.filter(user=user)[:5]
    
    # Paginate projects
    paginator = Paginator(projects, 9)
    page_number = request.GET.get('page')
    projects_page = paginator.get_page(page_number)
    
    context = {
        'portfolio_user': user,
        'projects': projects_page,
        'skills': skills,
        'experience': experience,
        'education': education,
        'achievements': achievements,
        'testimonials': testimonials,
    }
    return render(request, 'portfolio/user_portfolio.html', context)


def about(request):
    """About page"""
    # Get some statistics
    stats = {
        'total_projects': Project.objects.filter(is_published=True).count(),
        'total_users': User.objects.filter(is_active=True).count(),
        'total_categories': Category.objects.count(),
        'completed_projects': Project.objects.filter(
            status='completed',
            is_published=True
        ).count(),
    }
    
    # Get featured developers
    featured_developers = User.objects.filter(
        is_active=True,
        projects__isnull=False
    ).annotate(
        project_count=Count('projects')
    ).order_by('-project_count')[:8]
    
    context = {
        'stats': stats,
        'featured_developers': featured_developers,
    }
    return render(request, 'portfolio/about.html', context)


@login_required
def like_project(request):
    """AJAX view to like/unlike projects"""
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        
        if project.likes.filter(pk=request.user.pk).exists():
            project.likes.remove(request.user)
            liked = False
        else:
            project.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'like_count': project.like_count
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def search(request):
    """Advanced search functionality"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    user_filter = request.GET.get('user', '')
    
    projects = Project.objects.filter(is_published=True)
    
    if query:
        projects = projects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(technologies__icontains=query) |
            Q(short_description__icontains=query)
        )
    
    if category:
        projects = projects.filter(category__slug=category)
    
    if user_filter:
        projects = projects.filter(user__username=user_filter)
    
    projects = projects.order_by('-created_at')
    
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'categories': Category.objects.all(),
        'current_category': category,
        'current_user': user_filter,
        'total_results': projects.count(),
    }
    return render(request, 'portfolio/search_results.html', context)
