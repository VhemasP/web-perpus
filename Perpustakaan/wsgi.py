"""
WSGI config for Perpustakaan project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

"""
Ini file WSGI (Web Server Gateway Interface) buat deployment!

- Cara kerja: Web Server (nginx/apache) -> WSGI -> Django App
- Jadi kalo udah mau dipake beneran (production), pake file ini
- Kalo masih development mah pake manage.py runserver aja 😉
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Perpustakaan.settings')

application = get_wsgi_application()
