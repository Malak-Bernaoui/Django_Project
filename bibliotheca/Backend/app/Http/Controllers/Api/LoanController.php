<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Book;
use App\Models\Loan;
use App\Models\Penalty;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class LoanController extends Controller
{
    public function index(Request $request)
    {
        $query = Loan::query()->with(['user', 'book'])->orderByDesc('id');

        if ($request->filled('status')) {
            $query->where('status', $request->string('status'));
        }

        if ($request->filled('user_id')) {
            $query->where('user_id', $request->integer('user_id'));
        }

        return response()->json($query->paginate(10));
    }

    public function borrow(Request $request)
    {
        $data = $request->validate([
            'user_id' => ['required', 'integer', 'exists:users,id'],
            'book_id' => ['required', 'integer', 'exists:books,id'],
            'days' => ['nullable', 'integer', 'min:1', 'max:60'],
        ]);

        $days = (int) ($data['days'] ?? 14);

        return DB::transaction(function () use ($data, $days) {
            $book = Book::query()->lockForUpdate()->findOrFail($data['book_id']);
            $user = User::query()->findOrFail($data['user_id']);

            if ($book->copies_available <= 0) {
                return response()->json(['message' => 'Aucun exemplaire disponible.'], 422);
            }

            $activeLoansCount = Loan::query()
                ->where('user_id', $user->id)
                ->where('status', Loan::STATUS_BORROWED)
                ->count();

            if ($activeLoansCount >= 3) {
                return response()->json(['message' => 'Quota d\'emprunts atteint (max 3).'], 422);
            }

            $unpaidPenalty = Penalty::query()
                ->where('user_id', $user->id)
                ->where('status', Penalty::STATUS_UNPAID)
                ->exists();

            if ($unpaidPenalty) {
                return response()->json(['message' => 'Pénalité impayée: emprunt bloqué.'], 422);
            }

            $now = Carbon::now();

            $loan = Loan::create([
                'user_id' => $user->id,
                'book_id' => $book->id,
                'borrowed_at' => $now,
                'due_at' => $now->copy()->addDays($days),
                'status' => Loan::STATUS_BORROWED,
            ]);

            $book->decrement('copies_available');

            return response()->json($loan->load(['user', 'book']), 201);
        });
    }

    public function return(Request $request, Loan $loan)
    {
        if ($loan->status === Loan::STATUS_RETURNED) {
            return response()->json(['message' => 'Emprunt déjà retourné.'], 422);
        }

        return DB::transaction(function () use ($loan) {
            $loan->refresh();

            $now = Carbon::now();
            $loan->update([
                'returned_at' => $now,
                'status' => Loan::STATUS_RETURNED,
            ]);

            $book = Book::query()->lockForUpdate()->findOrFail($loan->book_id);
            $book->increment('copies_available');

            $daysLate = 0;
            if ($loan->due_at !== null && $now->greaterThan($loan->due_at)) {
                $daysLate = (int) $loan->due_at->diffInDays($now);
            }

            if ($daysLate > 0) {
                Penalty::firstOrCreate(
                    ['loan_id' => $loan->id],
                    [
                        'user_id' => $loan->user_id,
                        'amount' => $daysLate * 1.0,
                        'status' => Penalty::STATUS_UNPAID,
                    ]
                );
            }

            return response()->json($loan->load(['user', 'book', 'penalty']));
        });
    }

    public function history(Request $request)
    {
        $data = $request->validate([
            'user_id' => ['required', 'integer', 'exists:users,id'],
        ]);

        $query = Loan::query()
            ->where('user_id', $data['user_id'])
            ->with(['book', 'penalty'])
            ->orderByDesc('id');

        return response()->json($query->paginate(10));
    }
}
