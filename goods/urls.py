from django.urls import path
from . import views
from . import views_admin

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
    path('admin/add/', views_admin.goods_admin_add, name='goods_admin_add'),  # ← 管理者グッズ追加
    path('history/', views.order_history, name='order_history'), # ← 交換履歴追加
    path('admin/list/', views_admin.goods_admin_list, name='goods_admin_list'),  # ← 管理者グッズ一覧
    path('admin/edit/<int:goods_id>/', views_admin.goods_admin_edit, name='goods_admin_edit'),  # ← グッズ編集
    path('admin/delete/<int:goods_id>/', views_admin.goods_admin_delete, name='goods_admin_delete'), # ← グッズ削除

    path('admin/orders/', views_admin.admin_order_list, name='admin_order_list'), # ← 注文一覧
    path('admin/orders/<int:order_id>/', views_admin.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<int:order_id>/ship/', views_admin.admin_order_ship, name='admin_order_ship'),
    path('admin/orders/<int:order_id>/toggle/', views_admin.toggle_shipping_status, name='toggle_shipping_status'),
]   

