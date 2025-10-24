from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Member

class MemberSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Member
        fields = [
            'username',      # ID
            'name',          # 名前
            'email',         # メール
            'postal_code',   # 郵便番号
            'address',       # 住所
            'phone',         # 電話番号
            'password1',     # パスワード
            'password2',     # パスワード確認
        ]
