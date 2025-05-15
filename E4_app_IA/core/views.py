from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import VisionPrediction, ErrorImage
from django.views.decorators.http import require_POST
from .models import AnnotationManuelle
from datetime import datetime
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
import csv

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
    produits_image = list(VisionPrediction.objects.filter(confidence_score__isnull=False).order_by('-confidence_score'))
    produits_texte = list(ErrorImage.objects.values('url').distinct())

    # On ajoute un type pour les différencier dans le template
    for produit in produits_image:
        produit.type = 'image'

    for p in produits_texte:
        p['type'] = 'texte'

    produits_combines = produits_image + produits_texte

    # PAGINATION UNIQUE
    page = request.GET.get('page', 1)
    paginator = Paginator(produits_combines, 30)
    page_obj = paginator.get_page(page)

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
        messages.success(request, f"Annotation enregistrée pour l’URL : {url}")

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

    return response

# Vue pour l’admin (gestion de l’app)
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, 'core/admin_dashboard.html')

