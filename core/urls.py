from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('courses/', views.courses_view, name='courses'),
    path('my-courses/', views.my_courses_view, name='my_courses'),
    path('exams/', views.exams_view, name='exams'),
    path('results/', views.dashboard_view, name='results'),
    path('signin/', views.signin_view, name='signin'),
    path('signup/', views.signup_view, name='signup'),
]