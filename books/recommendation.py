"""
Yo! Ini file buat sistem rekomendasi buku!

1. GRAPH
   - Kita bikin graph buat nyambungin buku-buku yang related
   - Tiap buku = node
   - Hubungan antar buku = edge
   - Weight = seberapa mirip bukunya (based on author)
"""

from collections import defaultdict, Counter
import requests
from typing import Dict, List, Set, Tuple
from .models import Book

class BookGraph:
    """
    Mantap! Class ini tuh buat sistem rekomendasi pake konsep graph.
    Graph-nya gini nih bentuknya:
    
    Buku A ----0.8---- Buku B
       \\                  /
        0.5          0.6
          \\          /
              Buku C
              
    - Weight 0.8: Buku A & B mirip bgt (sama penulisnya)
    - Weight 0.6: Buku B & C lumayan mirip
    - Weight 0.5: Buku A & C agak mirip dikit
    """
    def __init__(self):
        # bikin dictionary kosong buat graph dan cache
        self.graph: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.book_cache: Dict[str, Book] = {}

    def add_book(self, book: Book) -> None:
        """Nambahin buku baru ke graph kita"""
        if book.id not in self.book_cache:
            self.book_cache[book.id] = book
            self._build_relationships(book)

    def _build_relationships(self, book: Book) -> None:
        """
        Bikin koneksi antar buku berdasarkan penulisnya
        Cara kerjanya:
        1. Cari buku-buku dari penulis yang sama
        2. Koneksiin buku-buku tsb di graph
        3. Kasih bobot 1.0 kalo authornya sama
        """
        try:
            # nyari buku dari penulis yang sama
            author_works_url = f"https://openlibrary.org/search.json?author={book.author}&limit=10"
            author_response = requests.get(author_works_url)
            author_books = author_response.json().get('docs', [])
            
            # tambahin ke graph dengan bobot 1.0 (soalnya authornya sama)
            for related_book in author_books:
                if related_book.get('key', '').startswith('/works/'):
                    related_id = related_book['key'].split('/')[-1]
                    if related_id != book.id:
                        self.graph[book.id][related_id] += 1.0
                        self.graph[related_id][book.id] += 1.0

        except Exception as e:
            print(f"Waduh error nih pas bikin relasi buat buku {book.id}: {str(e)}")

    def get_recommendations(self, book_id: str, limit: int = 5) -> List[Tuple[Book, float]]:
        """
        Nyari rekomendasi buku berdasarkan graph
        Parameters:
        - book_id: ID buku yang mau dicarian rekomendasinya
        - limit: Mau berapa rekomendasi? (defaultnya 5)
        Returns:
        - List of (Book, weight) -> buku yang direkomendasiin + score kemiripannya
        """
        if book_id not in self.graph:
            return []

        # Sort buku yang related berdasarkan weightnya
        related_books = sorted(
            self.graph[book_id].items(),
            key=lambda x: x[1],
            reverse=True  # dari yang paling gede weightnya
        )

        # Ambil top recommendations sesuai limit
        recommendations = []
        for related_id, weight in related_books[:limit]:
            # Kalo bukunya belom ada di cache, kita fetch dulu datanya
            if related_id not in self.book_cache:
                try:
                    work_response = requests.get(f"https://openlibrary.org/works/{related_id}.json")
                    work_data = work_response.json()
                    
                    # Cari nama penulisnya
                    author_name = 'Penulis Tidak Diketahui'
                    if 'authors' in work_data and work_data['authors']:
                        author_key = work_data['authors'][0].get('author', {}).get('key')
                        if author_key:
                            author_resp = requests.get(f"https://openlibrary.org{author_key}.json")
                            author_data = author_resp.json()
                            author_name = author_data.get('name', 'Penulis Tidak Diketahui')
                    
                    # Ambil tahun terbit
                    year_response = requests.get(f"https://openlibrary.org/works/{related_id}/editions.json?limit=1&sort=first_publish_year")
                    year_data = year_response.json()
                    year = year_data.get('entries', [{}])[0].get('first_publish_year', 0)
                    
                    # Bikin objek buku baru
                    book = Book(
                        id=related_id,
                        title=work_data.get('title', 'Judul Tidak Diketahui'),
                        author=author_name,
                        year=year,
                        cover_url=f"https://covers.openlibrary.org/b/id/{work_data.get('covers', [0])[0]}-L.jpg" if 'covers' in work_data and work_data['covers'] else None
                    )
                    self.book_cache[related_id] = book
                except Exception as e:
                    print(f"Duh error nih pas ngambil detail buku {related_id}: {str(e)}")
                    continue
            
            recommendations.append((self.book_cache[related_id], weight))

        return recommendations

# Bikin satu instance global buat dipake di aplikasi
book_recommender = BookGraph()
