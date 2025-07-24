from django.urls import path
from . import views
from .views import homepage
from .views import estatisticas_visitas
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', homepage, name='homepage'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('calculadora/', views.calculadora_view, name='calculadora'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('simuladores/', views.simuladores, name='simuladores'),
    path('calcular-custos/', views.calcular_custos, name='calcular_custos'),
    path('calcular-custos-trad/', views.calcular_custosTradicional, name='calcular_custos_tradicional'),
    path('faq/', views.faq, name='faq'),
    path('manuais/', views.manuais, name='manuais'),
    path('estudos/', views.estudos, name='estudos'),
    path('admin-visitas/', estatisticas_visitas, name='estatisticas_visitas'),
    path('clique/<str:nome_botao>/', views.registrar_clique_redirect, name='registrar_clique'),
    path('admin-cliques/', views.estatisticas_cliques, name='estatisticas_cliques'),
]