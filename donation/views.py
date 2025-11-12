from django.shortcuts import render, redirect, get_object_or_404 
from animals.models import Zoo
from django.contrib.auth.decorators import login_required
from django.utils import timezone

# -----------------------------
# 寄付フォームページ
# -----------------------------
@login_required
def donate(request):
    zoos = Zoo.objects.all()

    if request.method == "POST":
        zoo_id = request.POST.get("zoo")
        amount = request.POST.get("amount")
        if not zoo_id or not amount:
            return render(request, "donation/donate.html", {
                "zoos": zoos,
                "error": "動物園と寄付額を選択してください"
            })
        # 一時的にセッションに保存して確認ページへ
        request.session["donation_data"] = {
            "zoo_id": zoo_id,
            "amount": amount
        }
        return redirect("donation:donate_confirm")

    return render(request, "donation/donate.html", {"zoos": zoos})


# -----------------------------
# 確認ページ
# -----------------------------
@login_required
def donate_confirm(request):
    data = request.session.get("donation_data")
    if not data:
        return redirect("donation:donate")

    zoo = get_object_or_404(Zoo, pk=data["zoo_id"])
    amount = int(data["amount"])

    if request.method == "POST":
        # 固定メッセージ
        default_message = "上記のとおり、寄附金を受領いたしました。ここに感謝の意を表します。"

        # 寄付を登録
        donation = Donation.objects.create(
            donor=request.user,
            zoo=zoo,
            amount=amount,
            address=request.user.address,  # 会員モデルの住所を使う
            message=default_message         # ← ここを追加！
        )

        # 確認用にセッション削除
        del request.session["donation_data"]
        return redirect("donation:donate_complete", donation_id=donation.donation_id)

    return render(request, "donation/donate_confirm.html", {
        "zoo": zoo,
        "amount": amount
    })



# -----------------------------
# 完了ページ
# -----------------------------
@login_required
def donate_complete(request, donation_id):
    donation = get_object_or_404(Donation, pk=donation_id)
    return render(request, "donation/donate_complete.html", {
        "donation": donation
    })



import os
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.contrib.auth.decorators import login_required
from .models import Donation
from django.conf import settings

from .models import Stamp

@login_required
def donation_receipt_pdf(request, donation_id):
    donation = get_object_or_404(Donation, pk=donation_id)

    # 寄付者本人しか見れないように制限
    if donation.donor != request.user:
        return HttpResponse("権限がありません", status=403)

    # PDFレスポンスを作成
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="donation_receipt_{donation_id}.pdf"'

    # PDFキャンバス作成
    p = canvas.Canvas(response)

    # 日本語フォント登録
    font_path = os.path.join(settings.BASE_DIR, "static/fonts/ipaexg.ttf")
    pdfmetrics.registerFont(TTFont('IPAexGothic', font_path))
    p.setFont("IPAexGothic", 16)

    # タイトル
    p.drawCentredString(300, 800, "寄附金受領証明書")

    # 内容
    y = 750
    line_height = 25
    p.setFont("IPAexGothic", 12)
    p.drawString(50, y, f"寄付者名: {donation.donor.name}")
    y -= line_height
    p.drawString(50, y, f"寄付者住所: {donation.address}")
    y -= line_height
    p.drawString(50, y, f"寄付先動物園: {donation.zoo.zoo_name}")
    y -= line_height
    p.drawString(50, y, f"寄付金額: {donation.amount:,}円")
    y -= line_height
    p.drawString(50, y, f"寄付日: {donation.created_at.strftime('%Y年%m月%d日')}")
    y -= line_height
    message = donation.message or "-"
    p.drawString(50, y, f"備考: {message}")

    #  動物園ごとの有効ハンコを取得して描画
    stamp = Stamp.objects.filter(zoo=donation.zoo, is_active=True).first()
    if stamp and stamp.image:
        p.drawImage(stamp.image.path, 420, 100, width=100, height=100, mask='auto')

    # フッター
    p.drawRightString(550, 50, "動物園支援サイト")
    p.drawRightString(550, 30, donation.created_at.strftime("%Y年%m月%d日"))

    p.showPage()
    p.save()

    return response




#　寄付履歴ページ
from django.shortcuts import render
from .models import Donation
from django.contrib.auth.decorators import login_required

@login_required
def donation_history(request):
    # ログインユーザーの寄付履歴
    donations = Donation.objects.filter(donor=request.user).order_by('-created_at')
    return render(request, 'donation/donation_history.html', {
        'donations': donations
    })