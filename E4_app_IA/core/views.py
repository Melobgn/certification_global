import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.conf import settings

from .models import VisionPrediction, ErrorImage, AnnotationManuelle

from datetime import datetime
from django.db.models import Count
import sqlite3
import json
import csv

logger = logging.getLogger('core')

User = get_user_model()

def home_view(request):
    return render(request, 'core/home.html')

def is_analyst(user):
    return user.is_authenticated and user.role == 'analyst'

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@login_required
def redirect_view(request):
    user = request.user
    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'analyst':
        return redirect('annotation_dashboard')
    else:
        return redirect('login')

@login_required
@user_passes_test(is_analyst)
def annotation_dashboard(request):
    if getattr(settings, "TESTING", False):
        produits_image = []
    else:
        produits_image = list(VisionPrediction.objects.filter(confidence_score__isnull=False).order_by('-confidence_score'))

    produits_texte = list(ErrorImage.objects.values('url').distinct())

    for produit in produits_image:
        produit.type = 'image'

    for p in produits_texte:
        p['type'] = 'texte'

    produits_combines = produits_image + produits_texte

    page = request.GET.get('page', 1)
    paginator = Paginator(produits_combines, 30)
    page_obj = paginator.get_page(page)

    logger.info(f"{request.user} a consulté le tableau d'annotation avec {len(produits_combines)} produits.")

    return render(request, 'core/annotation_dashboard.html', {
        'produits': page_obj,
        'year': datetime.now().year
    })

@login_required
@user_passes_test(is_analyst)
@require_POST
def soumettre_annotation(request):
    url = request.POST.get('url')
    action = request.POST.get('action')
    page = request.POST.get('page')

    if url and action in ['vrai', 'faux']:
        user_obj = User.objects.using('default').get(pk=request.user.pk)
        AnnotationManuelle.objects.using('default').update_or_create(
            url=url,
            user=user_obj,
            defaults={'is_confirmed_weapon': action == 'vrai'}
        )
        logger.info(f"Annotation enregistrée - URL : {url}, Action : {action}, Utilisateur : {request.user}")
        messages.success(request, f"Annotation enregistrée pour l’URL : {url}")
    else:
        logger.warning(f"Soumission invalide - URL : {url}, Action : {action}, Utilisateur : {request.user}")

    if page:
        return HttpResponseRedirect(f"{reverse('annotation_dashboard')}?page={page}")
    return redirect('annotation_dashboard')

@login_required
@user_passes_test(is_analyst)
def historique_annotations(request):
    annotations = AnnotationManuelle.objects.using('default').filter(user=request.user).order_by('-date_annotation')
    paginator = Paginator(annotations, 20)
    page = request.GET.get('page')
    annotations_page = paginator.get_page(page)

    logger.info(f"{request.user} a consulté son historique d’annotations.")

    return render(request, 'core/historique_annotations.html', {
        'annotations_page': annotations_page
    })

@login_required
@user_passes_test(is_analyst)
def telecharger_annotations_csv(request):
    annotations = AnnotationManuelle.objects.using('default').filter(user=request.user).order_by('-date_annotation')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=annotations_produits_partenaires.csv'

    writer = csv.writer(response)
    writer.writerow(['URL', 'Type', 'Date annotation', 'Résultat'])

    for ann in annotations:
        resultat = "Vrai positif" if ann.is_confirmed_weapon else "Faux positif"
        writer.writerow([ann.url, 'Produit suspect', ann.date_annotation.strftime("%d/%m/%Y %H:%M"), resultat])

    logger.info(f"{request.user} a téléchargé ses annotations au format CSV.")

    return response

def dashboard_data_from_sqlite():
    if getattr(settings, "TESTING", False):
        return 0  # Bypass en mode test
    try:
        db_path = settings.DATABASES['weapon_data']['NAME']
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions_xgboost WHERE is_weapon_pred = 1")
            nb_xgb = cursor.fetchone()[0]
        return nb_xgb
    except Exception as e:
        logger.warning(f"Erreur d'accès à weapon_data : {e}")
        return 0

@login_required
@user_passes_test(is_analyst)
def dashboard_view(request):
    nb_xgb = dashboard_data_from_sqlite()
    nb_yolo = VisionPrediction.objects.count()
    nb_errors = ErrorImage.objects.values('url').distinct().count()
    nb_annotations = AnnotationManuelle.objects.using('default').count()
    nb_vrais = AnnotationManuelle.objects.using('default').filter(is_confirmed_weapon=True).count()
    nb_faux = AnnotationManuelle.objects.using('default').filter(is_confirmed_weapon=False).count()

    annotations_par_date = (
        AnnotationManuelle.objects.using('default')
        .extra(select={'day': "DATE(date_annotation)"})
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
    )

    last_annotations = (
        AnnotationManuelle.objects.using('default')
        .select_related('user')
        .order_by('-date_annotation')[:10]
    )

    logger.info(f"{request.user} a accédé au dashboard analyste.")

    if nb_xgb == 0 or nb_yolo == 0:
        logger.warning(f"Alerte : modèles sans détection ! YOLO: {nb_yolo}, XGBoost: {nb_xgb}")

    return render(request, 'core/dashboard.html', {
        'nb_xgb': nb_xgb,
        'nb_yolo': nb_yolo,
        'nb_errors': nb_errors,
        'nb_annotations': nb_annotations,
        'nb_vrais': nb_vrais,
        'nb_faux': nb_faux,
        'annotations_dates_json': json.dumps([
            {'date': a['day'], 'total': a['total']}
            for a in annotations_par_date
        ]),
        'last_annotations': last_annotations,
    })

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    logger.info(f"{request.user} a accédé au dashboard admin.")
    return render(request, 'core/admin_dashboard.html')
