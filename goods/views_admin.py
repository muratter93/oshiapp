from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import GoodsForm, GoodsImageForm
from .models import Goods, GoodsImage

from django.contrib.admin.views.decorators import staff_member_required
from .models import Order

# --- 管理者チェック関数 ---
def is_admin(user):
    return user.is_authenticated and user.is_staff  # ← スタッフ権限持ちユーザーだけOK

# --- 管理者用グッズ登録ページ ---
@login_required
@user_passes_test(is_admin)
def goods_admin_add(request):
    """管理者がグッズを追加するページ"""
    if request.method == 'POST':
        form = GoodsForm(request.POST, request.FILES)
        images = request.FILES.getlist('detail_images')  # ← input name="detail_images" の複数ファイル取得
        
        if form.is_valid():
            goods = form.save()  # まずメインのグッズを保存
            
            # 詳細画像がある場合は、GoodsImage に保存
            for img in images:
                GoodsImage.objects.create(goods=goods, image=img)
            
            messages.success(request, "新しいグッズを登録しました！")
            return redirect('goods:goods_admin_add')
        else:
            messages.error(request, "入力内容にエラーがあります。")
    else:
        form = GoodsForm()

    return render(request, 'goods/goods_admin_add.html', {'form': form})


# 管理者チェック関数（is_staff または superuser）
def admin_check(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(admin_check)
def goods_admin_list(request):
    """グッズ一覧を管理者用に表示"""
    goods_list = Goods.objects.all().order_by('-id')
    return render(request, 'goods/admin_goods_list.html', {'goods_list': goods_list})


@user_passes_test(admin_check)
def goods_admin_edit(request, goods_id):
    """指定グッズを編集"""
    goods = get_object_or_404(Goods, id=goods_id)

    if request.method == 'POST':
        form = GoodsForm(request.POST, request.FILES, instance=goods)
        if form.is_valid():
            form.save()

            # 新しい詳細画像の追加処理
            images = request.FILES.getlist('detail_images')
            for img in images:
                GoodsImage.objects.create(goods=goods, image=img)

            messages.success(request, "グッズ情報を更新しました！")
            return redirect('goods:goods_admin_list')
        else:
            messages.error(request, "入力内容にエラーがあります。")
    else:
        form = GoodsForm(instance=goods)

    return render(request, 'goods/admin_goods_edit.html', {
        'form': form,
        'goods': goods
    })


# 削除
@user_passes_test(admin_check)
def goods_admin_delete(request, goods_id):
    """グッズ削除（確認付き）"""
    goods = get_object_or_404(Goods, id=goods_id)

    if request.method == "POST":
        goods.delete()
        return redirect('goods:goods_admin_list')

    return render(request, 'goods/admin_goods_delete_confirm.html', {'goods': goods})

# 注文一覧
@staff_member_required
def admin_order_list(request):
    orders = Order.objects.prefetch_related('items__goods').order_by('-created_at')
    return render(request, 'goods/admin_order_list.html', {'orders': orders})


@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__goods'), id=order_id)
    return render(request, 'goods/admin_order_detail.html', {'order': order})


@staff_member_required
def admin_order_ship(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'shipped'
    order.save()
    return redirect('goods:admin_order_list')

# 発送状態を切り替えるビュー
@staff_member_required
def toggle_shipping_status(request, order_id):
    """発送状態を「未発送⇄発送済み」に切り替える"""
    order = get_object_or_404(Order, id=order_id)

    # 状態をトグル（切り替え）
    if order.status == 'pending':
        order.status = 'shipped'
        messages.success(request, f"注文ID {order.id} を『発送済み』に変更しました。")
    else:
        order.status = 'pending'
        messages.info(request, f"注文ID {order.id} を『未発送』に戻しました。")

    order.save()
    return redirect('goods:admin_order_list')

# 詳細画像削除
@user_passes_test(admin_check)
def delete_detail_image(request, image_id):
    """詳細画像を削除"""
    image = get_object_or_404(GoodsImage, id=image_id)
    goods_id = image.goods.id

    if request.method == "POST":
        image.delete()
        messages.success(request, "詳細画像を削除しました。")
        return redirect('goods:goods_admin_edit', goods_id=goods_id)

    # 確認ページを挟む場合（不要ならこのブロック削除）
    return render(request, 'goods/delete_detail_image_confirm.html', {'image': image})