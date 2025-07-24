from django.contrib.auth.backends import ModelBackend
from .models import Usuario

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Usuario.objects.get(email=email)
            if user.check_password(password):
                return user
        except Usuario.DoesNotExist:
            return None