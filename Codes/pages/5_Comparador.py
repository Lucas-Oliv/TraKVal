import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import os

from utils import carregar_dados_vlr

st.set_page_config(page_title="Modelos Preditivos e Avaliação", layout="wide")

st.title("Avaliação de Desempenho")
st.markdown("---")

@st.cache_resource
def carregar_modelos():
    modelos = {}
    ficheiros = {
        "Regressão Logística": "modelo_Regressao_Logistica.pkl",
        "Random Forest": "modelo_Random_Forest.pkl",
        "XGBoost": "modelo_XGBoost.pkl"
    }
    
    for nome, caminho in ficheiros.items():
        if os.path.exists(caminho):
            with open(caminho, 'rb') as arquivo:
                modelos[nome] = pickle.load(arquivo)
                
    info_features = None
    if os.path.exists("info_features.pkl"):
        with open("info_features.pkl", 'rb') as arquivo:
            info_features = pickle.load(arquivo)
            
    return modelos, info_features

modelos_carregados, info = carregar_modelos()
df_macro = carregar_dados_vlr()

if modelos_carregados and info and not df_macro.empty:
    
    # Pré-processamento dos dados reais para a calculadora
    if 'KAST%' in df_macro.columns and df_macro['KAST%'].dtype == object:
        df_macro['KAST%'] = df_macro['KAST%'].str.replace('%', '').astype(float)
        
    # ==========================================
    # CLASSIFICADOR DE DESEMPENHO REAL (CONSENSO)
    # ==========================================
    st.markdown("### Classificador de Desempenho (Jogador / Equipa)")
    st.write("Os modelos analisam as médias reais de um alvo na base de dados e prevêem a probabilidade dessas estatísticas resultarem em vitórias consistentes. O consenso entre os algoritmos garante uma maior precisão analítica.")
    
    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        tipo_analise = st.radio("Selecione o alvo da análise:", ["Jogador", "Equipa"], horizontal=True)
        
    with col_sel2:
        if tipo_analise == "Jogador":
            lista_alvos = sorted(df_macro['Jogador'].dropna().unique())
        else:
            lista_alvos = sorted(df_macro['Time'].dropna().unique())
            
        alvo_escolhido = st.selectbox(f"Selecione o(a) {tipo_analise}:", lista_alvos)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    if tipo_analise == "Jogador":
        dados_alvo = df_macro[df_macro['Jogador'] == alvo_escolhido]
    else:
        dados_alvo = df_macro[df_macro['Time'] == alvo_escolhido]
        
    if not dados_alvo.empty:
        media_rating = dados_alvo['Rating'].mean()
        media_acs = dados_alvo['ACS'].mean()
        media_kast = dados_alvo['KAST%'].mean()
        media_fk = dados_alvo['FK'].mean()
        media_fd = dados_alvo['FD'].mean()
        media_a = dados_alvo['A'].mean()
        
        total_k = dados_alvo['K'].sum()
        total_d = dados_alvo['D'].sum()
        media_kd = total_k / total_d if total_d > 0 else total_k
        
        diferenca_fk_fd = media_fk - media_fd
        
        ordem_features = info['features']
        vetor_alvo = pd.DataFrame([{
            'Rating': media_rating,
            'ACS': media_acs,
            'KAST%': media_kast,
            'Diferenca_FK_FD': diferenca_fk_fd,
            'KD_Ratio': media_kd,
            'A': media_a
        }])[ordem_features]
        
        # Função auxiliar para classificação visual
        def classificar_resultado(probabilidade):
            if probabilidade >= 65:
                return "Nível Elite (Carrying)", "#00FF00"
            elif probabilidade >= 50:
                return "Sólido (Impacto Positivo)", "#00BFFF"
            elif probabilidade >= 40:
                return "Abaixo da Média", "#FFA500"
            else:
                return "Crítico (Impacto Negativo)", "#FF0000"

        # Calcular previsões dos 3 modelos
        prob_xgb = modelos_carregados["XGBoost"].predict_proba(vetor_alvo)[0][1] * 100
        prob_rf = modelos_carregados["Random Forest"].predict_proba(vetor_alvo)[0][1] * 100
        prob_lr = modelos_carregados["Regressão Logística"].predict_proba(vetor_alvo)[0][1] * 100
        
        col_res1, col_res2, col_res3 = st.columns(3)
        
        # Bloco XGBoost (Principal)
        with col_res1:
            classe_xgb, cor_xgb = classificar_resultado(prob_xgb)
            st.markdown(f"**Previsão XGBoost** (Maior Precisão)")
            st.markdown(f"<h2 style='color: {cor_xgb}; margin-top: 0px;'>{prob_xgb:.1f}%</h2>", unsafe_allow_html=True)
            st.write(f"**Classe:** {classe_xgb}")
            st.progress(int(prob_xgb))
            
        # Bloco Random Forest
        with col_res2:
            classe_rf, cor_rf = classificar_resultado(prob_rf)
            st.markdown(f"**Previsão Random Forest**")
            st.markdown(f"<h2 style='color: {cor_rf}; margin-top: 0px;'>{prob_rf:.1f}%</h2>", unsafe_allow_html=True)
            st.write(f"**Classe:** {classe_rf}")
            st.progress(int(prob_rf))

        # Bloco Regressão Logística
        with col_res3:
            classe_lr, cor_lr = classificar_resultado(prob_lr)
            st.markdown(f"**Previsão Reg. Logística** (Baseline)")
            st.markdown(f"<h2 style='color: {cor_lr}; margin-top: 0px;'>{prob_lr:.1f}%</h2>", unsafe_allow_html=True)
            st.write(f"**Classe:** {classe_lr}")
            st.progress(int(prob_lr))

    st.markdown("---")
    
    # ==========================================
    # DESEMPENHO DOS MODELOS E FEATURE IMPORTANCE
    # ==========================================
    st.markdown("### Importância das Variáveis (Feature Importance)")
    
    col_grafico, col_texto = st.columns([2, 1])
    
    with col_grafico:
        df_importancia = info['importancia_xgb']
        traducao = {
            'KD_Ratio': 'Rácio K/D (Sobrevivência)',
            'A': 'Assistências (Trabalho de Equipa)',
            'KAST%': 'KAST% (Consistência)',
            'ACS': 'Pontuação de Combate (ACS)',
            'Diferenca_FK_FD': 'Saldo de First Kills',
            'Rating': 'VLR Rating Bruto'
        }
        df_importancia['Nome_Apresentacao'] = df_importancia['Variavel'].map(traducao)
        
        fig_imp = px.bar(
            df_importancia.sort_values(by='Importancia', ascending=True), 
            x='Importancia', 
            y='Nome_Apresentacao', 
            orientation='h',
            labels={'Importancia': 'Peso na Decisão do Modelo', 'Nome_Apresentacao': 'Métrica'},
            color='Importancia',
            color_continuous_scale='viridis'
        )
        fig_imp.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig_imp, use_container_width=True)
        
    with col_texto:
        st.markdown("**Precisão no Teste (Acurácia)**")
        st.metric("1. XGBoost", "80.61%")
        st.metric("2. Random Forest", "79.50%")
        st.metric("3. Regressão Logística", "76.62%")
        
        st.info("O modelo prova que a sobrevivência (K/D) e o suporte (Assistências) são os indicadores mais fortes de uma equipa vencedora, superando métricas tradicionais de confronto direto como o ACS.")

    st.markdown("---")
    
    # ==========================================
    # SIMULADOR PREDITIVO INTERATIVO
    # ==========================================
    st.markdown("### Simulador de Cenários Teóricos")
    st.write("Ajuste as métricas abaixo para simular o impacto de diferentes estilos de jogo na probabilidade de vitória.")
    
    col_sim1, col_sim2, col_sim3 = st.columns(3)
    
    with col_sim1:
        sim_kd = st.slider("Rácio K/D", min_value=0.2, max_value=2.5, value=1.0, step=0.1)
        sim_ast = st.slider("Média de Assistências", min_value=0, max_value=25, value=7, step=1)
        
    with col_sim2:
        sim_kast = st.slider("KAST %", min_value=30, max_value=100, value=70, step=1)
        sim_acs = st.slider("Pontuação de Combate (ACS)", min_value=100, max_value=350, value=200, step=5)
        
    with col_sim3:
        sim_fkfd = st.slider("Saldo de First Kills (FK - FD)", min_value=-10, max_value=10, value=0, step=1)
        sim_rating = st.slider("VLR Rating", min_value=0.5, max_value=1.8, value=1.0, step=0.05)
        
    dados_simulacao = pd.DataFrame([{
        'Rating': sim_rating,
        'ACS': sim_acs,
        'KAST%': sim_kast,
        'Diferenca_FK_FD': sim_fkfd,
        'KD_Ratio': sim_kd,
        'A': sim_ast
    }])[ordem_features]
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_res1_sim, col_res2_sim, col_res3_sim = st.columns(3)
    
    def exibir_probabilidade_simulador(nome_modelo, modelo_obj, coluna):
        probabilidades = modelo_obj.predict_proba(dados_simulacao)[0]
        prob_vitoria = probabilidades[1] * 100
        
        cor = "green" if prob_vitoria >= 50 else "red"
        
        with coluna:
            st.markdown(f"**{nome_modelo}**")
            st.markdown(f"<h2 style='color: {cor}; margin-top: 0px;'>{prob_vitoria:.1f}%</h2>", unsafe_allow_html=True)
            st.progress(int(prob_vitoria))

    exibir_probabilidade_simulador("XGBoost", modelos_carregados["XGBoost"], col_res1_sim)
    exibir_probabilidade_simulador("Random Forest", modelos_carregados["Random Forest"], col_res2_sim)
    exibir_probabilidade_simulador("Regressão Logística", modelos_carregados["Regressão Logística"], col_res3_sim)

else:
    st.warning("Modelos preditivos ou dados não encontrados. Execute o script `pipeline_ml.py` no terminal para gerar os ficheiros `.pkl`.")