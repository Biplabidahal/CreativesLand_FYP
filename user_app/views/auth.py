from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from ..models import CustomUser, EmailVerification
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
import random
import uuid
from django.utils import timezone
from datetime import timedelta

# verification code for the 6 digit code
def generate_verification_code():
    return str(random.randint(100000, 999999))


def send_verification_email(email, code):
    subject = "Verify your email address"
    message = f"This is your email verification code: {code}"
    send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
    print(f"Verification code for {email}: {code}")



def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, "Please fill in all fields.")
            return render(request, 'auth/login.html')
        
        # Get the user by email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, 'auth/login.html')
        
        # Check the password
        if user.check_password(password):
            if user.is_active:
                auth_login(request, user)
                messages.success(request, "Login successful!")

                # check the user is verified or not
                check_email_verification = EmailVerification.objects.get(user=user)

                if not check_email_verification.is_verified:
                    messages.error(request, "Please verify your email address.")
                    return redirect('verify')

                
                return redirect('home')
            else:
                messages.error(request, "Your account is not active.")
                return render(request, 'auth/login.html')
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, 'auth/login.html')
    
    return render(request, 'auth/login.html')


def logout(request):
    auth_logout(request)
    messages.success(request, "Logout successful!")
    return redirect('home')


def register(request):
    if request.method == 'POST':
        # Get form fields using the new names from the updated UI
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone')
        dob = request.POST.get('dob')
        terms = request.POST.get('terms')

        # Validate Terms acceptance
        if not terms:
            messages.error(
                request,
                "You must agree to the Terms of Service and Privacy Policy."
            )
            return render(request, 'auth/register.html')

        # Validate password matching
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'auth/register.html')

        # Check for duplicate email
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email address is already registered.")
            return render(request, 'auth/register.html')

        # Check for existing username
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'auth/register.html')

        # Hash the password before saving the user instance
        hashed_password = make_password(password)

        try:
            # Create the new user object with the provided information
            user = CustomUser.objects.create(
                username=username,
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                dob=dob
            )

            # Generate a verification code and create an EmailVerification instance
            verification_code = generate_verification_code()
            EmailVerification.objects.create(
                user=user,
                code=verification_code
            )
            send_verification_email(email, verification_code)

            messages.success(
                request, "Email verification sent. Please check your email."
            )
            return redirect('login')

        except Exception as e:
            messages.error(
                request, f"An error occurred during registration: {str(e)}"
            )
            return render(request, 'auth/register.html')

    return render(request, 'auth/register.html')


def verify(request):

    if request.method == 'POST':
        # get the email from the session 
        email = request.user.email
        verification_code = request.POST.get('verification_code')

        # get the user by email
        user = CustomUser.objects.get(email=email)
        email_verification = EmailVerification.objects.get(user=user)

        if email_verification.code == verification_code:
            email_verification.is_verified = True
            email_verification.save()
            messages.success(request, "Email verified successfully!")
            return redirect('home')
        else:
            messages.error(request, "Invalid verification code. Please try again.")
            return redirect('verify')
    return render(request, 'auth/verify.html')
