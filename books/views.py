from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
import requests
from requests.exceptions import RequestException, Timeout
import logging
from .models import Book, RecentlyViewedBooks, Borrowing
from .recommendation import book_recommender

# Inisialisasi tumpukan buku yang baru saja dilihat (stack)
recently_viewed = RecentlyViewedBooks(max_size=5)

class CategoryNode:
    def __init__(self, name, category_id):
        self.name = name
        self.category_id = category_id
        self.children = []
        
    def add_child(self, child):
        self.children.append(child)
        return child
        
    def to_dict(self):
        return {
            'name': self.name,
            'id': self.category_id,
            'children': [child.to_dict() for child in self.children]
        }

# Build category tree
def build_category_tree():
    root = CategoryNode("All Categories", "all")
    
    # Fiction category
    fiction = root.add_child(CategoryNode("Fiction", "fiction"))
    fiction.add_child(CategoryNode("Romance", "romance"))
    fiction.add_child(CategoryNode("Mystery", "mystery"))
    fiction.add_child(CategoryNode("Science Fiction", "sci-fi"))
    fiction.add_child(CategoryNode("Fantasy", "fantasy"))
    
    # Non-Fiction category
    non_fiction = root.add_child(CategoryNode("Non-Fiction", "non-fiction"))
    non_fiction.add_child(CategoryNode("Biography", "biography"))
    non_fiction.add_child(CategoryNode("History", "history"))
    non_fiction.add_child(CategoryNode("Science", "science"))
    non_fiction.add_child(CategoryNode("Self-Help", "self-help"))
    
    return root

# Initialize category tree
CATEGORY_TREE = build_category_tree()

logger = logging.getLogger(__name__)

# OpenLibrary API base URL
OPENLIBRARY_API_BASE = "https://openlibrary.org/search.json"

def clean_work_id(work_id):
    return work_id.replace('/works/', '')

def fetch_books(query="subject:fiction", limit=20, offset=0):
    """
    Fetch books from OpenLibrary API
    Args:
        query (str): Search query for books
        limit (int): Number of books per page
        offset (int): Number of books to skip
    Returns:
        list: List of Book objects
    """
    try:
        params = {
            'q': query,
            'limit': limit,
            'offset': offset,
            'fields': 'key,title,author_name,first_publish_year,cover_i',
            'sort': 'rating'  # Sort by rating to get more interesting books first
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
    """Menampilkan daftar buku"""
    try:
        category = request.GET.get('category', 'all')
        page = int(request.GET.get('page', 1))
        books_per_page = 20
        
        # Modify query based on selected category
        if category and category != 'all':
            query = f"subject:{category}"
        else:
            query = "subject:*"  # All books
            
        # Calculate offset for the API
        offset = (page - 1) * books_per_page
            
        # Fetch only the current page
        response = requests.get(
            OPENLIBRARY_API_BASE,
            params={
                'q': query,
                'limit': books_per_page,
                'offset': offset,
                'fields': 'key,title,author_name,first_publish_year,cover_i',
                'sort': 'rating'
            },
            timeout=10,
            headers={'Accept': 'application/json'}
        )
        response.raise_for_status()
        data = response.json()
        
        books = []
        if data.get('docs'):
            for doc in data.get('docs', []):
                work_id = clean_work_id(doc.get('key', ''))
                book = Book(
                    id=doc.get('key', '').split('/')[-1],
                    title=doc.get('title', 'Unknown Title'),
                    author=doc.get('author_name', ['Unknown Author'])[0] if doc.get('author_name') else 'Unknown Author',
                    year=doc.get('first_publish_year', 0),
                    cover_url=f"https://covers.openlibrary.org/b/id/{doc.get('cover_i', 0)}-L.jpg" if doc.get('cover_i') else None
                )
                book.is_available = not Borrowing.objects.filter(
                    book_id=book.id,
                    status='borrowed'
                ).exists()
                books.append(book)

        total_results = data.get('numFound', 0)
        shown_results = offset + len(books)
            
        # For HTMX/AJAX requests, return only the book items
        if request.headers.get('HX-Request'):
            return render(request, 'books/book_items.html', {
                'books': books,
                'has_more': shown_results < total_results
            })
            
        return render(request, 'books/index.html', {
            'books': books,
            'recently_viewed': recently_viewed.get_books(),
            'category_tree': CATEGORY_TREE.to_dict(),
            'selected_category': category,
            'total_results': total_results,
            'shown_results': shown_results,
            'has_more': shown_results < total_results
        })
    except Exception as e:
        logger.error(f"Error in index view: {str(e)}")
        messages.error(request, f"Error fetching books: {str(e)}")
        return render(request, 'books/index.html', {
            'books': [], 
            'recently_viewed': [],
            'category_tree': CATEGORY_TREE.to_dict(),
            'selected_category': 'all',
            'total_results': 0,
            'shown_results': 0,
            'has_more': False
        })
    
def book_detail(request, book_id):
    """Menampilkan detail buku """
    try:
        book_id = clean_work_id(book_id)

        # Ambil data works
        work_response = requests.get(f"https://openlibrary.org/works/{book_id}.json")
        work_response.raise_for_status()
        work_data = work_response.json()

        # Ambil data author
        author_name = 'Unknown Author'
        if 'authors' in work_data and work_data['authors']:
            author_key = work_data['authors'][0].get('author', {}).get('key')
            if author_key:
                author_resp = requests.get(f"https://openlibrary.org{author_key}.json")
                author_resp.raise_for_status()
                author_data = author_resp.json()
                author_name = author_data.get('name', 'Unknown Author')

        # Ambil data editions (untuk year)
        edition_response = requests.get(f"https://openlibrary.org/works/{book_id}/editions.json?limit=1&sort=first_publish_year")
        edition_response.raise_for_status()
        edition_data = edition_response.json()
        first_publish_year = work_data.get('first_publish_year', 0)
        if not first_publish_year and 'entries' in edition_data and edition_data['entries']:
            first_publish_year = edition_data['entries'][0].get('first_publish_year', 0)
        if not first_publish_year:
            first_publish_year = work_data.get('created', {}).get('value', '').split('-')[0]
            first_publish_year = int(first_publish_year) if first_publish_year.isdigit() else 0

        book = Book(
            id=book_id,
            title=work_data.get('title', 'Unknown Title'),
            author=author_name,
            year=first_publish_year,
            cover_url=f"https://covers.openlibrary.org/b/id/{work_data.get('covers', [0])[0]}-L.jpg"
                      if 'covers' in work_data and work_data['covers'] else None
        )        # Add book to recommender and get recommendations
        book_recommender.add_book(book)
        raw_recommendations = book_recommender.get_recommendations(book_id)
        
        # Fetch year information for recommended books
        recommendations = []
        for rec_book, similarity in raw_recommendations:
            # Ambil data works untuk recommended book
            rec_work_response = requests.get(f"https://openlibrary.org/works/{rec_book.id}.json")
            if rec_work_response.ok:
                rec_work_data = rec_work_response.json()
                rec_year = rec_work_data.get('first_publish_year', 0)
                if not rec_year:
                    rec_year = rec_work_data.get('created', {}).get('value', '').split('-')[0]
                    rec_year = int(rec_year) if rec_year.isdigit() else 0
                rec_book.year = rec_year
            recommendations.append((rec_book, similarity))

        # Cek status ketersediaan
        book.is_available = not Borrowing.objects.filter(
            book_id=book_id,
            status='borrowed'
        ).exists()

        # Riwayat peminjaman
        borrowing_history = Borrowing.objects.filter(book_id=book_id).order_by('-borrow_date')

        # Tambah ke recently viewed
        recently_viewed.add_book(book)

        return render(request, 'books/detail.html', {
            'book': book,
            'borrowing_history': borrowing_history,
            'recommendations': recommendations
        })
    except Exception as e:
        messages.error(request, f"Error fetching book details: {str(e)}")
        return redirect('books:index')



def borrowed_books(request):
    """Menampilkan semua buku yang dipinjam"""
    try:
        borrowed = Borrowing.objects.filter(status='borrowed').order_by('-borrow_date')
        return render(request, 'books/borrowed.html', {
            'borrowings': borrowed,
        })
    except Exception as e:
        messages.error(request, f"Error fetching borrowed books: {str(e)}")
        return redirect('books:index')

def about_us(request):
    """Menampilkan halaman about us"""
    return render(request, 'books/about.html')

def borrow_book(request, book_id):
    
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
