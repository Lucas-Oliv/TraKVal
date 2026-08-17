import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 🧠 Importar as funções que criámos no utils.py (o cérebro do teu TCC)
from utils import carregar_dados_mestres, obter_mapas_riot

# ==========================================
# ⚙️ CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Radar Tático - TCC", layout="wide", initial_sidebar_state="expanded")

# Carregar a super-tabela fundida e as imagens da Riot
df_valido = carregar_dados_mestres()
mapas_riot = obter_mapas_riot()

# Prevenção de erros caso os dados falhem a carregar
if df_valido.empty or not mapas_riot:
    st.error("⚠️ Não foi possível carregar os dados ou a API da Riot. Verifica o teu ficheiro utils.py.")
    st.stop()

# ==========================================
# 🎛️ SELEÇÃO DE JOGO E MAPA (TOPO)
# ==========================================
st.markdown("<h2 style='text-align: center; color: #fff;'>Radar Tático Avançado</h2>", unsafe_allow_html=True)

col_jogo1, col_jogo2 = st.columns(2)
with col_jogo1:
    # Criar nomes legíveis para as séries (Jogos)
    series_ids = df_valido['ID_Serie'].unique()
    dict_series = {}
    for s in series_ids:
        times = df_valido[df_valido['ID_Serie'] == s]['Equipa_Eliminador'].dropna().unique()
        if len(times) >= 2:
            dict_series[s] = f"{times[0]} vs {times[1]} (ID: {s})"
        else:
            dict_series[s] = f"Jogo ID: {s}"
            
    serie_escolhida = st.selectbox("📺 Selecione o Jogo:", options=series_ids, format_func=lambda x: dict_series[x])
    df_serie = df_valido[df_valido['ID_Serie'] == serie_escolhida]

with col_jogo2:
    # Apenas mostrar mapas jogados nesta série
    mapas_serie = df_serie['Mapa'].dropna().unique()
    mapa_escolhido = st.selectbox("🗺️ Selecione o Mapa:", mapas_serie)
    df_mapa = df_serie[df_serie['Mapa'] == mapa_escolhido]

st.markdown("---")

# ==========================================
# 📐 LAYOUT DO DASHBOARD (3 COLUNAS)
# ==========================================
col_esq, col_centro, col_dir = st.columns([2, 5, 2], gap="large")

# --- COLUNA ESQUERDA: EQUIPAS E JOGADORES ---
with col_esq:
    st.markdown("### 🛡️ Jogadores (Atacantes)")
    equipas = df_mapa['Equipa_Eliminador'].dropna().unique()
    jogadores_selecionados = []
    
    for eq in equipas:
        st.markdown(f"**{eq}**")
        jogadores_eq = df_mapa[df_mapa['Equipa_Eliminador'] == eq]['Eliminador'].dropna().unique()
        selecionados = st.multiselect(f"Selecionar:", options=jogadores_eq, default=jogadores_eq, key=f"ms_{eq}")
        jogadores_selecionados.extend(selecionados)

# --- COLUNA DIREITA: FILTROS TÁTICOS ---
with col_dir:
    st.markdown("### 🔎 Filtros")
    estilo_grafico = st.radio("Estilo de Visão:", ["Points", "Heatmap"], horizontal=True)
    
    st.markdown("**Tipo de Abate**")
    filtro_fk = st.checkbox("Apenas First Kills", value=False)
    
    st.markdown("**Condição da Ronda**")
    condicoes = df_mapa['Condicao_Vitoria'].dropna().unique()
    cond_escolhida = st.multiselect("Resultado:", condicoes, default=condicoes)
    
    st.markdown("**Rondas Específicas**")
    rounds_disp = sorted(df_mapa['Round'].dropna().unique())
    round_escolhido = st.multiselect("Filtrar Rondas:", rounds_disp, default=[])

# ==========================================
    # BOTÃO DE REPLAY (Com Sincronização Dinâmica)
    # ==========================================
    series_com_replay = [100169, 100168, 100120, 100121, 100122, 100123, 100124, 100125, 100126, 100127, 100128, 100129, 100130, 100131, 100132, 100133, 100134, 100135, 100136, 100137, 100138, 100139, 100140, 100141] 
    
    # 1. 🗺️ MATEMÁTICA DO MAPA BATENDO:
    # Descobre se o mapa escolhido é o Mapa 1, 2 ou 3 com base na ordem da série
    try:
        mapa_num_atual = list(mapas_serie).index(mapa_escolhido) + 1
    except:
        mapa_num_atual = 1 # Caso falhe, assume o mapa 1

    # 2. 🎯 SINCRONIZAÇÃO DE ROUND:
    # Se o utilizador escolheu algum round no filtro "Filtrar Rondas", pegamos o primeiro escolhido
    if round_escolhido:
        round_padrao = round_escolhido[0]
    else:
        round_padrao = 1 # Se estiver vazio, o replay começará normalmente no Round 1
    
    # 3. VALIDAÇÃO E ENVIO DE PARÂMETROS PELA URL
    if serie_escolhida in series_com_replay:
        st.markdown("<br><br>", unsafe_allow_html=True) 
        
        nome_pagina_replay = "Replay_Utilitarios"
        
        # 🔗 AGORA A URL PASSA O ID, O NÚMERO DO MAPA E O ROUND FILTRADO!
        url_destino = f"{nome_pagina_replay}?series_id={serie_escolhida}&map_num={mapa_num_atual}&round_num={round_padrao}"
        
        st.markdown(f"""
            <a href="{url_destino}" target="_blank" style="text-decoration: none; display: block; width: 100%;">
                <div style="background-color: transparent; border: 2px solid #00FFCC; color: #00FFCC; 
                            padding: 12px; text-align: center; border-radius: 5px; font-weight: bold; 
                            font-family: 'Rajdhani', sans-serif; font-size: 18px; text-transform: uppercase; 
                            cursor: pointer; transition: 0.3s; box-shadow: 0 0 10px rgba(0,255,204,0.1);">
                    ▶ REPLAY (ROUND {round_padrao})
                </div>
            </a>
        """, unsafe_allow_html=True)

# --- COLUNA CENTRAL: O RADAR GEOMÉTRICO ---
with col_centro:
    tempo_min, tempo_max = st.slider("⏱️ Linha do Tempo da Ronda (Segundos)", min_value=0, max_value=150, value=(0, 150), step=5)
    
    # 1. Aplicar todos os filtros escolhidos
    df_filtrado = df_mapa[
        (df_mapa['Eliminador'].isin(jogadores_selecionados)) &
        (df_mapa['Tempo_Segundos'] >= tempo_min) &
        (df_mapa['Tempo_Segundos'] <= tempo_max) &
        (df_mapa['Condicao_Vitoria'].isin(cond_escolhida))
    ].copy()
    
    if filtro_fk: df_filtrado = df_filtrado[df_filtrado['First_Kill'] == True]
    if round_escolhido: df_filtrado = df_filtrado[df_filtrado['Round'].isin(round_escolhido)]

    if not df_filtrado.empty:
        
        # 2. Resgatar a Matemática e a Imagem da API Oficial da Riot
        mapa_info = None
        for m in mapas_riot:
            if m['displayName'].lower() == mapa_escolhido.lower():
                mapa_info = m
                break
                
        if mapa_info:
            x_mult = mapa_info['xMultiplier']
            y_mult = mapa_info['yMultiplier']
            x_add = mapa_info['xScalarToAdd']
            y_add = mapa_info['yScalarToAdd']
            url_img_oficial = mapa_info['displayIcon'] 
            
            # 3. Converter Coordenadas 3D (Unreal Engine) para o Plano 2D (0 a 1)
            # Atenção: O Valorant inverte o X e o Y quando exporta os dados!
            df_filtrado['X_Radar'] = (df_filtrado['Eliminado_Y'] * x_mult) + x_add
            df_filtrado['Y_Radar'] = (df_filtrado['Eliminado_X'] * y_mult) + y_add

            # ==========================================
            # 🎨 DESENHAR O GRÁFICO (PLOTLY)
            # ==========================================
            fig = go.Figure()

            if estilo_grafico == "Points":
                for jogador in jogadores_selecionados:
                    df_jog = df_filtrado[df_filtrado['Eliminador'] == jogador]
                    if not df_jog.empty:
                        
                        # Preparar os dados para o Tooltip baseado nos novos ficheiros fundidos
                        dados_extra = df_jog[[
                            'Eliminado', 'Arma', 'Round', 
                            'Lado_Killer', 'Tipo_Dano', 
                            'Assistencias', 'Trade_Kill'
                        ]].fillna("Desconhecido")

                        # HTML Customizado para a caixa de informações do ponto
                        template_hover = (
                            "<b>Atacante:</b> " + jogador + " (Lado: %{customdata[3]})<br>" +
                            "<b>Alvo:</b> %{customdata[0]}<br>" +
                            "<b>Arma:</b> %{customdata[1]} (Dano: %{customdata[4]})<br>" +
                            "<b>Assistência(s):</b> %{customdata[5]}<br>" +
                            "<b>Trade Kill:</b> %{customdata[6]}<br>" +
                            "<b>Round:</b> %{customdata[2]}<br><extra></extra>"
                        )

                        fig.add_trace(go.Scatter(
                            x=df_jog['X_Radar'], 
                            y=df_jog['Y_Radar'],
                            mode='markers',
                            name=jogador,
                            marker=dict(size=11, line=dict(width=1.5, color='black'), opacity=0.9),
                            hovertemplate=template_hover,
                            customdata=dados_extra
                        ))
                        
            elif estilo_grafico == "Heatmap":
                # Heatmap Profissional e Suavizado (Sem "Pixelização")
                escala_termica = [
                    [0.0, 'rgba(0,0,0,0)'],       # Vazio -> Transparente
                    [0.2, 'rgba(0,0,255,0.4)'],   # Frio -> Azul translúcido
                    [0.5, 'rgba(255,255,0,0.7)'], # Morno -> Amarelo
                    [1.0, 'rgba(255,0,0,0.9)']    # Quente -> Vermelho intenso
                ]

                fig.add_trace(go.Histogram2dContour(
                    x=df_filtrado['X_Radar'],
                    y=df_filtrado['Y_Radar'],
                    colorscale=escala_termica,
                    reversescale=False,
                    opacity=0.8, 
                    ncontours=30, 
                    zsmooth='best', 
                    showscale=False, 
                    line=dict(width=0), 
                    hoverinfo='skip' 
                ))

            # 4. Colocar a Imagem Oficial do Mapa no Fundo
            fig.add_layout_image(
                dict(
                    source=url_img_oficial, 
                    xref="x", yref="y",
                    x=0, y=0, 
                    sizex=1, sizey=1, 
                    sizing="stretch", 
                    opacity=0.9, 
                    layer="below"
                )
            )

            # 5. Travar o Gráfico na Escala Correta (1:1 Geométrica)
            fig.update_layout(
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", 
                xaxis=dict(visible=False, range=[0, 1], showgrid=False, zeroline=False),
                # A grande sacada: range=[1,0] inverte o Y para o mapa não ficar de pernas para o ar!
                yaxis=dict(visible=False, range=[1, 0], scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False),
                margin=dict(l=0, r=0, t=0, b=0),
                height=700,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white"))
            )

            # Exibir no Streamlit
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error(f"❌ O mapa '{mapa_escolhido}' não foi encontrado na API oficial da Riot.")
            
    else:
        st.info("👻 Nenhuma eliminação encontrada com os filtros selecionados.")