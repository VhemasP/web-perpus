from django.db import models

# Create your models here.

from django.db import models

class Book:

    def __init__(self, id, title, author, year, cover_url=None, created_at=None, updated_at=None):
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.cover_url = cover_url or f"https://covers.openlibrary.org/b/isbn/{id}-L.jpg"
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_available = True  

    @classmethod
    def from_dict(cls, data):

        return cls(
            id=data.get('id'),
            title=data.get('title'),
            author=data.get('author'),
            year=data.get('year'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

class RecentlyViewedBooks:
    """
    Ini gunain stack ya cuy
    """
    def __init__(self, max_size=5):
        self._books = []
        self._max_size = max_size
        self._book_ids = set()  

    def add_book(self, book):

        if book.id in self._book_ids:

            self._books = [b for b in self._books if b.id != book.id]
            self._book_ids.remove(book.id)
        
        self._books.append(book)
        self._book_ids.add(book.id)

        if len(self._books) > self._max_size:
            oldest = self._books.pop(0)
            self._book_ids.remove(oldest.id)
    
    def get_books(self):

        return list(reversed(self._books)) 

class Borrowing(models.Model):

    book_id = models.CharField(max_length=50) 
    book_title = models.CharField(max_length=255)
    borrower_name = models.CharField(max_length=100)
    borrow_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('borrowed', 'Borrowed'),
            ('returned', 'Returned'),
        ],
        default='borrowed'
    )

    class Meta:
        ordering = ['-borrow_date']

    def __str__(self):
        return f"{self.book_title} - {self.borrower_name} ({self.status})"
