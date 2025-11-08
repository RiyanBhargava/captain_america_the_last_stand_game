import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from google.auth.transport import requests
from google.oauth2 import id_token
from django.conf import settings
from .models import User
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/game/')
    return render(request, 'authentication/login.html', {
        'google_client_id': settings.GOOGLE_OAUTH2_CLIENT_ID
    })

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/game/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'authentication/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'authentication/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'authentication/register.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        login(request, user)
        messages.success(request, 'Account created successfully!')
        # Add flag to show tutorial popup
        request.session['show_tutorial'] = True
        return redirect('/game/')
    
    return render(request, 'authentication/register.html')

@csrf_exempt
@require_http_methods(["POST"])
def google_auth(request):
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        # Verify the Google token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), settings.GOOGLE_OAUTH2_CLIENT_ID
        )
        
        # Get user info from Google
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo['name']
        avatar_url = idinfo.get('picture', '')
        
        # Check if user exists
        try:
            user = User.objects.get(google_id=google_id)
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
                
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=name.split(' ')[0] if ' ' in name else name,
                last_name=' '.join(name.split(' ')[1:]) if ' ' in name else '',
                google_id=google_id,
                avatar_url=avatar_url
            )
        
        # Update avatar URL if changed
        if user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            user.save()
        
        # Log in the user
        login(request, user)
        
        return JsonResponse({'success': True, 'redirect_url': '/game/'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('/auth/login/')

@login_required
def profile_view(request):
    return render(request, 'authentication/profile.html', {
        'user': request.user
    })
