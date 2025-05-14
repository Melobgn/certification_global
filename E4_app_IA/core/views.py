from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import VisionPrediction, ErrorImage
from django.views.decorators.http import require_POST
from .models import AnnotationManuelle
from datetime import datetime
from django.contrib.auth import get_user_model
User = get_user_model()

def home_view(request):
    return render(request, 'core/home.html')

# Test pour savoir si l'utilisateur est un analyste
def is_analyst(user):
    return user.is_authenticated and user.role == 'analyst'

# Test pour savoir si l'utilisateur est admin
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

# Redirection post-login
@login_required
def redirect_view(request):
    user = request.user

    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'analyst':
        return redirect('annotation_dashboard')
    else:
        return redirect('login')

# Vue pour les analystes risques (annotation)
@login_required
@user_passes_test(is_analyst)
def annotation_dashboard(request):
    # 1. Produits avec image (vision YOLO)
    produits_avec_image = VisionPrediction.objects.all().order_by('-confidence_score')

    # 2. Produits sans image (erreurs listées mais suspicion xgboost)
    alertes_sans_image = ErrorImage.objects.values('url').distinct()

    return render(request, 'core/annotation_dashboard.html', {
        'produits_avec_image': produits_avec_image,
        'alertes_sans_image': alertes_sans_image,
        'year': datetime.now().year
    })


@login_required
@user_passes_test(is_analyst)
@require_POST
def soumettre_annotation(request):
    url = request.POST.get('url')
    action = request.POST.get('action')  # 'vrai' ou 'faux'

    if url and action in ['vrai', 'faux']:
        # On récupère l’utilisateur explicitement depuis la base 'default'
        user_obj = User.objects.using('default').get(pk=request.user.pk)
        AnnotationManuelle.objects.using('default').update_or_create(
            url=url,
            user=user_obj,
            defaults={'is_confirmed_weapon': action == 'vrai'}
        )
    return redirect('annotation_dashboard')


@login_required
@user_passes_test(is_analyst)
def historique_annotations(request):
    annotations = AnnotationManuelle.objects.using('default').filter(user=request.user).order_by('-date_annotation')
    return render(request, 'core/historique_annotations.html', {
        'annotations': annotations,
        'year': datetime.now().year
    })


# Vue pour l’admin (gestion de l’app)
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, 'core/admin_dashboard.html')

