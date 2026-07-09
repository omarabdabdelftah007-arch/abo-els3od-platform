from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # الصفحة الرئيسية
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home'),

    # الكورسات
    path('courses/', views.courses_list_view, name='courses_list'),
    path('my-courses/', views.my_courses_view, name='my_courses'),
    
    # 🔓 السطر الجديد: مسار تفعيل الاشتراك التلقائي للكورسات المجانية
    path('course/<int:month_id>/enroll-free/', views.enroll_free_course_view, name='enroll_free_course'),
    
    path('exam/<int:exam_id>/', views.take_exam_view, name='take_exam'),
    path('exam/<int:exam_id>/result/', views.exam_result_view, name='exam_result'),
    path('watch/<int:month_id>/', views.course_watch, name='course_watch'),
    path('courses/<int:month_id>/watch/', views.course_watch, name='course_watch'),

    # الامتحانات والنتائج
    path('exams/', views.exams_view, name='exams'),
    path('results/', views.results_view, name='results'),

    # الحسابات
    path('signin/', views.signin_view, name='signin'),
    path('signup/', views.signup_view, name='signup'),
    path('signout/', views.signout_view, name='signout'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 