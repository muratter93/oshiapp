from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from animals.models import Animal
from money.models import Wallet

def index(request):
    animals = Animal.objects.filter(animal_id__lte=100, is_active=True)

    ranking = Animal.objects.filter(is_active=True).order_by('-total_point')[:10]

    wallet = None
    if request.user.is_authenticated:
        wallet = Wallet.objects.filter(member=request.user).first()

    return render(request, "main/index.html", {
        "animals": animals,
        "ranking": ranking,
        "wallet": wallet,
    })


@transaction.atomic
def like(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "invalid request"}, status=400)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "login required"}, status=403)

    animal = get_object_or_404(Animal, pk=pk)
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

    from django.template.loader import render_to_string
    ranking = Animal.objects.order_by('-total_point')[:10]
    ranking_html = render_to_string("ranking/top.html", {"ranking": ranking}, request=request)

    return JsonResponse({
        "total_point": animal.total_point,
        "cheer_coin_balance": wallet.cheer_coin_balance,
        "stanning_point_balance": wallet.stanning_point_balance,
        "ranking_html": ranking_html,
    })