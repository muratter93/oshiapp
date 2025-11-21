from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Animal

from gift.models import Gift

# ---- 詳細ページ ----
def detail(request, animal_id):
    animal = get_object_or_404(Animal, animal_id=animal_id)

    gifts = Gift.objects.filter(
        zoo=animal.zoo
    ).order_by("price")

    return render(request, "animals/detail.html", {
        "animal": animal,
        "gifts": gifts,
    })


# ---- ランキングページ ----
def ranking(request):
    animals = Animal.objects.order_by('-total_point')
    return render(request, "animals/ranking.html", {"animals": animals})

from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction

from animals.models import Animal
from money.models import Wallet  # アプリ名に合わせて

# ---- 推しP を +1 するAPI（コイン -100 付き）----
@require_POST
@transaction.atomic
def push_animal(request, animal_id):
    # ログイン必須
    if not request.user.is_authenticated:
        return JsonResponse(
            {"success": False, "error": "ログインが必要です。"},
            status=403
        )

    # 対象の動物を取得
    animal = get_object_or_404(Animal, animal_id=animal_id)

    # ウォレットをロック付きで取得
    try:
        wallet = (
            Wallet.objects
            .select_for_update()
            .get(member=request.user)
        )
    except Wallet.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "ウォレットがありません。"},
            status=400
        )

    # 残高チェック（100チアコイン必要）
    if wallet.cheer_coin_balance < 100:
        return JsonResponse(
            {"success": False, "error": "チアコインが不足しています。"},
            status=400
        )

    # --- 残高更新＆ポイント加算 ---

    # コイン -100、ユーザーの推しP +1
    wallet.cheer_coin_balance -= 100
    wallet.stanning_point_balance += 1
    wallet.save(update_fields=["cheer_coin_balance", "stanning_point_balance"])

    # 動物側の total_point も +1
    animal.total_point += 1
    animal.save(update_fields=["total_point"])

    # 正常レスポンス
    return JsonResponse({
        "success": True,
        "total_point": animal.total_point,
        "cheer_coin_balance": wallet.cheer_coin_balance,
        "stanning_point_balance": wallet.stanning_point_balance,
    })

