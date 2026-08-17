import streamlit as st
import pandas as pd
import requests
from pathlib import Path # <-- Importamos o Pathlib aqui

# ==========================================
# 1. CONFIGURAÇÃO DE CAMINHOS (PATHLIB)
# ==========================================
# Descobre a pasta onde este ficheiro (ex: utils.py) está guardado.
BASE_DIR = Path(__file__).parent

# Volta duas pastas para trás para chegar à raiz do projeto (assumindo a mesma estrutura).
# Exemplo: Sitte (BASE_DIR) -> Codigos (.parent) -> CD-Att (.parent.parent)
RAIZ_DO_PROJETO = BASE_DIR.parent.parent

# Cria o caminho base para a pasta onde estão os teus CSVs
PASTA_CSVS = RAIZ_DO_PROJETO / "CSV" / "Dados_Limpos"

# ==========================================
# 2. DEFINIÇÃO DOS FICHEIROS
# ==========================================
# Agora, basta juntar a pasta aos nomes dos ficheiros!
CAMINHO_ESPACIAL = PASTA_CSVS / "04_micro_posicionamento_limpo.csv"
CAMINHO_TATICO = PASTA_CSVS / "03_telemetria_tatica_limpa.csv"
CAMINHO_VLR = PASTA_CSVS / "01_vlr_matches_limpo.csv"

@st.cache_data
def carregar_dados_mestres():
    try:
        # 1. Carregar os ficheiros corretamente mapeados
        df_espacial = pd.read_csv(CAMINHO_ESPACIAL)
        df_tatico = pd.read_csv(CAMINHO_TATICO)
        
        # 2. Limpeza de segurança (remove espaços invisíveis nos nomes das colunas)
        df_espacial.columns = df_espacial.columns.str.strip()
        df_tatico.columns = df_tatico.columns.str.strip()
        
        # 3. Limpar coordenadas inválidas
        df_espacial = df_espacial[(df_espacial['Vitima_X'] != 0) & (df_espacial['Vitima_Y'] != 0)].copy()
        
        # 4. Normalizar os nomes no ficheiro ESPACIAL (Coordenadas)
        df_espacial = df_espacial.rename(columns={
            'Matador': 'Eliminador',
            'Vitima': 'Eliminado',
            'Equipa_Matador': 'Equipa_Eliminador',
            'Equipa_Vitima': 'Equipa_Eliminado',
            'Vitima_X': 'Eliminado_X',
            'Vitima_Y': 'Eliminado_Y'
        })
        
        # 5. Normalizar os nomes no ficheiro TÁTICO para baterem certo na fusão
        df_tatico = df_tatico.rename(columns={
            'Killer': 'Eliminador',
            'Victim': 'Eliminado',
            'Round_Numero': 'Round',
            'Arma_Utilizada': 'Arma' 
        })
        
        # 6. A FUSÃO DOS DADOS (Merge)
        df_mestre = pd.merge(
            df_espacial, 
            df_tatico[['ID_Serie', 'Mapa', 'Round', 'Eliminador', 'Eliminado', 'Lado_Killer', 'Tipo_Dano', 'Trade_Kill', 'Assistencias', 'Qtd_Assistencias']], 
            on=['ID_Serie', 'Mapa', 'Round', 'Eliminador', 'Eliminado'],
            how='left' 
        )
        
        # 7. Preencher valores vazios para não quebrar o código
        df_mestre['Assistencias'] = df_mestre['Assistencias'].fillna("Nenhuma")
        df_mestre['Trade_Kill'] = df_mestre['Trade_Kill'].fillna(False)
        df_mestre['Lado_Killer'] = df_mestre['Lado_Killer'].fillna("Desconhecido")
        
        return df_mestre
        
    except FileNotFoundError as e:
        st.error(f"Erro: Ficheiro CSV não encontrado. Verifica se a pasta existe. Detalhes: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar e fundir os CSVs: {e}")
        return pd.DataFrame()

@st.cache_data
def obter_mapas_riot():
    try:
        resposta = requests.get("https://valorant-api.com/v1/maps")
        return resposta.json()['data']
    except Exception as e:
        st.error(f"Erro ao ligar à API do Valorant: {e}")
        return []
    
@st.cache_data
def carregar_dados_vlr():
    try:
        df_vlr = pd.read_csv(CAMINHO_VLR)
        # Limpar espaços invisíveis nas colunas
        df_vlr.columns = df_vlr.columns.str.strip()
        return df_vlr
    except FileNotFoundError as e:
        st.error(f"Erro: Ficheiro VLR não encontrado. Detalhes: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados do VLR: {e}")
        return pd.DataFrame()