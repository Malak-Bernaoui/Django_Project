<?php

use App\Http\Controllers\Api\BookController;
use App\Http\Controllers\Api\LoanController;
use App\Http\Controllers\Api\PenaltyController;
use App\Http\Controllers\Api\ReservationController;
use Illuminate\Support\Facades\Route;

Route::get('/health', function () {
    return response()->json(['status' => 'ok']);
});

Route::apiResource('books', BookController::class);

Route::get('loans', [LoanController::class, 'index']);
Route::post('loans/borrow', [LoanController::class, 'borrow']);
Route::post('loans/{loan}/return', [LoanController::class, 'return']);
Route::get('loans/history', [LoanController::class, 'history']);

Route::get('reservations', [ReservationController::class, 'index']);
Route::post('reservations', [ReservationController::class, 'store']);
Route::post('reservations/{reservation}/cancel', [ReservationController::class, 'cancel']);

Route::get('penalties', [PenaltyController::class, 'index']);
Route::post('penalties/{penalty}/pay', [PenaltyController::class, 'pay']);
