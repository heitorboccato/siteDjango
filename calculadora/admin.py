from django.contrib import admin
from .models import PageVisit
from .models import Usuario
from .models import ClickEvent
from .models import SistemaStatus

@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ('path', 'timestamp', 'ip')
    list_filter = ('path',)
    ordering = ('-timestamp',)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'unidade')
    search_fields = ('nome', 'email', 'unidade')

@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ('nome_botao', 'usuario', 'timestamp')
    list_filter = ('nome_botao', 'usuario')
    ordering = ('-timestamp',)
    search_fields = ('nome_botao', 'usuario__nome', 'usuario__email')

admin.site.register(SistemaStatus)