from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
import re

User = get_user_model()

class StaffCreateForm(UserCreationForm):
    email = forms.EmailField(label="メール", required=True)

    name        = forms.CharField(label="名前", max_length=100, required=False)
    birth       = forms.DateField(label="生年月日", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    postal_code = forms.CharField(label="郵便番号", max_length=10, required=False)
    address     = forms.CharField(label="住所", max_length=255, required=False)
    phone       = forms.CharField(label="電話番号", max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "name", "birth", "postal_code", "address", "phone")

    # --- ユーザー名: 英数字＋記号OK（空白のみ禁止） ---
    def clean_username(self):
        username = self.cleaned_data["username"]
        if re.search(r"\s", username):
            raise forms.ValidationError("ユーザー名に空白は使用できません。")
        return username

    # --- パスワード1: 4文字以上、空白禁止 ---
    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if re.search(r"\s", password):
            raise forms.ValidationError("パスワードに空白は使えません。")
        return password

    # --- パスワード2: 同じルール＋一致確認 ---
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if not password2:
            raise forms.ValidationError("確認用パスワードを入力してください。")

        if len(password2) < 4:
            raise forms.ValidationError("パスワードは4文字以上で入力してください。")

        if re.search(r"\s", password2):
            raise forms.ValidationError("パスワードに空白は使えません。")

        if password1 and password1 != password2:
            raise forms.ValidationError("パスワードが一致しません。")

        return password2

    # --- メール: @形式 ---
    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise forms.ValidationError("メールアドレスは有効な形式で入力してください。")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("このメールアドレスは既に使用されています。")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.name = self.cleaned_data.get("name", "")
        user.birth = self.cleaned_data.get("birth")
        user.postal_code = self.cleaned_data.get("postal_code", "")
        user.address = self.cleaned_data.get("address", "")
        user.phone = self.cleaned_data.get("phone", "")
        user.is_superuser = False
        user.is_staff = True
        if commit:
            user.save()
        return user


# dashboard/forms.py
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class StaffEditForm(forms.ModelForm):
    class Meta:
        model = User
        # ここに「編集させたい」カラムだけを列挙
        fields = ("email", "name", "postal_code", "address", "phone", "birth")
        widgets = {
            "birth": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ユーザー名は変更不可 → テンプレで表示だけする or 参考表示
        # もしフォームに見せたい場合は、下のように「disabledなダミーフィールド」を追加してもOK
        # self.fields["username_display"] = forms.CharField(
        #     label="ユーザー名", initial=self.instance.username, disabled=True, required=False
        # )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            return email  # 空メールを許す設計ならこのまま戻す（許さないならバリデーションを入れる）
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("このメールアドレスは既に使用されています。")
        return email

class KeeperEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "name", "postal_code", "address", "phone", "birth", "zoo")
        widgets = {"birth": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zoo"].queryset = Zoo.objects.order_by("zoo_name")

    def clean(self):
        cleaned = super().clean()
        # 飼育員なら zoo 必須（安全側チェック）
        if getattr(self.instance, "is_keeper", False) and not cleaned.get("zoo"):
            self.add_error("zoo", "飼育員の所属動物園を選択してください。")
        return cleaned

# dashboard/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from animals.models import Zoo   # ★ 追加
import re

User = get_user_model()

# ---- 飼育員作成（is_keeper=True, is_staff=False） ----
class KeeperCreateForm(UserCreationForm):
    email = forms.EmailField(label="メール", required=True)
    name        = forms.CharField(label="名前", max_length=100, required=False)
    birth       = forms.DateField(label="生年月日", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    postal_code = forms.CharField(label="郵便番号", max_length=10, required=False)
    address     = forms.CharField(label="住所", max_length=255, required=False)
    phone       = forms.CharField(label="電話番号", max_length=20, required=False)

    # ★ 所属動物園（必須）
    zoo = forms.ModelChoiceField(
        label="所属動物園",
        queryset=Zoo.objects.none(),   # __init__でセット
        required=True,
        empty_label="選択してください",
        help_text="飼育員の所属先を選んでください。",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username", "email", "name", "birth",
            "postal_code", "address", "phone", "zoo"  # ★ zoo を追加
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zoo を名前順で選べるように
        self.fields["zoo"].queryset = Zoo.objects.order_by("zoo_name")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if re.search(r"\s", username):
            raise forms.ValidationError("ユーザー名に空白は使用できません。")
        return username

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if re.search(r"\s", password):
            raise forms.ValidationError("パスワードに空白は使えません。")
        return password

    def clean_password2(self):
        p1, p2 = self.cleaned_data.get("password1"), self.cleaned_data.get("password2")
        if not p2:
            raise forms.ValidationError("確認用パスワードを入力してください。")
        if len(p2) < 4:
            raise forms.ValidationError("パスワードは4文字以上で入力してください。")
        if re.search(r"\s", p2):
            raise forms.ValidationError("パスワードに空白は使えません。")
        if p1 and p1 != p2:
            raise forms.ValidationError("パスワードが一致しません。")
        return p2

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise forms.ValidationError("メールアドレスは有効な形式で入力してください。")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("このメールアドレスは既に使用されています。")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email        = self.cleaned_data["email"]
        user.name         = self.cleaned_data.get("name", "")
        user.birth        = self.cleaned_data.get("birth")
        user.postal_code  = self.cleaned_data.get("postal_code", "")
        user.address      = self.cleaned_data.get("address", "")
        user.phone        = self.cleaned_data.get("phone", "")
        user.zoo          = self.cleaned_data["zoo"]      # ★ 紐づけ
        user.is_superuser = False
        user.is_staff     = False
        user.is_keeper    = True
        if commit:
            user.save()
        return user

from django import forms
from animals.models import Animal, Zoo

class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = [
            "japanese", "name", "zoo", "sex", "birth", "txt", "pic1",
            "diet",
        ]
        widgets = {
            "zoo": forms.Select(),
            "birth": forms.DateInput(attrs={"type": "date"}),
            "txt": forms.Textarea(attrs={"rows": 5}),
            "diet": forms.Select(attrs={"placeholder": "主食を選択"}),
            "is_active": forms.CheckboxInput(),
        }


    def __init__(self, *args, **kwargs):
        # ★ ここで user を安全に取り出す（渡されてなかったら None）
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # zoo プルダウンの基本並び
        self.fields["zoo"].queryset = Zoo.objects.order_by("zoo_name")

        # ★ keeper の場合は、自分の所属動物園を強制・固定
        if user and getattr(user, "is_keeper", False):
            if user.zoo_id:
                self.fields["zoo"].initial = user.zoo
                self.fields["zoo"].disabled = True   # ← 選択不可にする