from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # مسار خريطة الموقع الـ SEO
    path('sitemap.xml', TemplateView.as_view(template_name="sitemap.xml", content_type="text/xml")),

    # ربط الموقع بتطبيق core
    path('', include('core.urls')), 
]