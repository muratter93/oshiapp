from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db import connection
from goods.models import Goods, GoodsImage, Order, OrderItem, CartItem

# 管理者のみアクセス可能
@user_passes_test(lambda u: u.is_staff)
def admin_reset(request):
    if request.method == "POST":
        # --- データ削除 ---
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartItem.objects.all().delete()
        GoodsImage.objects.all().delete()
        Goods.objects.all().delete()

        # --- IDリセット（SQLite用）---
        cursor = connection.cursor()
        for table in [
            'goods_goods',
            'goods_goodsimage',
            'goods_order',
            'goods_orderitem',
            'goods_cartitem',
        ]:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        cursor.close()

        # --- 完了メッセージ ---
        messages.success(request, "✅ 全データを削除し、IDをリセットしました。")
        return redirect("goods:admin_reset")

    # --- 確認画面表示 ---
    return render(request, "goods/admin_reset.html")
