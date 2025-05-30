#!/usr/bin/env python
"""
Ini file manage.py, buat ngejalanin command Django!

Yang bisa dilakuin:
- python manage.py runserver -> Jalanin development server
- python manage.py migrate -> Update database
- python manage.py createsuperuser -> Bikin admin account
- python manage.py shell -> Buka Python shell + Django context

"""

import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Perpustakaan.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
