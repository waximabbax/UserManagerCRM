from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.blog_home, name='blog_home'),
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('posts/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('series/<slug:slug>/', views.series_detail, name='series_detail'),
    path('search/', views.search, name='search'),
    path('archive/', views.archive, name='archive'),
    path('archive/<int:year>/', views.archive, name='archive_year'),
    path('archive/<int:year>/<int:month>/', views.archive, name='archive_month'),
    path('add-comment/<slug:slug>/', views.add_comment, name='add_comment'),
    path('like-post/', views.like_post, name='like_post'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
]
