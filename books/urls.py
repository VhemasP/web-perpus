"""
Ini nih mapping URL ke views!
Jadi kalo user akses URL tertentu, bakal di-handle sama function yang sesuai.

Routes yang ada:
1. / -> Homepage, nampilin daftar buku
2. /about/ -> About page kita
3. /borrowed/ -> List buku yang dipinjam
4. /book/<id>/ -> Detail buku
5. /book/<id>/borrow/ -> Minjem buku
6. /book/<id>/return/ -> Balikin buku
7. /search/ -> Nyari buku
"""

from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about_us, name='about'),
    path('borrowed/', views.borrowed_books, name='borrowed'),
    path('book/<str:book_id>/', views.book_detail, name='detail'),
    path('book/<str:book_id>/borrow/', views.borrow_book, name='borrow'),
    path('book/<str:book_id>/return/', views.return_book, name='return'),
    path('search/', views.search_books, name='search'),
]
