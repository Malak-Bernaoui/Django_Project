<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Penalty;
use Carbon\Carbon;
use Illuminate\Http\Request;

class PenaltyController extends Controller
{
    public function index(Request $request)
    {
        $query = Penalty::query()->with(['user', 'loan.book'])->orderByDesc('id');

        if ($request->filled('status')) {
            $query->where('status', $request->string('status'));
        }

        if ($request->filled('user_id')) {
            $query->where('user_id', $request->integer('user_id'));
        }

        return response()->json($query->paginate(10));
    }

    public function pay(Penalty $penalty)
    {
        if ($penalty->status === Penalty::STATUS_PAID) {
            return response()->json(['message' => 'Pénalité déjà payée.'], 422);
        }

        $penalty->update([
            'status' => Penalty::STATUS_PAID,
            'paid_at' => Carbon::now(),
        ]);

        return response()->json($penalty->load(['user', 'loan.book']));
    }
}
