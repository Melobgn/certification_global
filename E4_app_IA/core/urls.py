from django.urls import path
from .views import (
    redirect_view,
    annotation_dashboard,
    admin_dashboard,
    soumettre_annotation
)

urlpatterns = [
    path('redirect/', redirect_view, name='redirect'),
    path('annotation/', annotation_dashboard, name='annotation_dashboard'),
    path('admin/', admin_dashboard, name='admin_dashboard'),
    path('annoter/', soumettre_annotation, name='soumettre_annotation'),
]
