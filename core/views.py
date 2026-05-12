from django.shortcuts import render

def home_view(request):
    return render(request, 'home.html')

def courses_view(request):
    return render(request, 'courses.html')

def my_courses_view(request):
    return render(request, 'my-courses.html')

def exams_view(request):
    return render(request, 'exams.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')

def signin_view(request):
    return render(request, 'signin.html')

def signup_view(request):
    return render(request, 'signup.html')