import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from utils import carregar_dados_mestres, carregar_dados_vlr

st.set_page_config(page_title="Perfil de Jogadores", layout="wide")

st.title("Perfil de Jogadores e Scouting Avançado")
st.markdown("---")

df_micro = carregar_dados_mestres()
df_macro = carregar_dados_vlr()

DICIONARIO_FUNCOES = {
    'Jett': 'Duelista', 'Phoenix': 'Duelista', 'Reyna': 'Duelista', 'Raze': 'Duelista', 'Yoru': 'Duelista', 'Neon': 'Duelista', 'Iso': 'Duelista', 'Waylay': 'Duelista',
    'Brimstone': 'Controlador', 'Viper': 'Controlador', 'Omen': 'Controlador', 'Astra': 'Controlador', 'Harbor': 'Controlador', 'Clove': 'Controlador',
    'Sova': 'Iniciador', 'Breach': 'Iniciador', 'Skye': 'Iniciador', 'KAY/O': 'Iniciador', 'Kayo': 'Iniciador', 'Fade': 'Iniciador', 'Gekko': 'Iniciador', 'Tejo': 'Iniciador',
    'Sage': 'Sentinela', 'Cypher': 'Sentinela', 'Killjoy': 'Sentinela', 'Chamber': 'Sentinela', 'Deadlock': 'Sentinela', 'Vyse': 'Sentinela', 'Veto': 'Sentinela'
}

def classificar_regiao(nome_torneio):
    nome = str(nome_torneio).lower()
    if 'americas' in nome: return 'Americas'
    if 'emea' in nome: return 'EMEA'
    if 'pacific' in nome: return 'Pacific'
    if 'china' in nome: return 'China'
    if 'champions' in nome: return 'Champions'
    if 'masters' in nome: return 'Masters'
    return 'Outros'

if not df_micro.empty and not df_macro.empty:
    
    # Processamento inicial de Região e Data/Ano
    df_macro['Regiao_Macro'] = df_macro['Torneio'].apply(classificar_regiao)
    
    if 'Data' in df_macro.columns:
        df_macro['Data_Parse'] = pd.to_datetime(df_macro['Data'], errors='coerce')
        df_macro['Ano'] = df_macro['Data_Parse'].dt.year.fillna(0).astype(int)
    else:
        df_macro['Ano'] = 0

    # Correção Robusta do KAST% (Resolve o bug do "1%")
    if 'KAST%' in df_macro.columns:
        df_macro['KAST_num'] = df_macro['KAST%'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        df_macro['KAST_num'] = pd.to_numeric(df_macro['KAST_num'], errors='coerce').fillna(0)
        if df_macro['KAST_num'].max() > 0 and df_macro['KAST_num'].max() <= 1.5:
            df_macro['KAST%'] = df_macro['KAST_num'] * 100
        else:
            df_macro['KAST%'] = df_macro['KAST_num']

    # Mapeamento prévio de Funções para os Filtros
    df_macro['Agente_Limpo'] = df_macro['Agente'].astype(str).str.strip().str.title().replace('Kay/O', 'KAY/O')
    df_macro['Funcao_Filtro'] = df_macro['Agente_Limpo'].map(DICIONARIO_FUNCOES).fillna('Desconhecido')
        
    # ==========================================
    # FILTROS HIERÁRQUICOS ATUALIZADOS
    # ==========================================
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        lista_regioes = ["Todas"] + sorted(df_macro['Regiao_Macro'].unique().tolist())
        regiao_escolhida = st.selectbox("Região:", lista_regioes)
        
    df_f1 = df_macro if regiao_escolhida == "Todas" else df_macro[df_macro['Regiao_Macro'] == regiao_escolhida]
    
    with col_f2:
        # Substituímos o Torneio pela Função
        lista_funcoes = ["Todas", "Duelista", "Iniciador", "Controlador", "Sentinela"]
        funcao_escolhida = st.selectbox("Função Tática:", lista_funcoes)
        
    df_f2 = df_f1 if funcao_escolhida == "Todas" else df_f1[df_f1['Funcao_Filtro'] == funcao_escolhida]

    with col_f3:
        anos_validos = df_f2[df_f2['Ano'] > 0]['Ano'].unique().tolist()
        if anos_validos:
            lista_anos = ["Todos"] + sorted(anos_validos, reverse=True)
        else:
            lista_anos = ["Todos"]
            
        ano_escolhido = st.selectbox("Ano:", lista_anos)

    df_f3 = df_f2 if ano_escolhido == "Todos" else df_f2[df_f2['Ano'] == ano_escolhido]
        
    with col_f4:
        lista_jogadores = sorted(df_f3['Jogador'].dropna().unique())
        if not lista_jogadores:
            st.warning("Nenhum jogador encontrado com estes filtros.")
            st.stop()
        jogador_escolhido = st.selectbox("Jogador Alvo:", lista_jogadores)
        
    vlr_jogador = df_f3[df_f3['Jogador'] == jogador_escolhido]
    micro_jogador = df_micro[df_micro['Eliminador'] == jogador_escolhido]
    historico_completo = df_macro[df_macro['Jogador'] == jogador_escolhido].copy()
    
    if not vlr_jogador.empty:
        
        # ==========================================
        # CÁLCULO DA FUNÇÃO PRINCIPAL
        # ==========================================
        agentes_jogados = vlr_jogador['Agente'].dropna().tolist()
        agentes_limpos = [str(ag).strip().title() if str(ag).strip().upper() != 'KAY/O' else 'KAY/O' for ag in agentes_jogados]
        funcoes_jogadas = [DICIONARIO_FUNCOES.get(ag, 'Desconhecido') for ag in agentes_limpos]
        agentes_unicos = set(agentes_limpos)
        funcoes_unicas = set([f for f in funcoes_jogadas if f != 'Desconhecido'])
        
        if len(agentes_unicos) > 4 and len(funcoes_unicas) > 1:
            funcao_principal = "Flex"
        elif funcoes_jogadas:
            funcao_principal = max(set(funcoes_jogadas), key=funcoes_jogadas.count)
        else:
            funcao_principal = "Não informada"
            
        time_atual = "Desconhecido"
        linha_tempo_str = "Sem histórico detalhado"
        
        if not historico_completo.empty and 'Ano' in historico_completo.columns:
            historico_completo = historico_completo.sort_values(by='Data_Parse', ascending=False)
            time_atual = historico_completo['Time'].iloc[0]
            historico_valido = historico_completo[historico_completo['Ano'] > 0]
            
            if not historico_valido.empty:
                agrupamento_times = historico_valido.groupby('Time').agg(
                    Ano_Min=('Ano', 'min'), Ano_Max=('Ano', 'max'), Data_Recente=('Data_Parse', 'max')
                ).sort_values('Data_Recente', ascending=False).reset_index()
                lista_historico = [f"{row['Time']} ({row['Ano_Min']}" if row['Ano_Min'] == row['Ano_Max'] else f"{row['Time']} ({row['Ano_Min']}-{row['Ano_Max']})" for _, row in agrupamento_times.iterrows()]
                linha_tempo_str = " -> ".join(lista_historico)

        # ==========================================
        # CABEÇALHO DO JOGADOR
        # ==========================================
        st.markdown(f"### {jogador_escolhido}")
        st.markdown(f"**Equipa Atual:** {time_atual} | **Função Nominal:** {funcao_principal}")
        st.info(f"**Trajetória de Carreira:** {linha_tempo_str}")
        
        # ==========================================
        # ESTATÍSTICAS MACRO (VLR)
        # ==========================================
        rating_medio = vlr_jogador['Rating'].mean()
        acs_medio = vlr_jogador['ACS'].mean()
        total_k = vlr_jogador['K'].sum()
        total_d = vlr_jogador['D'].sum()
        total_a = vlr_jogador['A'].sum()
        kd_ratio = total_k / total_d if total_d > 0 else total_k
        kast_medio = vlr_jogador['KAST%'].mean() if 'KAST%' in vlr_jogador.columns else 0
            
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("VLR Rating", f"{rating_medio:.2f}")
        col2.metric("ACS", f"{acs_medio:.0f}")
        col3.metric("K / D / A", f"{total_k} / {total_d} / {total_a}")
        col4.metric("K/D Ratio", f"{kd_ratio:.2f}")
        col5.metric("KAST%", f"{kast_medio:.0f}%")

        st.markdown("---")

        # ==========================================
        # PERFIL COMPORTAMENTAL (HEURÍSTICAS)
        # ==========================================
        st.markdown("### Perfil Comportamental (Heurísticas Avançadas)")
        
        col_h1, col_h2, col_h3, col_h4 = st.columns(4)

        with col_h1:
            std_acs = vlr_jogador['ACS'].std()
            if pd.isna(std_acs) or len(vlr_jogador) < 3:
                label_consistencia = "Dados Insuficientes"
                cor_cons = "gray"
            elif std_acs < 35:
                label_consistencia = "Consistente (Baixa Variância)"
                cor_cons = "green"
            elif std_acs > 60:
                label_consistencia = "Volátil (Explosivo)"
                cor_cons = "red"
            else:
                label_consistencia = "Variância Normal"
                cor_cons = "blue"
                
            st.markdown("**Índice de Consistência**")
            st.markdown(f"<h4 style='color: {cor_cons}; margin-top: 0px;'>{label_consistencia}</h4>", unsafe_allow_html=True)
            st.write(f"Desvio Padrão: ±{std_acs:.1f} ACS" if pd.notna(std_acs) else "Mínimo de 3 partidas exigido.")

        with col_h2:
            media_a = vlr_jogador['A'].mean()
            if acs_medio > 200 and kast_medio < 68 and media_a < 5:
                label_isolamento = "Lobo Solitário (Lurker)"
                cor_iso = "purple"
            elif kast_medio >= 74 and media_a >= 6:
                label_isolamento = "Jogador de Sistema (Pack)"
                cor_iso = "green"
            else:
                label_isolamento = "Estilo Equilibrado"
                cor_iso = "blue"
                
            st.markdown("**Índice de Isolamento**")
            st.markdown(f"<h4 style='color: {cor_iso}; margin-top: 0px;'>{label_isolamento}</h4>", unsafe_allow_html=True)
            st.write("Calculado via KAST%, Assistências e Dano.")

        with col_h3:
            map_ratings = vlr_jogador.groupby('Mapa')['Rating'].mean()
            if len(map_ratings) >= 3:
                delta_map = map_ratings.max() - map_ratings.min()
                if delta_map < 0.15:
                    label_mapa = "Generalista Tático"
                    cor_map = "green"
                elif delta_map > 0.30:
                    label_mapa = "Especialista de Mapa"
                    cor_map = "orange"
                else:
                    label_mapa = "Adaptabilidade Padrão"
                    cor_map = "blue"
            else:
                label_mapa = "Amostra Pequena"
                delta_map = 0
                cor_map = "gray"
                
            st.markdown("**Domínio de Map Pool**")
            st.markdown(f"<h4 style='color: {cor_map}; margin-top: 0px;'>{label_mapa}</h4>", unsafe_allow_html=True)
            st.write(f"Delta de Performance: {delta_map:.2f} Rating" if len(map_ratings) >= 3 else "Mínimo de 3 mapas.")

        with col_h4:
            media_fk = vlr_jogador['FK'].mean()
            
            if len(vlr_jogador) >= 5 and 'Rounds_Ganhos' in vlr_jogador.columns:
                if media_fk >= 2.5 or funcao_principal == 'Duelista':
                    st.markdown("**Qualidade de Abertura (Entry)**")
                    corr_win = vlr_jogador['FK'].corr(vlr_jogador['Rounds_Ganhos'])
                    if pd.isna(corr_win):
                        st.markdown("<h4 style='color: gray; margin-top: 0px;'>Neutro</h4>", unsafe_allow_html=True)
                    elif corr_win > 0.40:
                        st.markdown("<h4 style='color: green; margin-top: 0px;'>Entry de Alto Impacto</h4>", unsafe_allow_html=True)
                    elif corr_win < 0.15:
                        st.markdown("<h4 style='color: red; margin-top: 0px;'>Entry Vazio (Baixa Conv.)</h4>", unsafe_allow_html=True)
                    else:
                        st.markdown("<h4 style='color: blue; margin-top: 0px;'>Impacto Moderado</h4>", unsafe_allow_html=True)
                    st.write(f"Correlação FK/Vitória: {corr_win:.2f}" if pd.notna(corr_win) else "Dados insuficientes.")

                elif media_a >= 6.0 or funcao_principal == 'Iniciador':
                    st.markdown("**Eficiência de Suporte**")
                    corr_win = vlr_jogador['A'].corr(vlr_jogador['Rounds_Ganhos'])
                    if pd.isna(corr_win):
                        st.markdown("<h4 style='color: gray; margin-top: 0px;'>Neutro</h4>", unsafe_allow_html=True)
                    elif corr_win > 0.45:
                        st.markdown("<h4 style='color: green; margin-top: 0px;'>Motor de Equipa</h4>", unsafe_allow_html=True)
                    elif corr_win < 0.20:
                        st.markdown("<h4 style='color: red; margin-top: 0px;'>Suporte Ineficiente</h4>", unsafe_allow_html=True)
                    else:
                        st.markdown("<h4 style='color: blue; margin-top: 0px;'>Suporte Padrão</h4>", unsafe_allow_html=True)
                    st.write(f"Correlação Ast/Vitória: {corr_win:.2f}" if pd.notna(corr_win) else "Dados insuficientes.")

                else:
                    st.markdown("**Resiliência Tática (Âncora)**")
                    corr_win = vlr_jogador['KAST%'].corr(vlr_jogador['Rounds_Ganhos'])
                    if pd.isna(corr_win):
                        st.markdown("<h4 style='color: gray; margin-top: 0px;'>Neutro</h4>", unsafe_allow_html=True)
                    elif corr_win > 0.50:
                        st.markdown("<h4 style='color: green; margin-top: 0px;'>Pilar de Estabilidade</h4>", unsafe_allow_html=True)
                    elif corr_win < 0.20:
                        st.markdown("<h4 style='color: red; margin-top: 0px;'>Impacto Passivo</h4>", unsafe_allow_html=True)
                    else:
                        st.markdown("<h4 style='color: blue; margin-top: 0px;'>Sobrevivência Útil</h4>", unsafe_allow_html=True)
                    st.write(f"Correlação KAST/Vitória: {corr_win:.2f}" if pd.notna(corr_win) else "Dados insuficientes.")
            else:
                st.markdown("**Métrica de Impacto Específica**")
                st.markdown("<h4 style='color: gray; margin-top: 0px;'>Amostra Pequena</h4>", unsafe_allow_html=True)
                st.write("Mínimo de 5 partidas exigido.")

        st.markdown("---")
        
        # ==========================================
        # CIÊNCIA DE DADOS: CLUSTERIZAÇÃO E SIMILARIDADE
        # ==========================================
        st.markdown("### Perfilagem e Scouting")
        
        estilo_arma = "Misto"
        if not micro_jogador.empty and 'Arma' in micro_jogador.columns:
            armas_contagem = micro_jogador['Arma'].value_counts()
            if not armas_contagem.empty:
                arma_principal = str(armas_contagem.index[0]).upper()
                rifles = ['VANDAL', 'PHANTOM', 'BULLDOG', 'GUARDIAN']
                snipers = ['OPERATOR', 'OUTLAW', 'MARSHAL']
                
                if arma_principal in rifles:
                    estilo_arma = "Foco em Rifle"
                elif arma_principal in snipers:
                    estilo_arma = "Foco em Sniper"
                else:
                    estilo_arma = "Misto/Eco"

        df_agrupado = df_f3.groupby('Jogador').agg({
            'Rating': 'mean', 'ACS': 'mean', 'KAST%': 'mean',
            'K': 'sum', 'D': 'sum', 'A': 'mean', 'FK': 'mean', 'FD': 'mean'
        }).reset_index()
        
        df_agrupado['KD_Ratio'] = np.where(df_agrupado['D'] > 0, df_agrupado['K'] / df_agrupado['D'], df_agrupado['K'])
        df_agrupado['Diferenca_FK_FD'] = df_agrupado['FK'] - df_agrupado['FD']
        
        features_ia = ['ACS', 'KAST%', 'KD_Ratio', 'Diferenca_FK_FD', 'A']
        X_cluster = df_agrupado[features_ia].fillna(0)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_cluster)
        
        if len(df_agrupado) >= 4:
            kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
            df_agrupado['Cluster'] = kmeans.fit_predict(X_scaled)
            
            medias_cluster = df_agrupado.groupby('Cluster')['ACS'].mean().sort_values(ascending=False).index
            labels_cluster = {
                medias_cluster[0]: "Agressivo (Entry Fragger)",
                medias_cluster[1]: "Flexível (Multikill)",
                medias_cluster[2]: "Suporte (Foco em Utilidade)",
                medias_cluster[3]: "Passivo (Âncora/Lurker)"
            }
            df_agrupado['Arquetipo'] = df_agrupado['Cluster'].map(labels_cluster)
            
            arquetipo_base = df_agrupado[df_agrupado['Jogador'] == jogador_escolhido]['Arquetipo'].values[0]
            arquetipo_final = f"{arquetipo_base} | {estilo_arma}"
            
            matriz_similaridade = cosine_similarity(X_scaled)
            idx_jogador = df_agrupado[df_agrupado['Jogador'] == jogador_escolhido].index[0]
            scores_sim = list(enumerate(matriz_similaridade[idx_jogador]))
            scores_sim = sorted(scores_sim, key=lambda x: x[1], reverse=True)
            
            top_3_idx = [i[0] for i in scores_sim[1:4]]
            df_similares = df_agrupado.iloc[top_3_idx].copy()
            df_similares['Similaridade'] = [f"{scores_sim[1][1]*100:.1f}%", f"{scores_sim[2][1]*100:.1f}%", f"{scores_sim[3][1]*100:.1f}%"]
            
            col_ia1, col_ia2 = st.columns([1, 1.5])
            
            with col_ia1:
                st.markdown("**Arquétipo Real (Clusterização K-Means)**")
                st.write("O algoritmo avaliou o comportamento estatístico e cruzou com os dados balísticos locais, classificando o estilo operacional deste jogador como:")
                st.markdown(f"#### {arquetipo_final}")
                
                fig_cluster = px.scatter(
                    df_agrupado, x='ACS', y='KAST%', color='Arquetipo', hover_data=['Jogador'],
                    title="Posicionamento no Ecossistema do Torneio"
                )
                fig_cluster.add_trace(go.Scatter(
                    x=[acs_medio], y=[kast_medio], mode='markers',
                    marker=dict(size=15, color='white', line=dict(width=2, color='black')),
                    name=jogador_escolhido
                ))
                fig_cluster.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", margin=dict(t=30, b=0))
                st.plotly_chart(fig_cluster, use_container_width=True)
                
            with col_ia2:
                st.markdown("**Motor de Similaridade (Scouting de Substitutos)**")
                st.write(f"Comparando a assinatura estatística de **{jogador_escolhido}** com todos os outros jogadores através do cálculo de similaridade de cossenos, os perfis mais idênticos são:")
                
                tabela_scout = df_similares[['Jogador', 'Similaridade', 'ACS', 'KD_Ratio', 'KAST%', 'Arquetipo']].rename(columns={'KD_Ratio': 'K/D'})
                tabela_scout['ACS'] = tabela_scout['ACS'].round(0).astype(int)
                tabela_scout['K/D'] = tabela_scout['K/D'].round(2)
                tabela_scout['KAST%'] = tabela_scout['KAST%'].round(0).astype(int).astype(str) + "%"
                
                st.dataframe(tabela_scout, use_container_width=True, hide_index=True)
        else:
            st.info("Dados insuficientes para rodar o algoritmo de clusterização.")

        st.markdown("---")
        
        # ==========================================
        # COMBATE LOCAL E TRADE KILLS (MICRO)
        # ==========================================
        st.markdown("### Disciplina Tática e Combate Local (Micro)")
        
        # Removido o gráfico de vítimas. Layout ajustado para 2 colunas amplas.
        col_micro1, col_micro2 = st.columns(2)
        
        with col_micro1:
            st.markdown("**Armas Preferidas**")
            if not micro_jogador.empty:
                armas_contagem = micro_jogador['Arma'].value_counts().head(5).reset_index()
                armas_contagem.columns = ['Arma', 'Abates']
                fig_armas = px.bar(armas_contagem, x='Arma', y='Abates', color='Arma', text='Abates')
                fig_armas.update_layout(showlegend=False, paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", margin=dict(t=0, b=0))
                st.plotly_chart(fig_armas, use_container_width=True)
            else:
                st.write("Sem dados de armas.")
                
        with col_micro2:
            st.markdown("**Cinética de Trade Kills**")
            if not micro_jogador.empty and 'Trade_Kill' in micro_jogador.columns:
                total_abates_micro = len(micro_jogador)
                trades_feitas = micro_jogador['Trade_Kill'].sum()
                
                if isinstance(trades_feitas, str):
                    trades_feitas = len(micro_jogador[micro_jogador['Trade_Kill'] == True])
                
                taxa_trade = (trades_feitas / total_abates_micro * 100) if total_abates_micro > 0 else 0
                
                st.metric("Total de Trade Kills", int(trades_feitas))
                st.metric("Taxa de Abates em Trade", f"{taxa_trade:.1f}%")
                st.write("Esta métrica indica a percentagem de abates que o jogador executou com o propósito direto de vingar um colega abatido recentemente, medindo a sua disciplina em jogar coletivamente.")
            else:
                st.write("Dados de Trade Kills não disponíveis na telemetria atual.")

        st.markdown("---")
        
        # ==========================================
        # DESEMPENHO POR MAPA E AGENTES
        # ==========================================
        st.markdown("### Desempenho por Mapa")
        col_mapa1, col_mapa2 = st.columns([1, 1.5])
        
        with col_mapa1:
            st.markdown("**Top 3 Agentes por Mapa**")
            agentes_mapa = vlr_jogador.groupby(['Mapa', 'Agente']).size().reset_index(name='Partidas')
            agentes_mapa = agentes_mapa.sort_values(['Mapa', 'Partidas'], ascending=[True, False])
            top3_agentes = agentes_mapa.groupby('Mapa').head(3)
            st.dataframe(top3_agentes, use_container_width=True, hide_index=True)
            
        with col_mapa2:
            st.markdown("**Performance por Mapa (K/D/A)**")
            mapas_contagem = vlr_jogador.groupby('Mapa')[['K', 'D', 'A']].sum().reset_index()
            partidas_mapa = vlr_jogador.groupby('Mapa').size().reset_index(name='Vezes Jogado')
            mapas_contagem = pd.merge(mapas_contagem, partidas_mapa, on='Mapa')
            mapas_contagem['Mapa_Label'] = mapas_contagem['Mapa'] + " (" + mapas_contagem['Vezes Jogado'].astype(str) + ")"
            
            fig_mapas = px.bar(
                mapas_contagem, 
                x='Mapa_Label', 
                y=['K', 'D', 'A'], 
                barmode='group',
                labels={'value': 'Total', 'Mapa_Label': 'Mapa (Partidas)', 'variable': 'Métrica'}
            )
            fig_mapas.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", margin=dict(t=0, b=0), legend_title="")
            st.plotly_chart(fig_mapas, use_container_width=True)

    else:
        st.warning("Jogador não encontrado para os filtros selecionados.")
else:
    st.error("Erro: Não foi possível carregar os dados. Verifique os ficheiros CSV.")