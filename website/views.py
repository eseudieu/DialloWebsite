from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.http.response import JsonResponse
from website.forms import RequestServiceForm, ServiceReviewForm, AdminTaskUpdateForm, ClientTaskUpdateForm, StatusUpdateForm
from website.models import Task
from DialloWebsite.settings import ADMIN_LIST, STRIPE_PUBLIC, STRIPE_PRIVATE, SERVER_EMAIL, SERVER_PASS
import stripe, smtplib
from email.message import EmailMessage

# Decorator to provide authentication checks
def auth_factory(auth_type=None):
     def auth_wrapper(action_function):
         def my_wrapper_function(request, *args, **kwargs):
             if not request.user.is_authenticated:
                 messages.error(request, 'You must be logged in to perform this action')
                 return redirect('home')
             if auth_type=='client' and request.user.is_admin():
                 messages.error(request, 'You must be a client to perform this action')
                 return redirect('home')
             if auth_type=='admin' and not request.user.is_admin():
                 messages.error(request, 'You must be an administrator to perform this action')
                 return redirect('home')
             return action_function(request, *args, **kwargs)
         return my_wrapper_function
     return auth_wrapper

# Email sending
def send_email(recipient='', subject='', content=''):
    msg = EmailMessage()
    msg.set_content(content)
    msg['From'], msg['To'], msg['Subject'] = SERVER_EMAIL, recipient, subject

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:  # Use SMTP_SSL for secure connection
            smtp.login(SERVER_EMAIL, SERVER_PASS)
            smtp.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# Neutral Views

''' FINISHED '''
def login_action(request):
    return redirect('/oauth/login/google-oauth2/')

@auth_factory()
def oauth_landing(request):
    user = request.user
    user.admin_status = user.email in ADMIN_LIST 
    user.save()

    return redirect('home')

''' FINISHED '''
@auth_factory()
def logout_action(request):
    logout(request)
    return redirect('projects')

''' FINISHED '''
def home_action(request):
    if request.user.is_authenticated and request.user.is_admin():
        return redirect('service-history')
    return redirect('projects')

# Just graphics
def projects_action(request):
    return render(request, 'website/projects.html', {})

# Just graphics
def about_action(request):
    return render(request, 'website/about.html', {})

# Client Views

''' FINISHED '''
@auth_factory('client')
def request_service_action(request):
    if request.method == 'POST': # someone has sent in a service request, either display error messages or success screen 
        with transaction.atomic():
            new_task = Task()
            new_task.user = request.user
            new_task.email = request.user.email
            service_form = RequestServiceForm(request.POST, instance=new_task)

            if not service_form.is_valid():
                messages.error(request, 'Invalid input')
                # Display errors in appropriate places
                return render(request, 'website/request_service.html', {'form': service_form})

            new_task.submission_date = new_task.client_update_date = new_task.admin_update_date = timezone.now()
            new_task.save()

            messages.success(request, "Successfully placed service query.")
            server_subject = f"New Request Submitted: {new_task.get_service_type_display()}"
            server_content = f'A request has been submitted for {new_task.get_service_type_display()}'

            # ?CHANGE EMAIL FOR PRODUCTION
            send_email(recipient='selvinjr04@gmail.com', subject=server_subject, content=server_content)

            client_subject = f"New Request Submitted: {new_task.get_service_type_display()}"
            # ?CHANGE NUMBER FOR PRODUCTION, DATE FORMATTING
            client_content = (f'We have successfully received your request for (request type) and will get back to you shortly. If you do not receive a phone call or email to the registered points of contact (Phone: {new_task.phone_number}; Email: {new_task.email}) within 48 hours, feel free to call us at {5+5}. Below is a copy of your request as a receipt:\n\n'
            f'Task type: {new_task.get_service_type_display()}\n'
            f'Submission date: {new_task.submission_date}\n'
            f'Task description: {new_task.description}\n'
            f'Associated email: {new_task.email}\nAssociated phone: {new_task.phone_number}')
            
            send_email(recipient=new_task.email, subject=client_subject, content=client_content)
            return redirect(reverse('view-request', args=[new_task.id]))
    
    service_form = RequestServiceForm()
    context = {}
    context['form'] = service_form
    return render(request, 'website/request_service.html', context)
 
@auth_factory()
def view_request_action(request, id):
    task = get_object_or_404(Task, id=id)

    if request.user != task.user and not request.user.is_admin():
        messages.error(request, "You do not have permission to view this request")
        return redirect('home')

    if request.method == 'POST': # someone is updating details concerning the request
        task = Task.objects.select_for_update().get(id=id)
        # admin updated the status of the request
        if 'update_status' in request.POST and request.user.is_admin():
            status_form = StatusUpdateForm(request.POST, request.FILES, instance=task)
            # ? SEND ONE EMAIL FOR ALL CHANGES IN PRODUCTION
            if status_form.is_valid():
                if 'status' in status_form.changed_data:
                    messages.success(request, f"Successfully updated status to {status_form.cleaned_data['status']}")
                    if task.status == 'COMPLETED':
                        task.completed_date = timezone.now()
                    elif task.status == 'CANCELLED':
                        task.cancelled_date = timezone.now()
                    elif task.status == 'CONFIRMED':
                        task.confirmed_date = timezone.now()
                    subject = f"New status for {task.get_service_type_display()}"
                    content = (f'The status of your request ({task.get_service_type_display()}) has been updated to ({task.status}).\n\n'
                                f'View the request here.\n\n' # ? HYPERLINK THIS IN PRODUCTION
                                f'If you have any questions, please call us at (Adama’s number).')
                    send_email(recipient=task.email, subject=subject, content=content)
                if 'paid' in status_form.changed_data and task.paid == True:
                    task.payment_date = timezone.now()
                    subject = f"Payment recieved for {task.get_service_type_display()}"
                    # ? UPDATE WITH ADAMA'S NUMBER FOR PRODUCTION
                    content = f'We have received your payment. Pleasure doing business with you. If you would like to leave a review, visit your request here. If you have any questions, please call us at (Adama’s number).'
                    send_email(recipient=task.email, subject=subject, content=content)
                task.save()
            else: 
                messages.error(request, 'Invalid input')
            return redirect(reverse('view-request', args=[id]))
        if 'update_review' in request.POST and not request.user.is_admin():
            if not task.review_rating:
                new_review = True
            review_form = ServiceReviewForm(request.POST, request.FILES, instance=task)
            if review_form.is_valid():
                task.review_date = timezone.now()
                task.save()
                messages.success(request, 'Successfully submitted review')
            else:
                messages.error(request, 'Invalid input')
            if new_review:
                subject = f"New Review for {task.get_service_type_display()}"
                content = f'We have received your review'
                send_email(recipient=task.email, subject=subject, content=content)
            return redirect(reverse('view-request', args=[id]))
        if 'update_info' in request.POST:
            # ? SEND ONE EMAIL FOR ALL CHANGES IN PRODUCTION
            if request.user.is_admin():
                # admin updated details of the request
                info_form = AdminTaskUpdateForm(request.POST, request.FILES, instance=task)
                if info_form.is_valid():
                    task.admin_update_date = timezone.now()
                    task.save()
                    messages.success(request, 'Successfully updated task information')
                else:
                    messages.error(request, 'Invalid input')
                if 'price' in info_form.changed_data:
                    subject = f"Payment requested for {task.get_service_type_display()}"
                    # ? HYPERLINK THIS FOR PRODUCTION
                    content = f'A payment amount of {task.price} has been specified for your request. Visit your request and pay ASAP. If you have any questions, please call us at (Adama’s number).'
                    send_email(recipient=task.email, subject=subject, content=content)
                if 'scheduled_date' in info_form.changed_data:
                    subject = f"Date scheduled for {task.get_service_type_display()}"
                    # ? HYPERLINK THIS FOR PRODUCTION, CHANGE DATE
                    content = f'Your request has been scheduled for {task.scheduled_date} If you have any questions, please call us at (Adama’s number).'
                    send_email(recipient=task.email, subject=subject, content=content)
                return redirect(reverse('view-request', args=[id]))
            else:
                # client updated details of the request
                info_form = ClientTaskUpdateForm(request.POST, request.FILES, instance=task)
                if info_form.is_valid():
                    task.client_update_date = timezone.now()
                    task.save()
                    messages.success(request, 'Successfully updated task information')
                else:
                    messages.error(request, 'Invalid input')
                return redirect(reverse('view-request', args=[id]))
            
        # neither update_status nor update_info were in the request
        messages.error(request, "Invalid request")
        return redirect(reverse('view-request', args=[id]))
    
    # it's a GET request, return different views depending on admin
    if request.user.is_admin():
        # proper forms
        info_form = AdminTaskUpdateForm(initial={'price': task.price, 'scheduled_date': task.scheduled_date, 'notes': task.notes})
        status_form = StatusUpdateForm(initial={'status': task.status, 'paid': task.paid})
        return render(request, 'website/view_request_admin.html', {'task': task, 'info_form': info_form, 'status_form': status_form})
    else:
        # proper forms
        info_form = ClientTaskUpdateForm(initial={'email':task.email, 'phone_number':task.phone_number})
        review_form = ServiceReviewForm(initial={'review_text': task.review_text, 'review_rating': task.review_rating})
        return render(request, 'website/view_request_client.html', {'task': task, 'info_form': info_form, 'review_form': review_form})

@auth_factory()
def service_history_action(request):
    if request.method == 'POST':
        messages.error(request, "Invalid request")
        redirect('home')
    
    if request.user.is_admin():
        tasks = Task.objects.all().order_by('-submission_date')
    else:
        tasks = request.user.service_requests.all().order_by('-submission_date')
    return render(request, 'website/service_history.html', {'tasks': tasks})

# Stripe calls
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': STRIPE_PUBLIC}
        return JsonResponse(stripe_config, safe=False)
    
@csrf_exempt
@auth_factory()
def create_checkout_session(request, id):
    task = get_object_or_404(Task, id=id)
    if not task.price:
        messages.error('Price has not been set yet for this task')
        return redirect(reverse('view-request', args=[id]))
    
    if task.user != request.user:
        messages.error(request, "You do not have permission to view this page")
        return redirect('home')
    
    if request.method == 'GET':
        stripe.api_key = STRIPE_PRIVATE
        # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        try:
            price = stripe.Price.create(
                currency="usd",
                product_data={"name": f"HVAC & More: {task.get_service_type_display()}"},
                unit_amount_decimal=task.price * 100,
            )

            price_id = price['id']
            checkout_session = stripe.checkout.Session.create(
                success_url=request.build_absolute_uri(reverse('success', args=[id])),
                cancel_url=request.build_absolute_uri(reverse('cancelled', args=[id, price_id])),
                mode='payment',
                line_items=[
                    {
                        'price': price,
                        'quantity': 1,
                    }
                ]
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            messages.error(request, 'Unexpected error while opening payment service. Try again')
            return redirect('home')
        
    messages.error(request, 'Invalid request')
    return redirect('home')

@auth_factory()
def success_action(request, id):
    if request.method == 'POST':
        messages.error(request, 'Invalid request')
        return redirect('home')
    
    task = get_object_or_404(Task, id=id)
    if task.user != request.user:
        messages.error(request, "You do not have permission to view this page")
        return redirect('home')
    
    messages.success(request, 'Payment successful.')

    return redirect(reverse('view-request', args=[id]))

@auth_factory()
def cancelled_action(request, id, price_id):
    if request.method == 'POST':
        messages.error(request, 'Invalid request')
        return redirect('home')
    
    task = get_object_or_404(Task, id=id)
    if task.user != request.user:
        messages.error(request, "You do not have permission to view this page")
        return redirect('home')
    
    messages.error(request, 'Payment cancelled.')
    return redirect(reverse('view-request', args=[id]))