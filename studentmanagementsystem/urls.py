from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', RedirectView.as_view(pattern_name='super_admin_dashboard', permanent=False)),
    re_path(r'^admin/.*$', RedirectView.as_view(pattern_name='super_admin_dashboard', permanent=False)),
    path('', include('students.urls')),
    # REST API v1 — JWT-authenticated endpoints for mobile app / integrations
    path('api/v1/', include('students.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = 'students.views.error_400'
handler403 = 'students.views.error_403'
handler404 = 'students.views.error_404'
handler500 = 'students.views.error_500'
