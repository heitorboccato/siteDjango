from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings

import calculadora

# Create your models here.
class PageVisit(models.Model):
    path = models.CharField(max_length=255)  # ex: /estudos/
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    visitante_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.path} em {self.timestamp}"
    
class ClickEvent(models.Model):
    usuario = models.ForeignKey('calculadora.Usuario', on_delete=models.CASCADE, null=True, blank=True)
    nome_botao = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_botao} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
    
class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, unidade, password=None):
        if not email:
            raise ValueError("O usuário deve ter um e-mail")
        user = self.model(email=self.normalize_email(email), nome=nome, unidade=unidade)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, unidade, password):
        user = self.create_user(email, nome, unidade, password)
        user.is_admin = True
        user.save(using=self._db)
        return user

class Usuario(AbstractBaseUser):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    unidade = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome', 'unidade']

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        return self.is_admin
    
    # ✅ Adicione estes dois métodos abaixo:
    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin
    
class SistemaStatus(models.Model):
    atualizado_em = models.DateTimeField(auto_now=True)

    powerbi_online = models.BooleanField(default=False)
    powerbi_atualizado = models.BooleanField(default=False)
    powerbi_odonto = models.BooleanField(default=False)

    sistema_amei_online = models.BooleanField(default=True)
    

    def __str__(self):
        return f"Status atualizado em {self.atualizado_em}"