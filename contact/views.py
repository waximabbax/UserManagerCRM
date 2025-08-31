from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import ContactMessage, ContactInfo, FAQ, ContactReply
from .forms import ContactForm, QuickContactForm, ContactReplyForm


def contact(request):
    """Main contact page with form and information"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            
            # Capture IP address and user agent
            contact_message.ip_address = request.META.get('REMOTE_ADDR')
            contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            contact_message.save()
            
            # Send notification email to admin
            try:
                send_notification_email(contact_message)
            except Exception as e:
                print(f"Failed to send notification email: {e}")
            
            messages.success(
                request, 
                'Thank you for your message! We will get back to you within 24 hours.'
            )
            return redirect('contact:success')
    else:
        form = ContactForm()
    
    # Get contact information
    contact_info = ContactInfo.objects.filter(is_active=True).first()
    
    # Get FAQs
    faqs = FAQ.objects.filter(is_featured=True).order_by('order')[:10]
    
    context = {
        'form': form,
        'contact_info': contact_info,
        'faqs': faqs,
    }
    return render(request, 'contact/contact.html', context)


def contact_success(request):
    """Success page after form submission"""
    return render(request, 'contact/success.html')


def quick_contact(request):
    """AJAX endpoint for quick contact form"""
    if request.method == 'POST':
        form = QuickContactForm(request.POST)
        if form.is_valid():
            # Create ContactMessage from quick form
            contact_message = ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message'],
                subject='general',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send notification
            try:
                send_notification_email(contact_message)
            except Exception as e:
                print(f"Failed to send notification email: {e}")
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you! Your message has been sent successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def faq_list(request):
    """FAQ listing page"""
    category = request.GET.get('category', '')
    
    faqs = FAQ.objects.all()
    if category:
        faqs = faqs.filter(category=category)
    
    faqs = faqs.order_by('order', '-created_at')
    
    # Group FAQs by category
    faq_categories = {}
    for faq in faqs:
        if faq.category not in faq_categories:
            faq_categories[faq.category] = []
        faq_categories[faq.category].append(faq)
    
    context = {
        'faq_categories': faq_categories,
        'current_category': category,
        'categories': FAQ.CATEGORY_CHOICES,
    }
    return render(request, 'contact/faq.html', context)


@staff_member_required
def admin_messages(request):
    """Admin view to manage contact messages"""
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    messages_queryset = ContactMessage.objects.all()
    
    if status:
        messages_queryset = messages_queryset.filter(status=status)
    
    if search:
        messages_queryset = messages_queryset.filter(
            models.Q(name__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(message__icontains=search)
        )
    
    messages_queryset = messages_queryset.order_by('-created_at')
    
    paginator = Paginator(messages_queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    stats = {
        'total': ContactMessage.objects.count(),
        'new': ContactMessage.objects.filter(status='new').count(),
        'read': ContactMessage.objects.filter(status='read').count(),
        'replied': ContactMessage.objects.filter(status='replied').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'current_status': status,
        'search_query': search,
        'stats': stats,
        'status_choices': ContactMessage.STATUS_CHOICES,
    }
    return render(request, 'contact/admin_messages.html', context)


@staff_member_required
def admin_message_detail(request, message_id):
    """Admin view for individual message details and reply"""
    contact_message = get_object_or_404(ContactMessage, id=message_id)
    contact_message.mark_as_read()
    
    if request.method == 'POST':
        form = ContactReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.contact_message = contact_message
            reply.admin_user = request.user
            reply.save()
            
            # Send reply email
            try:
                send_reply_email(reply)
                reply.is_sent = True
                reply.sent_at = timezone.now()
                reply.save()
                
                contact_message.mark_as_replied()
                
                messages.success(request, 'Reply sent successfully!')
            except Exception as e:
                messages.error(request, f'Failed to send reply: {e}')
            
            return redirect('contact:admin_message_detail', message_id=message_id)
    else:
        # Pre-populate reply subject
        reply_subject = f"Re: {contact_message.display_subject}"
        form = ContactReplyForm(initial={'subject': reply_subject})
    
    context = {
        'contact_message': contact_message,
        'replies': contact_message.replies.all(),
        'form': form,
    }
    return render(request, 'contact/admin_message_detail.html', context)


def send_notification_email(contact_message):
    """Send notification email to admin when new message is received"""
    subject = f"New Contact Message: {contact_message.display_subject}"
    message = f"""
    New contact message received:
    
    Name: {contact_message.name}
    Email: {contact_message.email}
    Subject: {contact_message.display_subject}
    
    Message:
    {contact_message.message}
    
    ---
    View and reply: http://your-domain.com/admin/contact/messages/{contact_message.id}/
    """
    
    admin_email = getattr(settings, 'CONTACT_EMAIL', settings.DEFAULT_FROM_EMAIL)
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin_email],
        fail_silently=False,
    )


def send_reply_email(reply):
    """Send reply email to the contact message sender"""
    contact_message = reply.contact_message
    
    send_mail(
        subject=reply.subject,
        message=reply.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[contact_message.email],
        fail_silently=False,
    )
