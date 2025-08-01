# mapa_saturacao/urls.py
from django.urls import path
from .views import mapa_view, exportar_excel_view, avaliacao_ia_view, download_parecer_pdf_view

urlpatterns = [
    path('', mapa_view, name='mapa'),
    path('download/', exportar_excel_view, name='baixar_excel'),
    path('avaliacao/', avaliacao_ia_view, name='avaliacao_ia'),
    path('avaliacao/download/', download_parecer_pdf_view, name='baixar_parecer_pdf'),
]