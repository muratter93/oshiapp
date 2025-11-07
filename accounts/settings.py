import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# デバッグ用
print(f"BASE_DIR: {BASE_DIR}")
print(f"STATIC path exists: {os.path.exists(BASE_DIR / 'static')}")
print(f"CSS file exists: {os.path.exists(BASE_DIR / 'static' / 'css' / 'style.css')}")

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

AUTH_USER_MODEL = "accounts.Member"
# settings.py の適切な場所に追加
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',  # 先にカスタムバックエンド
    'django.contrib.auth.backends.ModelBackend', # フォールバック（標準）
]
