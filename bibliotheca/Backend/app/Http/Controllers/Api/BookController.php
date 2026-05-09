<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Book;
use App\Models\Loan;
use Illuminate\Http\Request;

class BookController extends Controller
{
    public function index()
    {
        return response()->json(Book::query()->orderByDesc('id')->paginate(10));
    }

    public function show(Book $book)
    {
        return response()->json($book);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'author' => ['required', 'string', 'max:255'],
            'isbn' => ['nullable', 'string', 'max:255', 'unique:books,isbn'],
            'category' => ['nullable', 'string', 'max:255'],
            'published_year' => ['nullable', 'integer', 'min:0'],
            'copies_total' => ['required', 'integer', 'min:0'],
        ]);

        $data['copies_available'] = $data['copies_total'];

        $book = Book::create($data);

        return response()->json($book, 201);
    }

    public function update(Request $request, Book $book)
    {
        $data = $request->validate([
            'title' => ['sometimes', 'required', 'string', 'max:255'],
            'author' => ['sometimes', 'required', 'string', 'max:255'],
            'isbn' => ['sometimes', 'nullable', 'string', 'max:255', 'unique:books,isbn,' . $book->id],
            'category' => ['sometimes', 'nullable', 'string', 'max:255'],
            'published_year' => ['sometimes', 'nullable', 'integer', 'min:0'],
            'copies_total' => ['sometimes', 'required', 'integer', 'min:0'],
        ]);

        if (array_key_exists('copies_total', $data)) {
            $borrowedCount = Loan::query()
                ->where('book_id', $book->id)
                ->where('status', 'borrowed')
                ->count();

            if ($data['copies_total'] < $borrowedCount) {
                return response()->json([
                    'message' => 'copies_total ne peut pas être inférieur au nombre d\'emprunts en cours.',
                ], 422);
            }

            $data['copies_available'] = $data['copies_total'] - $borrowedCount;
        }

        $book->update($data);

        return response()->json($book);
    }

    public function destroy(Book $book)
    {
        $activeLoans = $book->loans()->where('status', 'borrowed')->exists();
        if ($activeLoans) {
            return response()->json([
                'message' => 'Impossible de supprimer un livre avec des emprunts actifs.',
            ], 422);
        }

        $book->delete();

        return response()->json(['deleted' => true]);
    }
}
