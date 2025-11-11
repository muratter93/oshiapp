from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("animals/", include("animals.urls")),
    path("ranking/", include("ranking.urls")),
    path("pages/", include("pages.urls")),
    path("money/", include("money.urls")),
    path('goods/', include('goods.urls')),
    path("subscription/", include("subscription.urls")),
    path('dashboard/', include('dashboard.urls')),  # 寄付ページ
    path('donation/', include('donation.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)