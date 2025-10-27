from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from animals.models import Animal
from money.models import Wallet


def index(request):
    animals = Animal.objects.filter(animal_id__lte=16)
    wallet = None
    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(member=request.user).first()
    return render(request, "main/index.html", {"animals": animals, "wallet": wallet})

@transaction.atomic
def like(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "invalid request"}, status=400)

    animal = get_object_or_404(Animal, pk=pk)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "login required"}, status=403)

    wallet = Wallet.objects.select_for_update().filter(member=request.user).first()
    if wallet is None:
        return JsonResponse({"error": "ウォレットがありません。"}, status=400)

    if wallet.cheer_coin_balance < 100:
        return JsonResponse({"error": "チアコインが不足しています。"}, status=400)

    wallet.cheer_coin_balance -= 100
    wallet.stanning_point_balance += 1
    wallet.save(update_fields=["cheer_coin_balance", "stanning_point_balance"])

    animal.total_point += 1
    animal.save(update_fields=["total_point"])

    return JsonResponse({
        "total_point": animal.total_point,
        "cheer_coin_balance": wallet.cheer_coin_balance,
        "stanning_point_balance": wallet.stanning_point_balance,
    })
