from django import template

register = template.Library()

@register.filter
def phone_format(value):
    """電話番号をハイフン付きに整形"""
    if not value:
        return ''
    value = str(value)
    # 携帯 or 固定電話を自動判別
    if len(value) == 10:
        return f"{value[:2]}-{value[2:6]}-{value[6:]}"
    elif len(value) == 11:
        return f"{value[:3]}-{value[3:7]}-{value[7:]}"
    else:
        return value  # 不明な形式はそのまま


@register.filter
def postal_format(value):
    """郵便番号をハイフン付きにフォーマットする（例: 1234567 → 123-4567）"""
    if not value:
        return ''
    value = str(value).replace('-', '').strip()
    if len(value) == 7 and value.isdigit():
        return f"{value[:3]}-{value[3:]}"
    return value