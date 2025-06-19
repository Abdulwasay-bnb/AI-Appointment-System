from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import UserProfile
from datetime import datetime, timedelta
import random

# Create your views here.
def home(request):
    """
    Render the home page.
    """
    return render(request, 'index.html')

@login_required(login_url='login')
def dashboard(request):
    """Render the user dashboard with personalized content."""

    return render(request, 'dashboard.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def logout_view(request):
    """
    Handle user logout and redirect to home page.
    """
    logout(request)
    return redirect('home')

@login_required(login_url='login')
def profile_view(request):
    """Render the user profile page."""
    context = {
        'user': request.user,
        'profile': request.user.userprofile
    }
    return render(request, 'profile.html', context)