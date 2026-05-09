<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Book;
use App\Models\Reservation;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class ReservationController extends Controller
{
    public function index(Request $request)
    {
        $query = Reservation::query()->with(['user', 'book'])->orderByDesc('id');

        if ($request->filled('status')) {
            $query->where('status', $request->string('status'));
        }

        if ($request->filled('user_id')) {
            $query->where('user_id', $request->integer('user_id'));
        }

        return response()->json($query->paginate(10));
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'user_id' => ['required', 'integer', 'exists:users,id'],
            'book_id' => ['required', 'integer', 'exists:books,id'],
        ]);

        return DB::transaction(function () use ($data) {
            $user = User::query()->findOrFail($data['user_id']);
            $book = Book::query()->lockForUpdate()->findOrFail($data['book_id']);

            $alreadyActive = Reservation::query()
                ->where('user_id', $user->id)
                ->where('book_id', $book->id)
                ->where('status', Reservation::STATUS_ACTIVE)
                ->exists();

            if ($alreadyActive) {
                return response()->json(['message' => 'Réservation déjà active pour ce livre.'], 422);
            }

            $reservation = Reservation::create([
                'user_id' => $user->id,
                'book_id' => $book->id,
                'reserved_at' => Carbon::now(),
                'status' => Reservation::STATUS_ACTIVE,
            ]);

            return response()->json($reservation->load(['user', 'book']), 201);
        });
    }

    public function cancel(Reservation $reservation)
    {
        if ($reservation->status !== Reservation::STATUS_ACTIVE) {
            return response()->json(['message' => 'Réservation non active.'], 422);
        }

        $reservation->update(['status' => Reservation::STATUS_CANCELLED]);

        return response()->json($reservation->load(['user', 'book']));
    }
}
