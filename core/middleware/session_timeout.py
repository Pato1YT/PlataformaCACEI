import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

#Este archivo maneja el tiempo de inactividad de la sesión del usuario. 
#Si el usuario ha estado inactivo durante un período de tiempo definido en 
# settings.SESSION_TIMEOUT, se cerrará su sesión automáticamente. 
# Cada vez que el usuario realiza una acción, se actualiza el tiempo de su última actividad 
# en la sesión.

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = int(time.time())
            last_activity = request.session.get('last_activity', current_time)

            if current_time - last_activity > settings.SESSION_TIMEOUT:
                logout(request)
                messages.warning(request, "Tu sesión se cerró por inactividad.")
                return redirect('core:login')  
            else:
                request.session['last_activity'] = current_time

        response = self.get_response(request)
        return response