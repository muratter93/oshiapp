from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, get_user_model, logout as auth_logout
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .forms import MemberUpdateForm
from django.views import View
from datetime import date
from django.http import JsonResponse
import requests


def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("accounts:login_success")  # ← ここを変更！
        else:
            messages.error(request, "メールアドレス／IDまたはパスワードが間違っています。")
    return render(request, "accounts/login.html")


# ← この関数を追加！
def login_success(request):
    return render(request, "accounts/login_success.html")


Member = get_user_model()

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        name = request.POST.get("name")
        postal_code = request.POST.get("postal_code")
        address = request.POST.get("address")
        phone = request.POST.get("phone")

        if password != password_confirm:
            messages.error(request, "パスワードが一致しません。")
            return redirect("accounts:signup")

        if Member.objects.filter(username=username).exists():
            messages.error(request, "このユーザーIDはすでに登録されています。")
            return redirect("accounts:signup")

        if Member.objects.filter(email=email).exists():
            messages.error(request, "このメールアドレスはすでに登録されています。")
            return redirect("accounts:signup")

        user = Member.objects.create_user(
            username=username,
            email=email,
            password=password,
            name=name,
            postal_code=postal_code,
            address=address,
            phone=phone
        )
        user.save()

        messages.success(request, "登録が完了しました。ログインしてください。")
        return redirect("accounts:login")

    return render(request, "accounts/signup.html")

def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
        return redirect("accounts:logout_success")
    
    return render(request, "accounts/logout.html")

def logout_success_view(request):
    return render(request, "accounts/logout_success.html")

class MyPageView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/mypage.html'

class MemberEditView(View):
    def get(self, request):
        form = MemberUpdateForm(instance=request.user)
        return render(request, 'accounts/edit_profile.html', {'form': form})

    def post(self, request):
        form = MemberUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            data = form.cleaned_data.copy()

            # 🔽 ここで date型を文字列に変換
            for key, value in data.items():
                if isinstance(value, date):
                    data[key] = value.strftime('%Y-%m-%d')

            # 確認画面に渡すためセッションに保存
            request.session['edit_data'] = data

            return redirect('accounts:edit_profile_confirm')
        return render(request, 'accounts/edit_profile.html', {'form': form})

class MemberEditConfirmView(View):
    def get(self, request):
        data = request.session.get('edit_data')
        if not data:
            return redirect('accounts:edit_profile')  # 修正
        return render(request, 'accounts/edit_profile_confirm.html', {'data': data})

    def post(self, request):
        data = request.session.get('edit_data')
        if not data:
            return redirect('accounts:edit_profile')  # 修正

        form = MemberUpdateForm(data, instance=request.user)
        if form.is_valid():
            form.save()
            request.session.pop('edit_data')
            return redirect('accounts:mypage')  # 保存後の遷移先
        return redirect('accounts:edit_profile')  # 修正

def ajax_get_address(request):
    # ハイフンなしの郵便番号だけを取得
    postal_code = request.GET.get('postal_code', '').strip()
    
    if not postal_code.isdigit() or len(postal_code) != 7:
        return JsonResponse({'address': None})
    
    # zipcloud API にリクエスト
    url = f"http://zipcloud.ibsnet.co.jp/api/search?zipcode={postal_code}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        result = res.json()
        
        if result['results']:
            # 住所を結合して返す
            addr_data = result['results'][0]
            address = f"{addr_data['address1']}{addr_data['address2']}{addr_data['address3']}"
            return JsonResponse({'address': address})
        else:
            return JsonResponse({'address': ''})
    except Exception:
        return JsonResponse({'address': ''})
