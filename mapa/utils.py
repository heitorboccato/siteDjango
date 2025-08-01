# mapa_saturacao/utils.py
import folium
import io
import pandas as pd
import xlsxwriter
import markdown
from weasyprint import HTML
import io
import base64
from openai import OpenAI
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from django.conf import settings


def _get_color(weight):
    if weight < 10: return '#0070ff'
    elif 10 <= weight < 40: return '#49ff00'
    elif 40 <= weight < 70: return 'yellow'
    elif 70 <= weight < 100: return 'orange'
    else: return 'red'

def criar_mapa(df):
    mapa = folium.Map(location=[-15.788, -53.879], zoom_start=4, tiles='CartoDB dark_matter')
    for _, row in df.iterrows():
        folium.Circle(
            location=(row['latitude'], row['longitude']),
            radius=row['qtd_saturacao'] * 30,
            color=_get_color(row['qtd_saturacao']),
            fill=True,
            fill_color=_get_color(row['qtd_saturacao']),
            tooltip=f"{row['unidade']}: {row['qtd_saturacao']}% Saturação<br>Atendimentos previstos: {round(row['qtd_saturacao2'])}"
        ).add_to(mapa)

    legend_html = """<div style='position: fixed; bottom: 50px; left: 50px; width: 175px;
    background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;'>
        <b>Legenda:</b><br>
        <i style='background:blue;width:18px;height:18px;border-radius:50%;display:inline-block;'></i> Menos de 10%<br>
        <i style='background:#49ff00;width:18px;height:18px;border-radius:50%;display:inline-block;'></i> 10%-40%<br>
        <i style='background:yellow;width:18px;height:18px;border-radius:50%;display:inline-block;'></i> 40%-70%<br>
        <i style='background:orange;width:18px;height:18px;border-radius:50%;display:inline-block;'></i> 70%-100%<br>
        <i style='background:red;width:18px;height:18px;border-radius:50%;display:inline-block;'></i> Acima de 100%<br>
    </div>"""
    mapa.get_root().html.add_child(folium.Element(legend_html))
    return mapa

def gerar_excel(df):
    output = io.BytesIO()
    df['categoria'] = df['qtd_saturacao'].apply(
        lambda x: 'Alta' if x >= 100 else ('Baixa' if x < 40 else 'Média')
    )
    media_por_regional = df.groupby(['hora', 'regional'])['qtd_saturacao'].mean().reset_index()
    media_por_regional['categoria'] = media_por_regional['qtd_saturacao'].apply(
        lambda x: 'Alta' if x >= 100 else ('Baixa' if x < 40 else 'Média')
    )

    altas = df[df['categoria'] == 'Alta']
    baixas = df[df['categoria'] == 'Baixa']
    medias = df[df['categoria'] == 'Média']
    regionais_altas = media_por_regional[media_por_regional['categoria'] == 'Alta']
    regionais_medias = media_por_regional[media_por_regional['categoria'] == 'Média']
    regionais_baixas = media_por_regional[media_por_regional['categoria'] == 'Baixa']
    relatorio = df[['hora', 'unidade', 'regional', 'qtd_saturacao', 'categoria']]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        relatorio.to_excel(writer, index=False, sheet_name='Completo')
        altas[['hora', 'unidade', 'regional', 'qtd_saturacao']].to_excel(writer, index=False, sheet_name='Unidades Saturação Alta')
        baixas[['hora', 'unidade', 'regional', 'qtd_saturacao']].to_excel(writer, index=False, sheet_name='Unidades Saturação Baixa')
        regionais_altas.to_excel(writer, index=False, sheet_name='Regionais Saturação Alta')
        regionais_medias.to_excel(writer, index=False, sheet_name='Regionais Saturação Média')
        regionais_baixas.to_excel(writer, index=False, sheet_name='Regionais Saturação Baixa')

    output.seek(0)
    return output

def avaliar_relatorio_por_gpt(df):
    # Conta unidades únicas por hora e categoria
    tabela = df.groupby(['hora', 'categoria'])['unidade'].nunique().unstack(fill_value=0)

    # Monta o resumo textual organizado por hora
    resumo_textual = "Resumo de unidades por categoria e hora:\n"
    for hora, row in tabela.iterrows():
        resumo_textual += f"\nHora {hora}:\n"
        for categoria in ['Alta', 'Média', 'Baixa']:
            qtd = row.get(categoria, 0)
            resumo_textual += f"  - {categoria}: {qtd} unidades\n"

    prompt = f"""
    Você é um analista de dados em uma franqueadora de Saúde, chamada AmorSaúde.

    {resumo_textual}

    Analise os dados enviados considerando padrões de saturação e subutilização por hora e categoria.
    Identifique horários críticos, horários ociosos e possíveis causas.
    Destaque diferenças entre categorias (como especialidades ou canais) e forneça sugestões práticas para equilibrar a demanda.
    Estruture sua resposta com insights claros e sugestões de gestão.
    """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um analista de dados em uma franqueadora de Saúde, chamada AmorSaúde."},
            {"role": "user", "content": prompt}
        ]
    )

    return resposta.choices[0].message.content.strip(), tabela
def markdown_para_html(texto_markdown):
    return markdown.markdown(texto_markdown)

import markdown
from weasyprint import HTML
import io
import base64
import os
from django.conf import settings

def markdown_para_html(texto_markdown):
    return markdown.markdown(texto_markdown)

def gerar_html_parecer(parecer_html, resumo_df, df_original):
    # Caminho do logo
    caminho_logo = os.path.join(settings.BASE_DIR, 'mapa', 'static', 'mapa_saturacao', 'logo_idn.png')
    
    if os.path.exists(caminho_logo):
        with open(caminho_logo, "rb") as image_file:
            logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        logo_html = f"<img src='data:image/png;base64,{logo_base64}' style='height:60px;'>"
    else:
        logo_html = ""

    # Construção da tabela de resumo por hora
    linhas = ""
    for hora, row in resumo_df.iterrows():
        altas = row.get("Alta", 0)
        #riscos = row.get("Risco", 0)
        medias = row.get("Média", 0)
        baixas = row.get("Baixa", 0)
        linhas += f"<tr><td>{hora}</td><td>{altas}</td><td>{medias}</td><td>{baixas}</td></tr>" #<td>{riscos}</td>

    # Top 10 unidades com mais saturações altas
    saturacao_alta = (
        df_original[df_original['qtd_saturacao'] >= 100]
        .groupby('unidade')
        .size()
        .reset_index(name='ocorrencias')
        .sort_values(by='ocorrencias', ascending=False)
    )
    top_unidades = saturacao_alta.head(10)['unidade'].tolist()

    top_unidades_html = ""
    for unidade in top_unidades:
        horas = (
            df_original[(df_original['unidade'] == unidade) & (df_original['qtd_saturacao'] >= 100)]
            .groupby('hora')
            .size()
            .reset_index(name='ocorrencias')
            .sort_values(by='ocorrencias', ascending=False)
        )

        # Pegando as 3 horas mais frequentes de saturação (ou menos, se tiver menos dados)
    top_horas = horas.head(3)['hora'].tolist()
    horas_formatadas = ', '.join(f"{int(h)}h" for h in top_horas)

    top_unidades_html += f"<li>{unidade} — Horários críticos: {horas_formatadas}</li>"

    # Unidades com horários atípicos
# Filtro para os dois intervalos
    madrugada = df_original[df_original['hora'].between(0, 7)]
    noite = df_original[df_original['hora'].between(19, 23)]

    # Unidades que aparecem nos dois períodos
    unidades_madrugada = set(madrugada['unidade'].unique())
    unidades_noite = set(noite['unidade'].unique())

    # Interseção: unidades que estão nos dois períodos
    unidades_ambos = unidades_madrugada & unidades_noite

    # Agora você pode montar o HTML
    unidades_atipicas_html = "".join(f"<li>{unidade}</li>" for unidade in sorted(unidades_ambos))

    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                color: #333;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .title {{
                font-size: 22px;
                font-weight: bold;
                color: #0c223c;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 13px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
            }}
            h2 {{
                color: #0c223c;
                margin-top: 30px;
            }}
            ul {{
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">Relatório de Saturação - Análise com IA</div>
            {logo_html}
        </div>

        <h2>Resumo por hora e categoria</h2>
        <table>
            <tr>
                <th>Hora</th>
                <th>Alta</th>
                <th>Risco</th>
                <th>Média</th>
                <th>Baixa</th>
            </tr>
            {linhas}
        </table>

        <h2>Top 10 unidades com maior número de saturações altas</h2>
        <ul>{top_unidades_html}</ul>

        <h2>Unidades com atendimentos em horários atípicos (0h–7h e 19h–23h)</h2>
        <ul>{unidades_atipicas_html}</ul>

        <h2>Parecer da IA</h2>
        {parecer_html}
    </body>
    </html>
    """

def gerar_parecer_pdf(parecer_texto, resumo_df, df_original):
    html_parecer = markdown_para_html(parecer_texto)
    html_completo = gerar_html_parecer(html_parecer, resumo_df, df_original)

    pdf_bytes = HTML(string=html_completo).write_pdf()
    return io.BytesIO(pdf_bytes)

def gerar_html_top10_unidades(df_original):
    # Filtra saturações altas
    saturacao_alta = (
        df_original[df_original['qtd_saturacao'] >= 100]
        .groupby('unidade')
        .size()
        .reset_index(name='ocorrencias')
        .sort_values(by='ocorrencias', ascending=False)
    )

    top_unidades = saturacao_alta.head(10)['unidade'].tolist()

    # Gera o HTML das top 10 unidades com os horários críticos
    top_unidades_html = ""
    for unidade in top_unidades:
        horas = (
            df_original[(df_original['unidade'] == unidade) & (df_original['qtd_saturacao'] >= 100)]
            .groupby('hora')
            .size()
            .reset_index(name='ocorrencias')
            .sort_values(by='ocorrencias', ascending=False)
        )

        top_horas = horas.head(3)['hora'].tolist()
        horas_formatadas = ', '.join(f"{int(h)}h" for h in top_horas)

        top_unidades_html += f"<p><strong>{unidade}</strong>: <strong>{horas_formatadas}</strong><p>"

    return f"<p>{top_unidades_html}</p>"