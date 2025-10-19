def app_name(request):
    """
    どのテンプレートからも使える共通変数を返す
    """
    return {
        "APP_NAME": "推し活アプリ",
    }

def navbar(request):
    """
    すべてのテンプレートで使えるナビ情報を返す。
    返り値は dict（キーがテンプレ変数名）である必要があります。
    """
    return {
        "NAV_ITEMS": [
            {"label": "Home",    "href": "/"},
            {"label": "Animals", "href": "/animals/"},
            {"label": "Ranking", "href": "/ranking/"},
            {"label": "Wallet",  "href": "/money/"},
            {"label": "Pages",   "href": "/pages/"},
            {"label": "Accounts","href": "/accounts/"},
        ]
    }
