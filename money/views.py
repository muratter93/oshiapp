from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from .models import Wallet, CheerCoinPurchase 

COIN_PLANS = [
    {"coins": 100,  "price": 100},
    {"coins": 1000, "price": 1000},
    {"coins": 3600, "price": 3000},
    {"coins": 7000, "price": 5000},
]

def _find_plan_by_coins(coins: int):
    return next((p for p in COIN_PLANS if p["coins"] == coins), None)

def charge(request):

    # チャージ画面表示（ログアウトでも閲覧可）。
    wallet = None
    if request.user.is_authenticated:
        wallet, _ = Wallet.objects.get_or_create(member=request.user)

    return render(request, "money/charge.html", {
        "wallet": wallet,
        "plans": COIN_PLANS,
        "can_purchase": request.user.is_authenticated,
        "login_url": f"{reverse('accounts:login')}?next={request.get_full_path()}",
    })

@login_required
@transaction.atomic
def buy_coins(request, coins: int):

    if request.method != "POST":
        return redirect("money:charge")

    plan = _find_plan_by_coins(coins)
    if not plan:
        messages.error(request, "不正な購入リクエストです。")
        return redirect("money:charge")

    wallet, _ = Wallet.objects.select_for_update().get_or_create(member=request.user)
    wallet.cheer_coin_balance += plan["coins"]
    # wallet.stanning_point_balance += plan["coins"] // 100
    wallet.save(update_fields=["cheer_coin_balance", "stanning_point_balance"])

     #  購入履歴を登録
    CheerCoinPurchase.objects.create(
        member=request.user,
        coins=plan["coins"],
        price=plan["price"],
    )

    charge_url = reverse("money:charge")
    return redirect(f"{charge_url}?done=1&coins={plan['coins']}&price={plan['price']}")

# チアコイン購入履歴
@login_required
def purchase_history(request):
    # ログインユーザーの購入履歴を取得（作成日時の新しい順）
    purchases = CheerCoinPurchase.objects.filter(member=request.user).order_by('-purchased_at')
    return render(request, 'money/cheer-purchases.html', {'purchases': purchases})