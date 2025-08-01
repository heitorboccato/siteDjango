from django.shortcuts import render
# mapa_saturacao/views.py
import os
from django.conf import settings
from django.http import HttpResponse
import pandas as pd
import folium
from datetime import datetime
from django.shortcuts import render
from .utils import criar_mapa, gerar_excel, avaliar_relatorio_por_gpt, gerar_parecer_pdf, gerar_html_top10_unidades
import io
import openai
import xlsxwriter

def mapa_view(request):
    arquivo_excel = os.path.join(settings.BASE_DIR, 'mapa', 'arquivos', 'Merged_UnidadesPerdasAMEI.xlsx')
    df = pd.read_excel(arquivo_excel)
    df = df.dropna(subset=['hora'])
    df['hora'] = df['hora'].astype(int)
    df['DATA'] = datetime.now().date()
    df['categoria'] = df['qtd_saturacao'].apply(
        lambda x: (
            'Alta' if x >= 100 else
            'Risco' if 70 <= x < 100 else
            'Média' if 40 <= x < 70 else
            'Baixa'
        )
    )

    # Filtros
    hora_selecionada = int(request.GET.get('hora', '8'))
    unidade_selecionada = request.GET.get('unidade', 'Todas')
    regional_selecionada = request.GET.get('regional', 'Todas')

    df_filtrado = df[df['hora'] == hora_selecionada]
    if unidade_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['unidade'] == unidade_selecionada]
    if regional_selecionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['regional'] == regional_selecionada]

    # Resumo dinâmico
    resumo_categorias = df_filtrado['categoria'].value_counts().to_dict()
    total_unidades = len(df_filtrado)
    top10_html = gerar_html_top10_unidades(df)
    mapa_html = criar_mapa(df_filtrado)._repr_html_() if not df_filtrado.empty else None

    # Listas para filtros
    horas = sorted(df['hora'].unique())
    unidades = ['Todas'] + sorted(df['unidade'].unique())
    regionais = ['Todas'] + sorted(df['regional'].unique())

    contexto = {
        'mapa_html': mapa_html,
        'horas': horas,
        'unidades': unidades,
        'regionais': regionais,
        'hora_selecionada': hora_selecionada,
        'unidade_selecionada': unidade_selecionada,
        'regional_selecionada': regional_selecionada,
        'resumo_categorias': resumo_categorias,
        'total_unidades': total_unidades,
        'top10_html': top10_html,
    }

    return render(request, 'mapa_saturacao/index.html', contexto)

# Create your views here.
def exportar_excel_view(request):
    # Caminho do Excel original
    caminho_arquivo = os.path.join(settings.BASE_DIR, 'mapa', 'arquivos', 'Merged_UnidadesPerdasAMEI.xlsx')
    df = pd.read_excel(caminho_arquivo)
    df = df.dropna(subset=['hora'])
    df['hora'] = df['hora'].astype(int)
    df['categoria'] = df['qtd_saturacao'].apply(
        lambda x: (
            'Alta' if x >= 100 else
            'Risco' if 70 <= x < 100 else
            'Média' if 40 <= x < 70 else
            'Baixa'
        )
    )

    media_por_regional = df.groupby(['hora', 'regional'])['qtd_saturacao'].mean().reset_index()
    media_por_regional['categoria'] = media_por_regional['qtd_saturacao'].apply(
        lambda x: (
            'Alta' if x >= 100 else
            'Risco' if 70 <= x < 100 else
            'Média' if 40 <= x < 70 else
            'Baixa'
        )
    )

    altas = df[df['categoria'] == 'Alta']
    baixas = df[df['categoria'] == 'Baixa']
    regionais_altas = media_por_regional[media_por_regional['categoria'] == 'Alta']
    regionais_medias = media_por_regional[media_por_regional['categoria'] == 'Média']
    regionais_baixas = media_por_regional[media_por_regional['categoria'] == 'Baixa']
    relatorio = df[['hora', 'unidade', 'regional', 'qtd_saturacao', 'categoria']].sort_values(by=['unidade', 'hora'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        relatorio.to_excel(writer, index=False, sheet_name='Completo')
        altas[['hora', 'unidade', 'regional', 'qtd_saturacao']].to_excel(writer, index=False, sheet_name='Unidades Saturação Alta')
        baixas[['hora', 'unidade', 'regional', 'qtd_saturacao']].to_excel(writer, index=False, sheet_name='Unidades Saturação Baixa')
        regionais_altas.to_excel(writer, index=False, sheet_name='Regionais Saturação Alta')
        regionais_medias.to_excel(writer, index=False, sheet_name='Regionais Saturação Média')
        regionais_baixas.to_excel(writer, index=False, sheet_name='Regionais Saturação Baixa')

    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=relatorio_saturacao_completo.xlsx'
    return response

openai.api_key = os.getenv("OPENAI_API_KEY")
def avaliacao_ia_view(request):
    caminho_arquivo = os.path.join(settings.BASE_DIR, 'mapa', 'arquivos', 'Merged_UnidadesPerdasAMEI.xlsx')
    df = pd.read_excel(caminho_arquivo)
    df = df.dropna(subset=['hora'])
    df['hora'] = df['hora'].astype(int)
    df['categoria'] = df['qtd_saturacao'].apply(
        lambda x: (
            'Alta' if x >= 100 else
            'Risco' if 70 <= x < 100 else
            'Média' if 40 <= x < 70 else
            'Baixa'
        )
    )

    parecer = avaliar_relatorio_por_gpt(df)

    return render(request, 'mapa_saturacao/avaliacao.html', {'parecer': parecer})

def download_parecer_pdf_view(request):
    caminho_arquivo = os.path.join(settings.BASE_DIR, 'mapa', 'arquivos', 'Merged_UnidadesPerdasAMEI.xlsx')
    df = pd.read_excel(caminho_arquivo)
    df = df.dropna(subset=['hora'])
    df['hora'] = df['hora'].astype(int)
    df['categoria'] = df['qtd_saturacao'].apply(
        lambda x: (
            'Alta' if x >= 100 else
            'Risco' if 70 <= x < 100 else
            'Média' if 40 <= x < 70 else
            'Baixa'
        )
    )
    # Carrega os dados originais
    df_original = df.copy()
    df_original = df_original.dropna(subset=['hora'])
    df_original['hora'] = df_original['hora'].astype(int)

    resumo_df = df.groupby("categoria")["unidade"].count().to_dict()
    parecer, resumo_df = avaliar_relatorio_por_gpt(df)

    pdf_buffer = gerar_parecer_pdf(parecer, resumo_df, df_original)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=parecer_ia.pdf'
    return response