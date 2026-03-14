from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from gestion_social.views import dashboard_social
from config.views_health import health

admin.site.site_header = "Demo de Actuarial Cortex"
admin.site.site_title = "Demo de Actuarial Cortex"
admin.site.index_title = "Gestión Social"
admin.site.index_template = "admin/cortex_index.html"

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='root'),
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard_social, name='dashboard'),
]
