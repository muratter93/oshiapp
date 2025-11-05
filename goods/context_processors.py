# かご表示
from goods.models import CartItem

def cart_total_quantity(request):
    total_quantity = 0
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(member=request.user)
        total_quantity = sum(item.quantity for item in cart_items)
    else:
        # セッションカートなどを使ってる場合はここに処理を追加
        cart = request.session.get('cart', {})
        total_quantity = sum(cart.values())
    return {'total_quantity': total_quantity}


from goods.models import Goods

def all_goods(request):
    goods_list = Goods.objects.all()
    return {'goods_list': goods_list}
