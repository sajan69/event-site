# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from .models import Contact, CustomUser, OTP
from .forms import CustomUserCreationForm, CustomPasswordChangeForm
from tickets.models import Ticket
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
           
                login(request, user)
                return redirect('events:home')
           
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, 'authentication/login.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            # Store email in session for OTP verification
            request.session['verification_email'] = user.email
            request.session['is_registration'] = True
            
            send_otp(request, user)
            messages.success(request, "Registration successful. Please verify your email.")
            return redirect('authentication:verify_otp')
    else:
        messages.error(request, "Invalid email or password.")
        form = CustomUserCreationForm()
    return render(request, 'authentication/register.html', {'form': form})

def send_otp(request, user):
    """Generate and send OTP to user"""
    try:
        # Delete any existing non-expired OTPs for this user
        OTP.objects.filter(user=user, expires_at__gt=timezone.now()).delete()
        
        # Generate new OTP
        otp = get_random_string(6, allowed_chars='0123456789')
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        # Save OTP
        OTP.objects.create(
            user=user,
            otp=otp,
            expires_at=expires_at
        )
        
        # Send email
        send_mail(
            'Your OTP for Event Master',
            f'Your OTP is: {otp}\nThis OTP will expire in 10 minutes.',
            'noreply@eventmaster.com',
            [user.email],
            fail_silently=False,
        )
        
        return True, "OTP sent successfully."
    except Exception as e:
        return False, str(e)

@require_http_methods(["POST"])
def resend_otp(request):
    """Handle OTP resend requests"""
    email = request.session.get('verification_email')
    
    if not email:
        return JsonResponse({
            'status': 'error',
            'message': 'No email found for verification.'
        }, status=400)
    
    try:
        user = CustomUser.objects.get(email=email)
        success, message = send_otp(request, user)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'OTP resent successfully.'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to send OTP: {message}'
            }, status=500)
            
    except CustomUser.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User not found.'
        }, status=404)

def verify_otp(request):
    """Handle OTP verification"""
    # Get email from session
    email = request.session.get('verification_email')
    is_registration = request.session.get('is_registration', False)
    
    if not email:
        messages.error(request, "No email found for verification.")
        return redirect('authentication:login')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        
        if not otp:
            messages.error(request, "OTP is required.")
            return render(request, 'authentication/verify_otp.html', {
                'email': email,
                'is_registration': is_registration
            })
            
        try:
            # Get latest OTP for the user
            otp_obj = OTP.objects.filter(
                user__email=email,
                otp=otp
            ).latest('created_at')
            
            if otp_obj.is_valid():
                user = otp_obj.user
                
                # Handle registration verification
                if is_registration:
                    user.is_active = True
                    user.is_verified = True
                    user.save()
                    login(request, user)
                    messages.success(request, "Email verified successfully.")
                    
                # Handle password reset verification
                elif request.session.get('is_password_reset'):
                    request.session['reset_password_user_id'] = user.id
                    return redirect('authentication:reset_password')
                
                # Clean up
                otp_obj.delete()
                request.session.pop('verification_email', None)
                request.session.pop('is_registration', None)
                request.session.pop('is_password_reset', None)
                
                return redirect('events:home')
            else:
                messages.error(request, "OTP has expired. Please request a new one.")
                
        except OTP.DoesNotExist:
            messages.error(request, "Invalid OTP. Please try again.")
    
    return render(request, 'authentication/verify_otp.html', {
        'email': email,
        'is_registration': is_registration
    })

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, "Email is required.")
            return render(request, 'authentication/forgot_password.html')
            
        try:
            user = CustomUser.objects.get(email=email)
            
            # Store email in session for verification
            request.session['verification_email'] = email
            request.session['is_password_reset'] = True
            
            success, message = send_otp(request, user)
            
            if success:
                messages.success(request, "OTP sent to your email for password reset.")
                return redirect('authentication:verify_otp')
            else:
                messages.error(request, f"Failed to send OTP: {message}")
                
        except CustomUser.DoesNotExist:
            messages.error(request, "No user found with that email address.")
            
    return render(request, 'authentication/forgot_password.html')

@login_required
def profile(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'authentication/profile.html', {
        'user': request.user,
        'tickets': tickets
    })

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'authentication/my_tickets.html', {
        'tickets': tickets
    })

def logout_user(request):
    logout(request)
    return redirect('events:home')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('authentication:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'authentication/change_password.html', {'form': form})