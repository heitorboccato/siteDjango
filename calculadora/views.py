from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count, Max, Subquery, OuterRef
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from .models import PageVisit
from .models import ClickEvent
from .models import SistemaStatus
from django.shortcuts import render, redirect
from django.db.models import Count
from django.shortcuts import resolve_url
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Usuario, PageVisit, ClickEvent
from .forms import UsuarioCadastroForm, UsuarioLoginForm
from django.db.models import Count, Max

def get_client_ip(request):
    """Captura o IP real do usuário (mesmo com proxy reverso)."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required(login_url='login')
def homepage(request):
    status = SistemaStatus.objects.last()
    return render(request, 'calculadora/index.html', {'status': status})

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'calculadora/dashboards.html')

@login_required(login_url='login')
def simuladores(request):
    return render(request, 'calculadora/simuladores.html')

@login_required(login_url='login')
def estudos(request):
    return render(request, 'calculadora/estudos.html')

@login_required(login_url='login')
def manuais(request):
    return render(request, 'calculadora/manuais.html')

@login_required(login_url='login')
def faq(request):
    return render(request, 'calculadora/faq.html')


@login_required(login_url='login')
def registrar_clique_redirect(request, nome_botao):
    print("Tipo real:", type(request.user._wrapped))
    print("É do tipo Usuario?", isinstance(request.user._wrapped, Usuario))
    ClickEvent.objects.create(
        usuario=request.user,
        nome_botao=nome_botao
    )

    destinos = {
        'powerbi_geral': 'https://app.powerbi.com/groups/51cc537c-5473-407a-bba4-05bb672d3e9e/list?experience=power-bi',
        'powerbi_AMEI':'https://app.powerbi.com/groups/51cc537c-5473-407a-bba4-05bb672d3e9e/reports/83920be7-182c-4278-9e68-8e572c542ca0/ReportSection?experience=power-bi',
        'powerbi_Feegow': 'https://app.powerbi.com/groups/51cc537c-5473-407a-bba4-05bb672d3e9e/reports/85876d1c-8ec1-4ca5-b324-8ca45b2a84f9/ReportSection?experience=power-bi',
        'powerbi_Odonto': 'https://app.powerbi.com/groups/51cc537c-5473-407a-bba4-05bb672d3e9e/reports/864d8898-3e29-4bd5-9b4c-fa1046604e2b/b6ea7e9afad44cf11509?experience=power-bi',
        'simulador_exames': 'https://amorsaude.com.br/simulador_exames/',
        'simulador_compra': 'https://amorsaude.com.br/simulador/',
        'linkZeev': 'https://amorsaude.zeev.it/my/services#inteligencia_de_negocio',
        'estudos': '/estudos/',
        'dashboard': '/dashboard/',
        'simuladores': '/simuladores/',
        'calculadora': '/calculadora/',
        'manuais': '/manuais/',
        'mapa_index': '/mapa/',
        'faq': '/faq/',
        'homepage': '/',
    }
    url_destino = destinos.get(nome_botao)
    if url_destino:
        return redirect(url_destino)
    else:
        # fallback seguro
        return redirect('homepage')


def calculadora_view(request):
    tela = request.GET.get('tela', 'pj')  # Alterna entre 'pj' e 'normal'
    context = {'tela': tela}

    if request.method == 'POST':
        # Entrada dos dados comuns
        valor_consulta = float(request.POST.get('valor_consulta', 40))
        qtde_consultas = int(request.POST.get('qtde_consultas', 40))
        repasse = float(request.POST.get('repasse', 37))
        deslocamento = float(request.POST.get('deslocamento', 100))
        custo_exames_percent = int(request.POST.get('custo_exames_percent', 20))

        receita_total = valor_consulta * qtde_consultas
        faturamento_clinica = valor_consulta - repasse
        receita_total_clinica = faturamento_clinica * qtde_consultas

        # Cálculo dos impostos
        impostos = {
            'ISS (4%)': receita_total_clinica * 0.04,
            'PIS (0,65%)': receita_total_clinica * 0.0065,
            'COFINS (3%)': receita_total_clinica * 0.03,
            'IR (8%)': receita_total_clinica * 0.08,
            'CSLL (2,88%)': receita_total_clinica * 0.02875,
            'Royalties (4%)': receita_total * 0.04,
            'Taxa (3,5%)': receita_total_clinica * 0.035,
        }
        total_impostos = sum(impostos.values())

        custo_total = (repasse * qtde_consultas) + deslocamento + total_impostos
        resultado_final = receita_total - custo_total

        if resultado_final < 0 and custo_exames_percent < 100:
            venda_minima_exame = (-resultado_final) / (custo_exames_percent / 100)
        else:
            venda_minima_exame = 0

        custo_total_exame = venda_minima_exame * custo_exames_percent / 100
        resultado_exame = venda_minima_exame - custo_total_exame
        resultado_final_total = resultado_exame + resultado_final

        context.update({
            'valor_consulta': valor_consulta,
            'qtde_consultas': qtde_consultas,
            'repasse': repasse,
            'deslocamento': deslocamento,
            'custo_exames_percent': custo_exames_percent,
            'receita_total': receita_total,
            'custo_total': custo_total,
            'resultado_final': resultado_final,
            'impostos': impostos,
            'venda_minima_exame': venda_minima_exame,
            'custo_total_exame': custo_total_exame,
            'resultado_exame': resultado_exame,
            'resultado_final_total': resultado_final_total,
        })
        if request.headers.get('Hx-Request') == 'true':
            target = request.headers.get('Hx-Target')
            print(f"Target: {faturamento_clinica}")
            print(f"Target: {target}")
            if target == 'resultado':
                return render(request, 'calculadora/partials/resultado.html', context)
                
    return render(request, 'calculadora/calculadora.html', context)

@csrf_exempt
def calcular_custos(request):
    tela = request.GET.get('tela', 'pj')  # Alterna entre 'pj' e 'normal'
    context = {'tela': tela}

    if request.method == 'POST':
        # Entrada dos dados comuns
        valor_consulta = float(request.POST.get('valor_consulta', 40))
        qtde_consultas = int(request.POST.get('qtde_consultas', 40))
        repasse = float(request.POST.get('repasse', 37))
        deslocamento = float(request.POST.get('deslocamento', 100))
        custo_exames_percent = int(request.POST.get('custo_exames_percent', 20))

        receita_total = valor_consulta * qtde_consultas
        faturamento_clinica = valor_consulta - repasse
        receita_total_clinica = faturamento_clinica * qtde_consultas

        # Cálculo dos impostos
        impostos = {
            'ISS (4%)': receita_total_clinica * 0.04,
            'PIS (0,65%)': receita_total_clinica * 0.0065,
            'COFINS (3%)': receita_total_clinica * 0.03,
            'IR (8%)': receita_total_clinica * 0.08,
            'CSLL (2,88%)': receita_total_clinica * 0.02875,
            'Royalties (4%)': receita_total * 0.04,
            'Taxa (3,5%)': receita_total_clinica * 0.035,
        }
        total_impostos = sum(impostos.values())

        custo_total = (repasse * qtde_consultas) + deslocamento + total_impostos
        resultado_final = receita_total - custo_total

        if resultado_final < 0 and custo_exames_percent < 100:
            venda_minima_exame = (-resultado_final) / (custo_exames_percent / 100)
        else:
            venda_minima_exame = 0

        custo_total_exame = venda_minima_exame * custo_exames_percent / 100
        resultado_exame = venda_minima_exame - custo_total_exame
        resultado_final_total = resultado_exame + resultado_final

        context.update({
            'valor_consulta': valor_consulta,
            'qtde_consultas': qtde_consultas,
            'repasse': repasse,
            'deslocamento': deslocamento,
            'custo_exames_percent': custo_exames_percent,
            'receita_total': receita_total,
            'custo_total': custo_total,
            'resultado_final': resultado_final,
            'impostos': impostos,
            'venda_minima_exame': venda_minima_exame,
            'custo_total_exame': custo_total_exame,
            'resultado_exame': resultado_exame,
            'resultado_final_total': resultado_final_total,
        })
        if request.headers.get('Hx-Request') == 'true':
            target = request.headers.get('Hx-Target')
            print(f"Target: {target}")
            if target == 'custos':    
                return render(request, 'calculadora/partials/custo.html', {'impostos': impostos, 'resultado_final': resultado_final, 'venda_minima_exame': venda_minima_exame})

    return JsonResponse({'erro': 'Método inválido'}, status=400)

@csrf_exempt
def calcular_custosTradicional(request):
    tela = request.GET.get('tela', 'trad')  # Alterna entre 'pj' e 'normal'
    context = {'tela': tela}

    if request.method == 'POST':
        # Entrada dos dados comuns
        valor_consulta = float(request.POST.get('valor_consulta', 40))
        qtde_consultas = int(request.POST.get('qtde_consultas', 40))
        repasse = float(request.POST.get('repasse', 37))
        deslocamento = float(request.POST.get('deslocamento', 100))
        custo_exames_percent = int(request.POST.get('custo_exames_percent', 20))

        receita_total = valor_consulta * qtde_consultas
        faturamento_clinica = valor_consulta - repasse
        receita_total_clinica = faturamento_clinica * qtde_consultas

        # Cálculo dos impostos
        impostos = {
            'ISS (4%)': receita_total * 0.04,
            'PIS (0,65%)': receita_total * 0.0065,
            'COFINS (3%)': receita_total * 0.03,
            'IR (8%)': receita_total * 0.08,
            'CSLL (2,88%)': receita_total * 0.02875,
            'Royalties (4%)': receita_total * 0.04,
            'Taxa (3,5%)': receita_total * 0.035,
        }
        total_impostos = sum(impostos.values())

        custo_total = (repasse * qtde_consultas) + deslocamento + total_impostos
        resultado_final = receita_total - custo_total

        if resultado_final < 0 and custo_exames_percent < 100:
            venda_minima_exame = (-resultado_final) / (custo_exames_percent / 100)
        else:
            venda_minima_exame = 0

        custo_total_exame = venda_minima_exame * custo_exames_percent / 100
        resultado_exame = venda_minima_exame - custo_total_exame
        resultado_final_total = resultado_exame + resultado_final

        context.update({
            'valor_consulta': valor_consulta,
            'qtde_consultas': qtde_consultas,
            'repasse': repasse,
            'deslocamento': deslocamento,
            'custo_exames_percent': custo_exames_percent,
            'receita_total': receita_total,
            'custo_total': custo_total,
            'resultado_final': resultado_final,
            'impostos': impostos,
            'venda_minima_exame': venda_minima_exame,
            'custo_total_exame': custo_total_exame,
            'resultado_exame': resultado_exame,
            'resultado_final_total': resultado_final_total,
        })
        if request.headers.get('Hx-Request') == 'true':
            target = request.headers.get('Hx-Target')
            print(f"Impostos: {impostos}")
            print(f"Target: {target}")
            if target == 'custos':    
                return render(request, 'calculadora/partials/custo.html', {'impostos': impostos, 'resultado_final': resultado_final, 'venda_minima_exame': venda_minima_exame})

    return JsonResponse({'erro': 'Método inválido'}, status=400)

#### Cadastro e Login de Usuários ####
def cadastro_view(request):
    if request.method == 'POST':
        form = UsuarioCadastroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)  # cria o objeto mas ainda não salva
            usuario.set_password(form.cleaned_data['senha'])  # hash da senha
            usuario.save()
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('login')
    else:
        form = UsuarioCadastroForm()
    return render(request, 'registration/cadastro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UsuarioLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            senha = form.cleaned_data['password']
            user = authenticate(request, email=email, password=senha)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next') or '/'
                return redirect(next_url)
            else:
                messages.error(request, 'Email ou senha inválidos.')
    else:
        form = UsuarioLoginForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def estatisticas_cliques(request):
    usuario_nome = request.GET.get('usuario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    cliques = ClickEvent.objects.select_related('usuario')

    if usuario_nome:
        cliques = cliques.filter(usuario__nome__icontains=usuario_nome)

    if data_inicio:
        cliques = cliques.filter(timestamp__date__gte=data_inicio)
    if data_fim:
        cliques = cliques.filter(timestamp__date__lte=data_fim)

    cliques = cliques.order_by('-timestamp')

    total_por_botao = (
        cliques
        .values('nome_botao')
        .annotate(total_cliques=Count('id'))
        .order_by('-total_cliques')
    )

    totais_dict = {item['nome_botao']: item['total_cliques'] for item in total_por_botao}

    return render(request, 'calculadora/estatisticas_cliques.html', {
        'cliques': cliques,
        'total_por_botao': total_por_botao,
        'totais_dict': totais_dict,
        'nome': request.user.nome,
        'email': request.user.email
    })

@login_required
def estatisticas_visitas(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    visitas = PageVisit.objects.all()

    if data_inicio:
        visitas = visitas.filter(timestamp__date__gte=data_inicio)
    if data_fim:
        visitas = visitas.filter(timestamp__date__lte=data_fim)

    visitas = (
        visitas
        .values('path')
        .annotate(
            total_acessos=Count('id'),
            usuarios_unicos=Count('visitante_id', distinct=True),
            ultimo_acesso=Max('timestamp')
        )
        .order_by('-total_acessos')
    )

    return render(request, 'calculadora/estatisticas_visitas.html', {
        'visitas': visitas,
        'nome': request.user.nome,
        'email': request.user.email
    })