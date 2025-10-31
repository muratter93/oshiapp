from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import GoodsForm

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
        if form.is_valid():
            form.save()
            messages.success(request, "新しいグッズを登録しました！")
            return redirect('goods:goods_admin_add')
        else:
            messages.error(request, "入力内容にエラーがあります。")
    else:
        form = GoodsForm()

    return render(request, 'goods/goods_admin_add.html', {'form': form})
