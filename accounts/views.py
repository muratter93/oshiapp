from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect


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