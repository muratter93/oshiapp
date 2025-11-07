from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order

@login_required
def order_history(request):
    """ログイン中会員の注文履歴"""
    orders = (
        Order.objects.filter(member=request.user)
        .prefetch_related('items__goods')
        .order_by('-created_at')
    )
    return render(request, 'goods/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """注文の詳細ページ（住所など表示）"""
    order = get_object_or_404(Order, id=order_id, member=request.user)
    return render(request, 'goods/order_detail.html', {'order': order})


@login_required
def cancel_order(request, order_id):
    """注文のキャンセル処理"""
    order = get_object_or_404(Order, id=order_id, member=request.user)

    if order.status == 'pending':
        # 1️⃣ 在庫を元に戻す
        for item in order.items.all():
            item.goods.stock += item.quantity
            item.goods.save()

        # 2️⃣ スターポイントを返却（Wallet 経由）
        wallet = getattr(request.user, "wallet", None)
        if wallet:
            wallet.stanning_point_balance += order.total_stanning_points
            wallet.save()
        else:
            messages.error(request, "ウォレット情報が見つかりませんでした。ポイントの返却に失敗しました。")

        # 3️⃣ 注文ステータスをキャンセルに変更
        order.status = 'cancelled'
        order.save()

        messages.success(request, "注文をキャンセルしました。スターポイントを返却しました。")

    else:
        messages.warning(request, "発送済みまたはキャンセル済みの注文はキャンセルできません。")

    return redirect('goods:order_history')

