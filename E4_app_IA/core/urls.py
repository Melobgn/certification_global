from django.urls import path
from .views import (
    home_view,
    redirect_view,
    annotation_dashboard,
    admin_dashboard,
    soumettre_annotation,
    historique_annotations,
    telecharger_annotations_csv
)

urlpatterns = [
    path('home/', home_view, name='home'),
    path('redirect/', redirect_view, name='redirect'),
    path('annotation/', annotation_dashboard, name='annotation_dashboard'),
    path('admin/', admin_dashboard, name='admin_dashboard'),
    path('annoter/', soumettre_annotation, name='soumettre_annotation'),
    path('historique/', historique_annotations, name='historique_annotations'),
    path('historique/csv/', telecharger_annotations_csv, name='telecharger_annotations_csv'),
]