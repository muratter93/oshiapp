from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from subscription.service import grant_plan_points_to_wallet
from subscription.models import SubscribePlan

@login_required
def purchase_done(request, code: str):
    """
    購入完了想定の超シンプルなビュー。
    /subscription/buy/<code>/done/ を叩くと、スタポを付与してサンクスを返す。
    """
    plan = get_object_or_404(SubscribePlan, code=code)
    new_balance = grant_plan_points_to_wallet(request.user, plan.code)
    return HttpResponse(f"{plan.code} を付与しました。残高: {new_balance}")