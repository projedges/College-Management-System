from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('students.urls')),
    # REST API v1 — JWT-authenticated endpoints for mobile app / integrations
    path('api/v1/', include('students.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'students.views.error_400'
handler403 = 'students.views.error_403'
handler404 = 'students.views.error_404'
handler500 = 'students.views.error_500'
