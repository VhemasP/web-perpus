"""
ASGI config for Perpustakaan project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

"""
Nah kalo ini file ASGI (Asynchronous Server Gateway Interface)!

- Lebih canggih dari WSGI soalnya bisa handle:
  * WebSocket
  * HTTP/2
  * Server-sent events
  
Tapi kita belom pake fitur-fitur itu sih, jadi ya udah gitu aja 😅
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Perpustakaan.settings')

application = get_asgi_application()
