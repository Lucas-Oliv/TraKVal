import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from utils import carregar_dados_mestres, carregar_dados_vlr

st.set_page_config(page_title="Comparação de Mercado", layout="wide")

st.title("Análise Comparativa de Jogadores")
st.markdown("---")

df_micro = carregar_dados_mestres()
df_macro = carregar_dados_vlr()

DICIONARIO_FUNCOES = {
    'Jett': 'Duelista', 'Phoenix': 'Duelista', 'Reyna': 'Duelista', 'Raze': 'Duelista', 'Yoru': 'Duelista', 'Neon': 'Duelista', 'Iso': 'Duelista', 'Waylay': 'Duelista',
    'Brimstone': 'Controlador', 'Viper': 'Controlador', 'Omen': 'Controlador', 'Astra': 'Controlador', 'Harbor': 'Controlador', 'Clove': 'Controlador',
    'Sova': 'Iniciador', 'Breach': 'Iniciador', 'Skye': 'Iniciador', 'KAY/O': 'Iniciador', 'Kayo': 'Iniciador', 'Fade': 'Iniciador', 'Gekko': 'Iniciador', 'Tejo': 'Iniciador',
    'Sage': 'Sentinela', 'Cypher': 'Sentinela', 'Killjoy': 'Sentinela', 'Chamber': 'Sentinela', 'Deadlock': 'Sentinela', 'Vyse': 'Sentinela', 'Veto': 'Sentinela'
}

if not df_macro.empty:
    
    if 'KAST%' in df_macro.columns:
        df_macro['KAST_num'] = df_macro['KAST%'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        df_macro['KAST_num'] = pd.to_numeric(df_macro['KAST_num'], errors='coerce').fillna(0)
        if df_macro['KAST_num'].max() > 0 and df_macro['KAST_num'].max() <= 1.5:
            df_macro['KAST%'] = df_macro['KAST_num'] * 100
        else:
            df_macro['KAST%'] = df_macro['KAST_num']
        
    lista_jogadores = sorted(df_macro['Jogador'].dropna().unique())
    
    # ==========================================
    # SELETOR PRÉVIO MULTIJOGADOR
    # ==========================================
    st.markdown("### Seleção de Atletas")
    st.write("Selecione dois ou mais jogadores no campo abaixo para gerar o relatório estatístico e o cruzamento de Agent Pool.")
    
    jogadores_selecionados = st.multiselect(
        "Jogadores em Análise:", 
        lista_jogadores,
        placeholder="Selecione os atletas..."
    )
    
    if len(jogadores_selecionados) >= 2:
        
        # ==========================================
        # CÁLCULO DE ESTATÍSTICAS AVANÇADAS
        # ==========================================
        def calcular_metricas(nome_jogador):
            df_jogador = df_macro[df_macro['Jogador'] == nome_jogador]
            if df_jogador.empty: 
                return {"Rating": 0, "ACS": 0, "K/D Ratio": 0, "KAST (%)": 0, "Kills Per Round (KPR)": 0, "Saldo FK/FD": 0, "Assistências": 0}
            
            rating = df_jogador['Rating'].mean()
            acs = df_jogador['ACS'].mean()
            kast = df_jogador['KAST%'].mean()
            
            total_k = df_jogador['K'].sum()
            total_d = df_jogador['D'].sum()
            kd = total_k / total_d if total_d > 0 else total_k
            
            if 'Rounds_Ganhos' in df_jogador.columns and 'Rounds_Perdidos' in df_jogador.columns:
                total_rounds = df_jogador['Rounds_Ganhos'].sum() + df_jogador['Rounds_Perdidos'].sum()
                kpr = total_k / total_rounds if total_rounds > 0 else 0
            else:
                kpr = 0
                
            total_fk = df_jogador['FK'].sum()
            total_fd = df_jogador['FD'].sum()
            saldo_fkfd = total_fk - total_fd
            assist_media = df_jogador['A'].mean()
            
            return {
                "Rating": rating, 
                "ACS": acs, 
                "K/D Ratio": kd, 
                "KAST (%)": kast, 
                "Kills Per Round (KPR)": kpr, 
                "Saldo FK/FD": saldo_fkfd,
                "Assistências": assist_media
            }

        metricas_nomes = ["Rating", "ACS", "K/D Ratio", "KAST (%)", "Kills Per Round (KPR)", "Saldo FK/FD"]
        formatos = {
            "Rating": "{:.2f}", "ACS": "{:.1f}", "K/D Ratio": "{:.2f}", 
            "KAST (%)": "{:.1f}", "Kills Per Round (KPR)": "{:.2f}", "Saldo FK/FD": "{:.0f}"
        }
        
        dados_jogadores = {jog: calcular_metricas(jog) for jog in jogadores_selecionados}
        
        pontos = {jog: 0 for jog in jogadores_selecionados}
        destaques = {jog: [] for jog in jogadores_selecionados}
        
        for metrica in metricas_nomes:
            ranking_metrica = sorted(jogadores_selecionados, key=lambda x: dados_jogadores[x][metrica], reverse=True)
            
            lider = ranking_metrica[0]
            segundo = ranking_metrica[1]
            
            val_lider = dados_jogadores[lider][metrica]
            val_segundo = dados_jogadores[segundo][metrica]
            
            if val_lider > val_segundo:
                pontos[lider] += 1
                diff_absoluta = val_lider - val_segundo
                
                if metrica == "Saldo FK/FD":
                    texto_vantagem = f"+{diff_absoluta:.0f} abates líquidos"
                else:
                    pct_vantagem = (diff_absoluta / abs(val_segundo) * 100) if val_segundo != 0 else 0
                    texto_vantagem = f"+{pct_vantagem:.1f}%"
                
                fmt = formatos[metrica]
                str_lider = fmt.format(val_lider)
                str_segundo = fmt.format(val_segundo)
                
                texto_destaque = f"<div style='margin-bottom: 10px;'><span style='color: #4CAF50; font-weight: bold;'>✓ Maior {metrica} ({texto_vantagem})</span><br><span style='font-size: 0.85em; color: #888; margin-left: 20px;'><b>{str_lider}</b> vs {str_segundo} (2º classificado: {segundo})</span></div>"
                destaques[lider].append(texto_destaque)

        # ==========================================
        # INTERFACE DO CONFRONTO (VERSUS STYLE)
        # ==========================================
        st.markdown("<br><hr style='width: 100%; border-top: 2px solid #333;'>", unsafe_allow_html=True)
        
        titulo_confronto = " vs ".join([f"<span style='color: #fff;'>{j}</span>" for j in jogadores_selecionados])
        st.markdown(f"<h2 style='text-align: center;'>{titulo_confronto}</h2>", unsafe_allow_html=True)
        
        vencedor_geral = max(pontos, key=pontos.get)
        maior_pontuacao = pontos[vencedor_geral]
        
        lideres = [j for j in pontos if pontos[j] == maior_pontuacao]
        
        if len(lideres) == 1:
            st.markdown(f"<h4 style='text-align: center; color: #4CAF50;'>VENCEDOR DA COMPARAÇÃO: {vencedor_geral.upper()}</h4>", unsafe_allow_html=True)
        else:
            vencedor_desempate = max(lideres, key=lambda x: dados_jogadores[x]["Rating"])
            st.markdown(f"<h4 style='text-align: center; color: #4CAF50;'>VENCEDOR POR DESEMPATE: {vencedor_desempate.upper()}</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #FFC107; font-size: 0.9em; margin-top: -10px;'>O empate estatístico ({maior_pontuacao} a {maior_pontuacao}) foi resolvido utilizando o VLR Rating Global.</p>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # PERFIS DE ATUAÇÃO (Sempre Visível)
        # ==========================================
        st.markdown("### Perfis de Atuação (Playstyle)")
        st.markdown("<div style='background-color: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px;'>", unsafe_allow_html=True)
        
        for jogador in jogadores_selecionados:
            df_jog = df_macro[df_macro['Jogador'] == jogador]
            agentes_jog = df_jog['Agente'].dropna().astype(str).str.strip().str.title().replace('Kay/O', 'KAY/O').tolist()
            funcoes_jog = [DICIONARIO_FUNCOES.get(ag, 'Desconhecido') for ag in agentes_jog]
            
            # Identifica Função e Agente Principal
            funcao_real = max(set(funcoes_jog), key=funcoes_jog.count) if funcoes_jog else "Misto"
            agente_principal = max(set(agentes_jog), key=agentes_jog.count) if agentes_jog else "Variado"
            
            # Identifica o Melhor Mapa com o Agente Principal
            if agente_principal != "Variado":
                df_agente_pico = df_jog[df_jog['Agente'].str.contains(agente_principal, case=False, na=False)]
                if not df_agente_pico.empty:
                    mapa_destaque = df_agente_pico.groupby('Mapa')['Rating'].mean().idxmax()
                else:
                    mapa_destaque = df_jog.groupby('Mapa')['Rating'].mean().idxmax() if not df_jog.empty else "Variado"
            else:
                mapa_destaque = df_jog.groupby('Mapa')['Rating'].mean().idxmax() if not df_jog.empty else "Variado"
            
            # Identifica Arma Principal (df_micro)
            df_micro_jog = df_micro[df_micro['Eliminador'] == jogador]
            estilo_arma = "foco equilibrado"
            if not df_micro_jog.empty and 'Arma' in df_micro_jog.columns:
                armas_contagem = df_micro_jog['Arma'].value_counts()
                if not armas_contagem.empty:
                    arma_principal = str(armas_contagem.index[0]).upper()
                    rifles = ['VANDAL', 'PHANTOM', 'BULLDOG', 'GUARDIAN']
                    snipers = ['OPERATOR', 'OUTLAW', 'MARSHAL']
                    
                    if arma_principal in rifles:
                        estilo_arma = "especialista em Rifles"
                    elif arma_principal in snipers:
                        estilo_arma = "especialista em Snipers"
                    else:
                        estilo_arma = f"focado em {arma_principal.title()}"
            
            # Constrói o texto
            if funcao_real == 'Duelista':
                 texto_base = f"destaca-se pelo alto poder de fogo e impacto inicial, atuando como **Duelista**"
            elif funcao_real == 'Controlador':
                 texto_base = f"exerce o seu impacto através do domínio de mapa e utilidade tática, atuando como **Controlador**"
            elif funcao_real == 'Iniciador':
                 texto_base = f"atua na facilitação de jogadas e suporte primário, como **Iniciador**"
            elif funcao_real == 'Sentinela':
                 texto_base = f"sustenta o seu jogo na capacidade de retenção de espaço e defesa passiva, como **Sentinela**"
            else:
                 texto_base = f"apresenta um perfil tático **Flexível**, adaptando-se a múltiplos papéis"
                 
            st.markdown(f"🔹 **{jogador}** {texto_base}, sendo um {estilo_arma} (Assinatura: **{agente_principal}**, com pico de performance no mapa **{mapa_destaque}**).")
                 
        st.markdown("</div><br>", unsafe_allow_html=True)
        
        # ==========================================
        # GRÁFICO E LISTA DE VANTAGENS
        # ==========================================
        col_grafico, col_texto = st.columns([1.2, 1])
        
        cores_base = ['rgba(233, 30, 99, 1)', 'rgba(65, 105, 225, 1)', 'rgba(76, 175, 80, 1)', 'rgba(255, 152, 0, 1)', 'rgba(156, 39, 176, 1)']
        
        with col_grafico:
            fig = go.Figure()
            
            for idx, jogador in enumerate(jogadores_selecionados):
                valores_jogador = [dados_jogadores[jogador][m] for m in metricas_nomes]
                
                max_vals = []
                for m in metricas_nomes:
                    valores_todas_ops = [dados_jogadores[j][m] for j in jogadores_selecionados]
                    max_abs = max(abs(min(valores_todas_ops)), abs(max(valores_todas_ops))) if m == "Saldo FK/FD" else max(valores_todas_ops)
                    max_vals.append(max_abs if max_abs > 0 else 1)
                    
                norm_vals = [v / m if m > 0 else 0 for v, m in zip(valores_jogador, max_vals)]
                norm_vals = [max(0, v) for v in norm_vals] 
                
                norm_closed = norm_vals + [norm_vals[0]]
                categorias_closed = metricas_nomes + [metricas_nomes[0]]
                
                cor_atual = cores_base[idx % len(cores_base)]
                cor_preenchimento = cor_atual.replace(', 1)', ', 0.2)')
                
                fig.add_trace(go.Scatterpolar(
                    r=norm_closed, 
                    theta=categorias_closed, 
                    fill='toself',
                    name=jogador, 
                    line_color=cor_atual, 
                    fillcolor=cor_preenchimento
                ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=False, range=[0, 1.1])),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="#0e1117",
                margin=dict(t=20, b=40, l=40, r=40)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_texto:
            st.markdown("### Argumentos Analíticos (Vantagens)")
            st.write("Análise de superioridade direta de cada atleta face ao segundo melhor classificado na respetiva categoria.")
            
            abas_jogadores = st.tabs(jogadores_selecionados)
            
            for idx, tab in enumerate(abas_jogadores):
                jogador_tab = jogadores_selecionados[idx]
                with tab:
                    pts = pontos[jogador_tab]
                    st.markdown(f"**Pontuação Geral: {pts} de {len(metricas_nomes)} categorias vencidas.**")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    lista_destaques = destaques[jogador_tab]
                    
                    if lista_destaques:
                        st.markdown(f"**Por que {jogador_tab} se destaca?**")
                        for destaque in lista_destaques:
                            st.markdown(destaque, unsafe_allow_html=True)
                    else:
                        st.info(f"O atleta {jogador_tab} não lidera de forma isolada em nenhuma das métricas centrais analisadas neste grupo.")

        # ==========================================
        # ANÁLISE DE AGENTES E VERSATILIDADE (POOL OVERLAP)
        # ==========================================
        st.markdown("---")
        st.markdown("### Análise de Versatilidade e Agentes (Agent Pool)")
        st.write("Esta secção avalia a sobreposição de funções. Um gráfico com barras lado a lado no mesmo agente indica **Conflito de Papel** (ambos competem pela mesma vaga). Barras dispersas indicam **Complementaridade** (podem jogar juntos na mesma equipa).")
        
        df_agentes = df_macro[df_macro['Jogador'].isin(jogadores_selecionados)]
        
        if not df_agentes.empty and 'Agente' in df_agentes.columns:
            contagem_agentes = df_agentes.groupby(['Jogador', 'Agente']).size().reset_index(name='Partidas')
            ordem_agentes = contagem_agentes.groupby('Agente')['Partidas'].sum().sort_values(ascending=False).index
            mapa_cores = {jogador: cores_base[idx % len(cores_base)] for idx, jogador in enumerate(jogadores_selecionados)}
            
            fig_agentes = px.bar(
                contagem_agentes, 
                x='Agente', 
                y='Partidas', 
                color='Jogador', 
                barmode='group',
                category_orders={'Agente': list(ordem_agentes)},
                color_discrete_map=mapa_cores
            )
            
            fig_agentes.update_layout(
                paper_bgcolor="#0e1117", 
                plot_bgcolor="#0e1117", 
                margin=dict(t=30, b=0),
                legend_title_text='Atletas'
            )
            
            st.plotly_chart(fig_agentes, use_container_width=True)
            
            st.markdown("**Principais Escolhas (Top 3)**")
            colunas_top3 = st.columns(len(jogadores_selecionados))
            
            for idx, jogador in enumerate(jogadores_selecionados):
                with colunas_top3[idx]:
                    st.markdown(f"**{jogador}**")
                    top3 = contagem_agentes[contagem_agentes['Jogador'] == jogador].sort_values(by='Partidas', ascending=False).head(3)
                    st.dataframe(top3[['Agente', 'Partidas']], hide_index=True, use_container_width=True)
        else:
            st.warning("Não há dados de seleção de agentes suficientes para os jogadores selecionados.")

    elif len(jogadores_selecionados) == 1:
        st.info("Selecione pelo menos mais um jogador na barra superior para iniciar o cruzamento de dados.")

else:
    st.error("Erro: Não foi possível carregar os dados. Verifique os ficheiros CSV.")