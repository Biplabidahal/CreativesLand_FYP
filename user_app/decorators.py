from django.shortcuts import redirect,HttpResponse
from .models import EmailVerification
from django.contrib import messages

def role_required(roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            email_verification = EmailVerification.objects.get(user=request.user)

            if(email_verification.is_verified == False):
                messages.error(request, 'Please verify your email address.')
                return redirect('verify')
            
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse("You do not have permission to access this page.")
        return wrapper
    return decorator
