from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User, Profile
from .forms import UserRegistrationForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm


class RegisterView(CreateView):
    """User registration view"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful! You can now log in.')
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('portfolio:home')
        return super().dispatch(request, *args, **kwargs)


def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('portfolio:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    next_page = request.GET.get('next', 'portfolio:home')
                    return redirect(next_page)
            except User.DoesNotExist:
                pass
            
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('portfolio:home')


@login_required
def profile_view(request, username=None):
    """View user profile"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    profile, created = Profile.objects.get_or_create(user=user)
    
    context = {
        'profile_user': user,
        'profile': profile,
        'is_own_profile': request.user == user,
    }
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'users/edit_profile.html', context)


@login_required
def dashboard(request):
    """User dashboard"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Get user's recent activity (you can customize this)
    recent_projects = request.user.project_set.all()[:5] if hasattr(request.user, 'project_set') else []
    recent_posts = request.user.post_set.all()[:5] if hasattr(request.user, 'post_set') else []
    
    context = {
        'profile': profile,
        'recent_projects': recent_projects,
        'recent_posts': recent_posts,
    }
    return render(request, 'users/dashboard.html', context)


def user_list(request):
    """List all users with search functionality"""
    query = request.GET.get('q', '')
    users = User.objects.filter(is_active=True).order_by('-created_at')
    
    if query:
        users = users.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(bio__icontains=query)
        )
    
    paginator = Paginator(users, 12)  # Show 12 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'users/user_list.html', context)
