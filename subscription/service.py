from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings

from money.models import Wallet
from .models import SubscribePlan

def grant_plan_points_to_wallet(user: settings.AUTH_USER_MODEL, plan_code: str) -> int:
    """
    指定ユーザーの Wallet に、そのプランのスタポを加算して新残高を返す。
    """
    plan = get_object_or_404(SubscribePlan, code=plan_code)
    add_point = plan.st_point or 0
    with transaction.atomic():
        wallet, _ = Wallet.objects.select_for_update().get_or_create(member=user)
        if add_point > 0:
            wallet.stanning_point_balance = (wallet.stanning_point_balance or 0) + add_point
            wallet.save(update_fields=["stanning_point_balance"])
        return wallet.stanning_point_balance