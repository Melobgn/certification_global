from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test

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
    return render(request, 'core/annotation_dashboard.html')

# Vue pour l’admin (gestion de l’app)
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, 'core/admin_dashboard.html')
