from collections import defaultdict, Counter
import requests
from typing import Dict, List, Set, Tuple
from .models import Book

# yang ini gunain graph untuk rekomendasi buku
class BookGraph:
    def __init__(self):
        self.graph: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.book_cache: Dict[str, Book] = {}

    def add_book(self, book: Book) -> None:
        """Add a book to the graph"""
        if book.id not in self.book_cache:
            self.book_cache[book.id] = book
            self._build_relationships(book)

    def _build_relationships(self, book: Book) -> None:
        """Build relationships for a book based on author only"""
        try:
            # Find books with same author
            author_works_url = f"https://openlibrary.org/search.json?author={book.author}&limit=10"
            author_response = requests.get(author_works_url)
            author_books = author_response.json().get('docs', [])
            
            # Add author relationships (weight: 1.0)
            for related_book in author_books:
                if related_book.get('key', '').startswith('/works/'):
                    related_id = related_book['key'].split('/')[-1]
                    if related_id != book.id:
                        self.graph[book.id][related_id] += 1.0
                        self.graph[related_id][book.id] += 1.0

        except Exception as e:
            print(f"Error building relationships for book {book.id}: {str(e)}")

    def get_recommendations(self, book_id: str, limit: int = 5) -> List[Tuple[Book, float]]:
        """Get book recommendations based on graph relationships"""
        if book_id not in self.graph:
            return []

        # Sort related books by weight
        related_books = sorted(
            self.graph[book_id].items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Get top recommendations
        recommendations = []
        for related_id, weight in related_books[:limit]:
            # Fetch book details if not in cache
            if related_id not in self.book_cache:
                try:
                    work_response = requests.get(f"https://openlibrary.org/works/{related_id}.json")
                    work_data = work_response.json()
                    
                    # Get author name
                    author_name = 'Unknown Author'
                    if 'authors' in work_data and work_data['authors']:
                        author_key = work_data['authors'][0].get('author', {}).get('key')
                        if author_key:
                            author_resp = requests.get(f"https://openlibrary.org{author_key}.json")
                            author_data = author_resp.json()
                            author_name = author_data.get('name', 'Unknown Author')
                    
                    # Get year
                    year_response = requests.get(f"https://openlibrary.org/works/{related_id}/editions.json?limit=1&sort=first_publish_year")
                    year_data = year_response.json()
                    year = year_data.get('entries', [{}])[0].get('first_publish_year', 0)
                    
                    book = Book(
                        id=related_id,
                        title=work_data.get('title', 'Unknown Title'),
                        author=author_name,
                        year=year,
                        cover_url=f"https://covers.openlibrary.org/b/id/{work_data.get('covers', [0])[0]}-L.jpg" if 'covers' in work_data and work_data['covers'] else None
                    )
                    self.book_cache[related_id] = book
                except Exception as e:
                    print(f"Error fetching book details for {related_id}: {str(e)}")
                    continue
            
            recommendations.append((self.book_cache[related_id], weight))

        return recommendations

# Create a global instance
book_recommender = BookGraph()
