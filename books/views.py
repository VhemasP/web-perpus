from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
import requests
from requests.exceptions import RequestException, Timeout
import logging
from .models import Book, RecentlyViewedBooks, Borrowing

# Initialize the recently viewed books stack
recently_viewed = RecentlyViewedBooks(max_size=5)

# Configure logging
logger = logging.getLogger(__name__)

# OpenLibrary API base URL
OPENLIBRARY_API_BASE = "https://openlibrary.org/search.json"

def clean_work_id(work_id):
    """Clean the work ID by removing the /works/ prefix if present"""
    return work_id.replace('/works/', '')

def fetch_books(query="subject:fiction", limit=20):
    """
    Fetch books from OpenLibrary API
    Args:
        query (str): Search query for books
        limit (int): Number of books to fetch
    Returns:
        list: List of Book objects
    """
    try:
        params = {
            'q': query,
            'limit': limit,
            'fields': 'key,title,author_name,first_publish_year,cover_i',
        }
        
        response = requests.get(
            OPENLIBRARY_API_BASE,
            params=params,
            timeout=10,
            headers={'Accept': 'application/json'}
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get('docs'):
            logger.warning(f"No books found for query: {query}")
            return []
            
        books = []
        for doc in data.get('docs', []):
            work_id = clean_work_id(doc.get('key', ''))
            book = Book(
                id=doc.get('key', '').split('/')[-1],
                title=doc.get('title', 'Unknown Title'),
                author=doc.get('author_name', ['Unknown Author'])[0] if doc.get('author_name') else 'Unknown Author',
                year=doc.get('first_publish_year', 0),
                cover_url=f"https://covers.openlibrary.org/b/id/{doc.get('cover_i', 0)}-L.jpg" if doc.get('cover_i') else None
            )
            books.append(book)
        return books
    except Timeout:
        logger.error(f"Timeout while fetching books from API for query: {query}")
        raise Exception("The request timed out. Please try again.")
    except RequestException as e:
        logger.error(f"Error fetching books from API: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 429:
                raise Exception("Too many requests. Please wait a moment and try again.")
            elif e.response.status_code >= 500:
                raise Exception("The book service is currently unavailable. Please try again later.")
        raise Exception(f"Error fetching books from API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching books: {str(e)}")
        raise Exception("An unexpected error occurred. Please try again later.")

def index(request):
    """Display the list of books"""
    try:
        books = fetch_books()
        # Check availability status
        for book in books:
            book.is_available = not Borrowing.objects.filter(
                book_id=book.id,
                status='borrowed'
            ).exists()
            
        return render(request, 'books/index.html', {
            'books': books,
            'recently_viewed': recently_viewed.get_books()
        })
    except Exception as e:
        messages.error(request, f"Error fetching books: {str(e)}")
        return render(request, 'books/index.html', {'books': [], 'recently_viewed': []})

def book_detail(request, book_id):
    """Display details of a specific book"""
    try:
        book_id = clean_work_id(book_id)
        response = requests.get(f"https://openlibrary.org/works/{book_id}.json")
        response.raise_for_status()
        book_data = response.json()
        
        book = Book(
            id=book_id,
            title=book_data.get('title', 'Unknown Title'),
            author=book_data.get('authors', [{'name': 'Unknown Author'}])[0].get('name', 'Unknown Author') if 'authors' in book_data else 'Unknown Author',
            year=book_data.get('first_publish_date', '').split(',')[-1].strip() if 'first_publish_date' in book_data else 0,
            cover_url=f"https://covers.openlibrary.org/b/id/{book_data.get('covers', [0])[0]}-L.jpg" if 'covers' in book_data and book_data['covers'] else None
        )
        
        # Check if book is currently borrowed
        book.is_available = not Borrowing.objects.filter(
            book_id=book_id,
            status='borrowed'
        ).exists()
        
        # Get borrowing history
        borrowing_history = Borrowing.objects.filter(book_id=book_id).order_by('-borrow_date')
        
        recently_viewed.add_book(book)
        
        return render(request, 'books/detail.html', {
            'book': book,
            'borrowing_history': borrowing_history
        })
    except Exception as e:
        messages.error(request, f"Error fetching book details: {str(e)}")
        return redirect('books:index')

def borrowed_books(request):
    """Display all currently borrowed books"""
    try:
        borrowed = Borrowing.objects.filter(status='borrowed').order_by('-borrow_date')
        return render(request, 'books/borrowed.html', {
            'borrowings': borrowed,
        })
    except Exception as e:
        messages.error(request, f"Error fetching borrowed books: {str(e)}")
        return redirect('books:index')

def about_us(request):
    """Display the About Us page"""
    return render(request, 'books/about.html')

def borrow_book(request, book_id):
    """Handle book borrowing"""
    if request.method == 'POST':
        try:
            book_id = clean_work_id(book_id)
            # Check if book is available
            if Borrowing.objects.filter(book_id=book_id, status='borrowed').exists():
                messages.error(request, "This book is currently unavailable")
                return redirect('books:detail', book_id=book_id)
            
            # Create borrowing record
            borrowing = Borrowing.objects.create(
                book_id=book_id,
                book_title=request.POST['book_title'],
                borrower_name=request.POST['borrower_name'],
                status='borrowed'
            )
            
            messages.success(request, "Book borrowed successfully!")
            return redirect('books:detail', book_id=book_id)
        except Exception as e:
            messages.error(request, f"Error borrowing book: {str(e)}")
            return redirect('books:detail', book_id=book_id)
    return redirect('books:detail', book_id=book_id)

def return_book(request, book_id):
    """Handle book return"""
    if request.method == 'POST':
        try:
            book_id = clean_work_id(book_id)
            borrowing = Borrowing.objects.get(
                book_id=book_id,
                status='borrowed'
            )
            borrowing.status = 'returned'
            borrowing.return_date = timezone.now()
            borrowing.save()
            
            messages.success(request, "Book returned successfully!")
        except Borrowing.DoesNotExist:
            messages.error(request, "No active borrowing found for this book")
        except Exception as e:
            messages.error(request, f"Error returning book: {str(e)}")
    return redirect('books:detail', book_id=book_id)

def search_books(request):
    """Search books by title or author"""
    query = request.GET.get('q', '').strip()
    if not query:
        return redirect('books:index')
        
    try:
        books = fetch_books(query=query, limit=20)
        if not books:
            messages.info(request, f"No books found matching '{query}'")
            return render(request, 'books/index.html', {
                'books': [],
                'recently_viewed': recently_viewed.get_books(),
                'search_query': query
            })
        
        # Check availability for each book
        for book in books:
            book.is_available = not Borrowing.objects.filter(
                book_id=book.id,
                status='borrowed'
            ).exists()
        
        return render(request, 'books/index.html', {
            'books': books,
            'recently_viewed': recently_viewed.get_books(),
            'search_query': query
        })
    except Exception as e:
        messages.error(request, f"Error searching books: {str(e)}")
        return redirect('books:index')
