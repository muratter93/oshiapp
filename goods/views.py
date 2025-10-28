# goods
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Goods, CartItem
# error
from django.contrib import messages
from money.models import Wallet

from .models import Goods, CartItem, Order, OrderItem # 注文履歴モデル
from django.urls import reverse


# グッズ一覧ページ
@login_required
def goods_list(request):
    print("goods_list ビューが呼ばれました")  # 追加
    goods_list = Goods.objects.all()
    # カート
    cart_items = CartItem.objects.filter(member=request.user)
    total_quantity = sum(item.quantity for item in cart_items)
    total_stanning = sum(item.get_required_stanning_points() for item in cart_items)

    return render(request, 'goods/goods_list.html', {
        'goods_list': goods_list,
        'cart_items': cart_items,
        'total_quantity': total_quantity,
        'total_stanning': total_stanning,
    })


# グッズをカートに追加
@login_required
def add_to_cart(request, goods_id):
    goods = get_object_or_404(Goods, id=goods_id)

    # 同じ商品がすでにカートにある場合は数量を増やす
    cart_item, created = CartItem.objects.get_or_create(
        member=request.user,
        goods=goods,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # カート
    return redirect('goods:goods_list')

# カートに入ったアイテムの数量を増やす
@login_required
def cart_item_increase(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, member=request.user)
    item.quantity += 1
    item.save()
    return redirect('goods:cart_view')


# カートに入ったアイテムの数量を減らす
@login_required
def cart_item_decrease(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, member=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()  # 1以下になったら削除
    return redirect('goods:cart_view')

# カートから削除
@login_required
def cart_item_remove(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, member=request.user)
    item.delete()
    return redirect('goods:cart_view')


# 確定ボタン（住所確認ページへ）
@login_required
def checkout(request):
    return render(request, 'goods/checkout.html')


# カート確認ページ
@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(member=request.user)
    total_stanning = sum([item.get_required_stanning_points() for item in cart_items])

    return render(request, 'goods/cart.html', {
        'cart_items': cart_items,
        'total_stanning': total_stanning
    })


# error
@login_required
def checkout(request):
    member = request.user
    cart_items = CartItem.objects.filter(member=member)
    total_stanning = sum(item.get_required_stanning_points() for item in cart_items)

    # ウォレットのスタポ残高取得
    wallet = Wallet.objects.get(member=member)

    # スタポ不足
    if total_stanning > wallet.stanning_point_balance:
        messages.error(request, "スタポが足りません！")
        return redirect('goods:cart_view')

    # 足りている場合は住所確認ページへ
    return render(request, 'goods/checkout.html', {
        'member': member,
        'cart_items': cart_items,
        'total_stanning': total_stanning,
        'wallet': wallet,
    })


# 完了ページ
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
    else:  # 新規入力
        recipient_name = request.POST.get('new_name')
        postal_code = request.POST.get('new_postal_code')
        address = request.POST.get('new_address')
        phone_number = request.POST.get('new_phone')

    # 注文登録
    order = Order.objects.create(
        member=member,
        total_stanning_points=total_stanning,
        recipient_name=recipient_name,
        postal_code=postal_code,
        address=address,
        phone_number=phone_number
    )

    # 注文アイテム登録＆在庫減少
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




# 詳細ページ
from django.shortcuts import render, get_object_or_404
from .models import Goods

def goods_detail(request, goods_id):
    goods = get_object_or_404(Goods, pk=goods_id)
    return render(request, 'goods/goods_detail.html', {'goods': goods})
