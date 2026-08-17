"""
WSGI config for el_saoud_platform project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# ✅ تم تصحيح المسار ليوجه إلى ملف settings الصحيح داخل el_saoud_platform
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.el_saoud_platform.settings')

application = get_wsgi_application()