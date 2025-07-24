from .models import PageVisit
from django.utils.deprecation import MiddlewareMixin
import uuid

class PageVisitMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None  # ignora assets e admin

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        PageVisit.objects.create(
            path=request.path,
            ip=ip,
            visitante_id=request.visitante_id  # ← aqui está o vínculo!
        )
        return None

class IdentificadorVisitanteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        visitante_id = request.COOKIES.get('visitante_id')
        if not visitante_id:
            visitante_id = str(uuid.uuid4())
            request.novo_visitante_id = visitante_id
        else:
            request.novo_visitante_id = None
        request.visitante_id = visitante_id
        response = self.get_response(request)
        if request.novo_visitante_id:
            response.set_cookie('visitante_id', visitante_id, max_age=31536000)  # 1 ano
        return response