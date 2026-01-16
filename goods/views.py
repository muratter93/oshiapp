from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator

from .models import Goods, CartItem, Order, OrderItem
from money.models import Wallet

# ===================================
# グッズ一覧ページ
# ===================================
def goods_list(request):
    goods_list = Goods.objects.all()
    cart_items = []
    total_stanning = 0

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(member=request.user)
        total_stanning = sum(item.get_required_stanning_points() for item in cart_items)
    else:
        session_cart = request.session.get("cart", {})
        goods_dict = Goods.objects.filter(id__in=session_cart.keys())
        cart_items_dict = {}
        cart_items_list = []

        for g in goods_dict:
            qty = session_cart.get(str(g.id), 0)
            cart_items_dict[str(g.id)] = {
                "name": g.name,
                "required_stanning_points": g.required_stanning_points,
                "quantity": qty
            }
            total_stanning += g.required_stanning_points * qty

        cart_items = cart_items_dict

    return render(request, 'goods/goods_list.html', {
        "goods_list": goods_list,
        "cart_items": cart_items,
        "total_stanning": total_stanning
    })


# ===================================
# カート追加
# ===================================
def add_to_cart(request, goods_id):
    cart = request.session.get('cart', {})

    # 数量を1追加（既にある場合は加算）
    cart[str(goods_id)] = cart.get(str(goods_id), 0) + 1

    request.session['cart'] = cart  # セッションに保存
    request.session.modified = True

    return redirect(request.META.get('HTTP_REFERER', 'goods:goods_list'))



# ===================================
# カート操作
# ===================================
def cart_item_increase(request, goods_id):
    cart = request.session.get("cart", {})
    cart[str(goods_id)] = cart.get(str(goods_id), 0) + 1
    request.session["cart"] = cart
    request.session.modified = True
    return redirect('goods:cart_view')



def cart_item_decrease(request, goods_id):
    cart = request.session.get("cart", {})
    if str(goods_id) in cart:
        if cart[str(goods_id)] > 1:
            cart[str(goods_id)] -= 1
        else:
            del cart[str(goods_id)]
        request.session["cart"] = cart
        request.session.modified = True
    return redirect('goods:cart_view')



def cart_item_remove(request, goods_id):
    cart = request.session.get("cart", {})
    cart.pop(str(goods_id), None)
    request.session["cart"] = cart
    request.session.modified = True
    return redirect('goods:cart_view')



# ===================================
# カート表示
# ===================================
def cart_view(request):
    # セッションのカートを取得
    cart = request.session.get('cart', {})

    items = {}
    total_stanning = 0

    for goods_id, quantity in cart.items():
        goods = Goods.objects.get(id=goods_id)
        subtotal = goods.required_stanning_points * quantity
        items[goods_id] = {
            "goods": goods,
            "quantity": quantity,
            "subtotal": subtotal
        }
        total_stanning += subtotal

    return render(request, "goods/cart.html", {
        "cart_items": items,
        "total_stanning": total_stanning,
    })







# ===============================
# 注文処理
# ===============================
@login_required
def checkout(request):
    cart = request.session.get("cart", {})
    goods_dict = Goods.objects.filter(id__in=cart.keys())

    cart_items = []
    total_stanning = 0

    for g in goods_dict:
        qty = cart.get(str(g.id), 0)
        cart_items.append({
            "goods": g,
            "quantity": qty,
            "subtotal": g.required_stanning_points * qty
        })
        total_stanning += g.required_stanning_points * qty

    wallet = request.user.wallet

    if total_stanning > wallet.stanning_point_balance:
        messages.error(request, "スタポが足りません！")
        return redirect('goods:cart_view')

    return render(request, 'goods/checkout.html', {
        "cart_items": cart_items,
        "total_stanning": total_stanning,
        "wallet": wallet
    })



@login_required
def confirm_exchange(request):
    if request.method != 'POST':
        return redirect('goods:checkout')

    cart = request.session.get("cart", {})
    goods_dict = Goods.objects.filter(id__in=cart.keys())

    # 名前、住所などの取得
    member = request.user
    wallet = member.wallet

    total_stanning = 0
    items_for_order = []

    for g in goods_dict:
        qty = cart.get(str(g.id), 0)
        if qty > 0:
            required = g.required_stanning_points * qty
            items_for_order.append((g, qty, required))
            total_stanning += required

    # ポイント足りないとき
    if wallet.stanning_point_balance < total_stanning:
        messages.error(request, "スタポが足りません！")
        return redirect('goods:cart_view')

    # 在庫チェック
    for g, qty, _ in items_for_order:
        if g.stock < qty:
            messages.error(request, f"{g.name} の在庫が足りません")
            return redirect('goods:cart_view')

    # ウォレット更新
    wallet.stanning_point_balance -= total_stanning
    wallet.save()

    # 宛先情報
    if request.POST.get('address_option') == "registered":
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

    # 注文アイテム
    for g, qty, required in items_for_order:
        OrderItem.objects.create(order=order, goods=g, quantity=qty)
        g.stock -= qty
        g.save()

    # セッションカート初期化
    request.session["cart"] = {}
    request.session.modified = True

    return render(request, 'goods/exchange_complete.html', {
        'order': order,
        'total_stanning': total_stanning
    })



# ===============================
# 詳細・履歴
# # ===============================
# @login_required
def goods_detail(request, goods_id):
    goods = get_object_or_404(Goods, pk=goods_id)
    return render(request, 'goods/goods_detail.html', {'goods': goods})
 
 
@login_required
@login_required
def order_history(request):
    """ユーザー自身のグッズ交換履歴ページ"""
    orders = Order.objects.filter(member=request.user).order_by('-created_at')

    return render(request, 'goods/order_history.html', {
        "orders": orders
    })
