from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('', views.contact, name='contact'),
    path('success/', views.contact_success, name='success'),
    path('quick-contact/', views.quick_contact, name='quick_contact'),
    path('faq/', views.faq_list, name='faq'),
    
    # Admin URLs
    path('admin/messages/', views.admin_messages, name='admin_messages'),
    path('admin/messages/<int:message_id>/', views.admin_message_detail, name='admin_message_detail'),
]
