# utils.py
import pandas as pd

def carregar_unidades_do_excel(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo)
    unidades = df['Nome Unidade'].dropna().unique()
    return [(unidade, unidade) for unidade in unidades]