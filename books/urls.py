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
