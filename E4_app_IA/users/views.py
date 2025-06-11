from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
import logging

logger = logging.getLogger('users')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"Nouvelle inscription réussie : {user.username}")
            return redirect('login')
        else:
            logger.warning("Échec d'inscription : données invalides")
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
