from django.urls import path
from . import views

app_name = 'goods'

urlpatterns = [
    path('', views.goods_list, name='goods_list'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:goods_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/increase/<int:item_id>/', views.cart_item_increase, name='cart_item_increase'),
    path('cart/decrease/<int:item_id>/', views.cart_item_decrease, name='cart_item_decrease'),
    path('cart/remove/<int:item_id>/', views.cart_item_remove, name='cart_item_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirm/', views.confirm_exchange, name='confirm_exchange'),
    path('detail/<int:goods_id>/', views.goods_detail, name='goods_detail'),  # ← 詳細ページ
]

