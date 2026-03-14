from django.contrib import admin
from django.urls import path
from gestion_social.views import dashboard_social

admin.site.site_header = "Demo de Actuarial Cortex"
admin.site.site_title = "Demo de Actuarial Cortex"
admin.site.index_title = "Gestión Social"
admin.site.index_template = "admin/cortex_index.html"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard_social, name='dashboard'),
]
