# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    username 引数に渡された値をまず username として探し、
    見つからなければ email として探して認証するバックエンド。
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        # まず username で試す
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            user = None

        # username で見つからなければ email で探す
        if user is None:
            try:
                user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                return None

        # パスワード確認
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
