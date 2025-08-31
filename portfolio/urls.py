from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.home, name='home'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/<slug:slug>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('user/<str:username>/', views.user_portfolio, name='user_portfolio'),
    path('about/', views.about, name='about'),
    path('search/', views.search, name='search'),
    path('like-project/', views.like_project, name='like_project'),
]
