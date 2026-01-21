from django.urls import path
from . import views
from . import views_admin       # 管理者用
from . import views_user        # 会員用
from . import views_admin_reset # 管理者：全初期化用

app_name = 'goods'

urlpatterns = [

    # ====== 一般ユーザー向け ======
    path('goods_list/', views.goods_list, name='goods_list'),

    # カート
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:goods_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/increase/<int:goods_id>/', views.cart_item_increase, name='cart_item_increase'),
    path('cart/decrease/<int:goods_id>/', views.cart_item_decrease, name='cart_item_decrease'),
    path('cart/remove/<int:goods_id>/', views.cart_item_remove, name='cart_item_remove'),

    # 購入処理
    path('checkout/', views.checkout, name='checkout'),
    path('confirm/', views.confirm_exchange, name='confirm_exchange'),

    # グッズ詳細
    path('detail/<int:goods_id>/', views.goods_detail, name='goods_detail'),

    # 交換履歴（会員）
    path('history/', views.order_history, name='order_history'),


    # ====== 管理者向け：グッズ管理 ======
    path('admin/list/', views_admin.goods_admin_list, name='goods_admin_list'),
    path('admin/add/', views_admin.goods_admin_add, name='goods_admin_add'),
    path('admin/edit/<int:goods_id>/', views_admin.goods_admin_edit, name='goods_admin_edit'),
    path('admin/delete/<int:goods_id>/', views_admin.goods_admin_delete, name='goods_admin_delete'),
    path('admin/goods/image/<int:image_id>/delete/', views_admin.delete_detail_image, name='delete_detail_image'),


    # ====== 管理者向け：注文管理 ======
    path('admin/orders/', views_admin.admin_order_list, name='admin_order_list'),
    path('admin/orders/<int:order_id>/', views_admin.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<int:order_id>/ship/', views_admin.admin_order_ship, name='admin_order_ship'),
    path('admin/orders/<int:order_id>/toggle/', views_admin.toggle_shipping_status, name='toggle_shipping_status'),


    # ====== 会員向け：注文詳細・キャンセル ======
    path('orders/', views_user.order_history, name='order_history_user'),
    path('orders/<int:order_id>/', views_user.order_detail, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views_user.cancel_order, name='cancel_order'),


    # ====== 管理者向け：全初期化（バルス） ======
    path('admin_reset/', views_admin_reset.admin_reset, name='admin_reset'),

]
