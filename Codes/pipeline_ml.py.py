import pandas as pd
import numpy as np
import pickle
from pathlib import Path # <-- Importamos o Pathlib aqui!
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report

# ==========================================
# 1. CONFIGURAÇÃO DE CAMINHOS (PATHLIB)
# ==========================================
# BASE_DIR é a pasta exata onde este script de Python está guardado.
BASE_DIR = Path(__file__).parent

# Aqui fazemos a "navegação". 
# Supondo que este script esteja em: D:\mack\tcc\ATTs\CD-Att\Codigos\Sitte\
# E o CSV esteja em:                 D:\mack\tcc\ATTs\CD-Att\CSV\Dados_Limpos\
# Precisamos de recuar 2 pastas (Sitte -> Codigos) para chegar a "CD-Att".
# BASE_DIR.parent volta uma pasta. BASE_DIR.parent.parent volta duas pastas.
RAIZ_DO_PROJETO = BASE_DIR.parent.parent 

# Agora construímos o caminho até ao CSV de forma que funcione em qualquer PC (Windows, Mac, Linux)
CAMINHO_VLR = RAIZ_DO_PROJETO / "CSV" / "Dados_Limpos" / "01_vlr_matches_limpo.csv"

def preparar_dados():
    print("1. Carregando dados...")
    
    # Verificação de segurança antes de tentar abrir o ficheiro
    if not CAMINHO_VLR.exists():
        raise FileNotFoundError(f"Erro: O ficheiro não foi encontrado no caminho: {CAMINHO_VLR}")
        
    df = pd.read_csv(CAMINHO_VLR)
    df.columns = df.columns.str.strip()
    
    # Limpeza básica e conversão de tipos
    if 'KAST%' in df.columns:
        df['KAST%'] = df['KAST%'].astype(str).str.replace('%', '').astype(float)
        
    # Preencher valores nulos com 0 para evitar erros matemáticos
    df = df.fillna(0)
    
    print("2. Criando Variáveis Preditoras (Features) e Alvo (Target)...")
    # A Variável Alvo (Y): 1 para Vitória, 0 para Derrota
    # Assumimos a vitória se os Rounds Ganhos forem maiores que os Perdidos
    df['Vitoria'] = np.where(df['Rounds_Ganhos'] > df['Rounds_Perdidos'], 1, 0)
    
    # Criar variáveis táticas derivadas (Feature Engineering)
    df['Diferenca_FK_FD'] = df['FK'] - df['FD']
    df['KD_Ratio'] = np.where(df['D'] > 0, df['K'] / df['D'], df['K'])
    
    # Selecionar as colunas que os modelos vão estudar (Variáveis Independentes - X)
    features = ['Rating', 'ACS', 'KAST%', 'Diferenca_FK_FD', 'KD_Ratio', 'A']
    
    X = df[features]
    y = df['Vitoria']
    
    return X, y, features

def treinar_e_avaliar():
    X, y, nomes_features = preparar_dados()
    
    print("3. Separando dados de Treino (80%) e Teste (20%)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Inicializar os 3 algoritmos
    modelos = {
        "Regressao_Logistica": LogisticRegression(max_iter=1000),
        "Random_Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    }
    
    resultados_modelos = {}
    importancias_xgboost = None
    
    print("4. Iniciando Treino dos Modelos...")
    for nome, modelo in modelos.items():
        # Treinar o modelo
        modelo.fit(X_train, y_train)
        
        # Fazer previsões no conjunto de teste
        previsoes = modelo.predict(X_test)
        
        # Calcular a precisão
        precisao = accuracy_score(y_test, previsoes)
        print(f"--- {nome} ---")
        print(f"Acurácia: {precisao * 100:.2f}%")
        
        # Guardar o modelo treinado num ficheiro .pkl na mesma pasta deste script
        nome_ficheiro = f"modelo_{nome}.pkl"
        caminho_ficheiro_pkl = BASE_DIR / nome_ficheiro # Garante que salva no lugar certo
        
        with open(caminho_ficheiro_pkl, 'wb') as arquivo:
            pickle.dump(modelo, arquivo)
            
        resultados_modelos[nome] = precisao
        
        # Extrair o peso das variáveis do XGBoost
        if nome == "XGBoost":
            importancias_xgboost = pd.DataFrame({
                'Variavel': nomes_features,
                'Importancia': modelo.feature_importances_
            }).sort_values(by='Importancia', ascending=False)
            
    # Guardar a lista de features e a importância num ficheiro na mesma pasta do script
    caminho_features = BASE_DIR / "info_features.pkl"
    with open(caminho_features, 'wb') as arquivo:
        pickle.dump({'features': nomes_features, 'importancia_xgb': importancias_xgboost}, arquivo)
        
    print(f"\n5. Processo concluído. Modelos guardados com sucesso na pasta: {BASE_DIR}")
    print("\nImportância das Variáveis (XGBoost):")
    print(importancias_xgboost)

if __name__ == "__main__":
    treinar_e_avaliar()