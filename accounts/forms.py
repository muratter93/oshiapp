from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm  # ← ここに追加
from .models import Member
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

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

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not Member.objects.filter(email=email).exists():
            raise ValidationError("このメールアドレスは登録されていません。")
        return email

class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': '新しいパスワード',
            'required': 'required',
            'pattern': '(?=.*[0-9])(?=.*[a-zA-Z])(?=.*[!@#$%^&*]).{8,}',
            'title': '英字・数字・記号を含む8文字以上で入力してください'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'パスワード（確認）',
            'required': 'required'
        })