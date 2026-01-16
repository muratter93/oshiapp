# かご表示
from goods.models import CartItem

def cart_total_quantity(request):
    cart = request.session.get('cart', {})
    total_quantity = sum(cart.values())
    return {'total_quantity': total_quantity}


from goods.models import Goods

def all_goods(request):
    goods_list = Goods.objects.all()
    return {'goods_list': goods_list}
