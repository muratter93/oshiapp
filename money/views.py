from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from .models import Wallet, CheerCoinPurchase 

from subscription.models import SubMember

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
        "PAYJP_PUBLIC_KEY": settings.PAYJP_PUBLIC_KEY,  # ← 追加
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

# チアコ購入履歴用
@login_required
def purchase_history(request):
    cheer_purchases = CheerCoinPurchase.objects.filter(member=request.user).order_by('-purchased_at')
    return render(request, 'money/purchase_history.html', {  
        'cheer_purchases': cheer_purchases,
    })


# サブスク購入履歴用
@login_required
def purchase_history2(request):
    stanning_purchases = (
        SubMember.objects
        .filter(member=request.user)
        .select_related('plan')
        .order_by('-sign_up')
    )
    return render(request, 'money/purchase_history2.html', {
        'stanning_purchases': stanning_purchases,
    })

# 決済
import payjp
from django.conf import settings

@login_required
@transaction.atomic
def pay_execute(request):
    if request.method != "POST":
        return redirect("money:charge")

    token = request.POST.get("payjp-token")
    coins = int(request.POST.get("coins", 0))

    plan = _find_plan_by_coins(coins)
    if not token or not plan:
        messages.error(request, "不正な決済リクエストです。")
        return redirect("money:charge")

    # 金額は必ずサーバー側で決定
    amount = plan["price"]

    payjp.api_key = settings.PAYJP_SECRET_KEY

    try:
        charge = payjp.Charge.create(
            amount=amount,
            currency="jpy",
            card=token,
        )
    except payjp.error.PayjpError:
        messages.error(request, "決済に失敗しました。")
        return redirect("money:charge")

    # 決済成功 → コイン付与
    wallet, _ = Wallet.objects.select_for_update().get_or_create(member=request.user)
    wallet.cheer_coin_balance += plan["coins"]
    wallet.save(update_fields=["cheer_coin_balance"])

    CheerCoinPurchase.objects.create(
        member=request.user,
        coins=plan["coins"],
        price=amount,
        # payjp_charge_id=charge.id,
    )

    return redirect(
        f"{reverse('money:charge')}?done=1&coins={plan['coins']}&price={amount}"
    )
