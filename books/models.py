from django.db import models

# Create your models here.

from django.db import models

class Book:
    """
    A class to represent a book from the external API.
    """
    def __init__(self, id, title, author, year, cover_url=None, created_at=None, updated_at=None):
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.cover_url = cover_url or f"https://covers.openlibrary.org/b/isbn/{id}-L.jpg"
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_available = True  # Default availability status

    @classmethod
    def from_dict(cls, data):
        """Create a Book instance from a dictionary (API response)"""
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
    A class to manage recently viewed books using a stack data structure.
    """
    def __init__(self, max_size=5):
        self._books = []
        self._max_size = max_size
        self._book_ids = set()  # For O(1) lookup

    def add_book(self, book):
        """Add a book to recently viewed stack"""
        if book.id in self._book_ids:
            # Remove existing entry to move it to top
            self._books = [b for b in self._books if b.id != book.id]
            self._book_ids.remove(book.id)
        
        self._books.append(book)
        self._book_ids.add(book.id)
        
        # Remove oldest if exceeding max size
        if len(self._books) > self._max_size:
            oldest = self._books.pop(0)
            self._book_ids.remove(oldest.id)
    
    def get_books(self):
        """Get list of recently viewed books"""
        return list(reversed(self._books))  # Most recent first

class Borrowing(models.Model):
    """Model for tracking book borrowings"""
    book_id = models.CharField(max_length=50)  # Changed to CharField to handle OpenLibrary IDs
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
