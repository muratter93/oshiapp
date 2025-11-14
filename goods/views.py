# goods/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator

from .models import Goods, CartItem, Order, OrderItem
from money.models import Wallet

# ===============================
# グッズ一覧ページ
# ===============================

def goods_list(request):
    goods_list = Goods.objects.all()

    cart_items = []
    total_quantity = 0
    total_stanning = 0

    #  ログインしている時だけカート情報を取得
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(member=request.user)
        total_quantity = sum(item.quantity for item in cart_items)
        total_stanning = sum(item.get_required_stanning_points() for item in cart_items)

    return render(request, 'goods/goods_list.html', {
        'goods_list': goods_list,
        'cart_items': cart_items,
        'total_quantity': total_quantity,
        'total_stanning': total_stanning,
    })



# ===============================
# カート関連
# ===============================
@login_required
def add_to_cart(request, goods_id):
    goods = get_object_or_404(Goods, id=goods_id)
    cart_item, created = CartItem.objects.get_or_create(
        member=request.user,
        goods=goods,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('goods:goods_list')


@login_required
def cart_item_increase(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, member=request.user)
    item.quantity += 1
    item.save()
    return redirect('goods:cart_view')


@login_required
def cart_item_decrease(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, member=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect('goods:cart_view')


@login_required
def cart_item_remove(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, member=request.user)
    item.delete()
    return redirect('goods:cart_view')


@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(member=request.user)
    total_stanning = sum(item.get_required_stanning_points() for item in cart_items)
    return render(request, 'goods/cart.html', {
        'cart_items': cart_items,
        'total_stanning': total_stanning
    })


# ===============================
# 注文処理
# ===============================
@login_required
def checkout(request):  # ← 修正版（重複削除済み）
    member = request.user
    cart_items = CartItem.objects.filter(member=member)
    total_stanning = sum(item.get_required_stanning_points() for item in cart_items)
    wallet = Wallet.objects.get(member=member)

    # スタポ不足チェック
    if total_stanning > wallet.stanning_point_balance:
        messages.error(request, "スタポが足りません！")
        return redirect('goods:cart_view')

    return render(request, 'goods/checkout.html', {
        'member': member,
        'cart_items': cart_items,
        'total_stanning': total_stanning,
        'wallet': wallet,
    })


@login_required
def confirm_exchange(request):
    if request.method != 'POST':
        return redirect('goods:checkout')

    member = request.user
    cart_items = CartItem.objects.filter(member=member)
    total_stanning = sum(item.get_required_stanning_points() for item in cart_items)
    wallet = member.wallet

    # スタポ不足
    if wallet.stanning_point_balance < total_stanning:
        messages.error(request, "スタポが足りません！")
        return redirect('goods:cart_view')

    # 在庫チェック
    for item in cart_items:
        if item.goods.stock < item.quantity:
            messages.error(request, f"{item.goods.name}の在庫が足りません")
            return redirect('goods:cart_view')

    # ウォレット更新
    wallet.stanning_point_balance -= total_stanning
    wallet.save()

    # 住所情報取得
    address_option = request.POST.get('address_option')
    if address_option == "registered":
        recipient_name = member.name
        postal_code = member.postal_code
        address = member.address
        phone_number = member.phone
    else:
        recipient_name = request.POST.get('new_name')
        postal_code = request.POST.get('new_postal_code')
        address = request.POST.get('new_address')
        phone_number = request.POST.get('new_phone')

    # 注文作成
    order = Order.objects.create(
        member=member,
        total_stanning_points=total_stanning,
        recipient_name=recipient_name,
        postal_code=postal_code,
        address=address,
        phone_number=phone_number
    )

    # 注文アイテム登録 & 在庫減少
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            goods=item.goods,
            quantity=item.quantity
        )
        item.goods.stock -= item.quantity
        item.goods.save()

    # カート空にする
    cart_items.delete()

    return render(request, 'goods/exchange_complete.html', {
        'total_stanning': total_stanning,
        'order': order
    })


# ===============================
# 詳細・履歴
# ===============================
@login_required
def goods_detail(request, goods_id):
    goods = get_object_or_404(Goods, pk=goods_id)
    return render(request, 'goods/goods_detail.html', {'goods': goods})


@login_required
def order_history(request):
    """ユーザー自身のグッズ交換履歴ページ"""
    orders = Order.objects.filter(member=request.user).order_by('-created_at')
    order_items = OrderItem.objects.filter(order__in=orders).select_related('goods', 'order').order_by('-order__created_at')

    paginator = Paginator(order_items, 20)  # 1ページ20件
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'goods/order_history.html', {
        'page_obj': page_obj,
    })
