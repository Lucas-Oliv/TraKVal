import streamlit as st
import streamlit.components.v1 as components
import json
import requests
import os
import re
import base64

st.set_page_config(page_title="Valorant VCT HUD", layout="wide", initial_sidebar_state="collapsed")

import mimetypes
from pathlib import Path

# ==========================================
# 1. CARREGADOR DE IMAGENS LOCAIS (Base64) - VERSÃO MODERNA
# ==========================================

# PASSO 1: Configurar os caminhos usando Pathlib (mais moderno e legível)
# Path(__file__).parent pega a pasta onde este script está salvo.
BASE_DIR = Path(__file__).parent

# Juntamos com a pasta "img" usando a barra "/", que o pathlib entende automaticamente!
IMG_DIR = BASE_DIR / "img"

def get_b64_image(filename):
    """
    Procura a imagem na pasta 'img', descobre seu formato automaticamente
    e retorna a string em Base64 pronta para uso na web.
    """
    # Cria o caminho completo até a imagem
    caminho_imagem = IMG_DIR / filename
    
    # PASSO 2: Verificar se a imagem realmente existe antes de tentar abrir
    if not caminho_imagem.exists():
        print(f"Aviso: A imagem '{filename}' não foi encontrada na pasta {IMG_DIR}.")
        return ""
    
    try:
        # PASSO 3: Descobrir automaticamente o tipo do arquivo (ex: image/png, image/webp)
        # O mimetypes resolve isso sozinho, sem precisarmos fazer "ifs" manuais.
        mime_type, _ = mimetypes.guess_type(caminho_imagem)
        
        # Se por acaso ele não descobrir, definimos um padrão de segurança
        if mime_type is None:
            mime_type = "image/png"
            
        # PASSO 4: Abrir, ler e converter a imagem
        # O ".read_bytes()" do pathlib já abre e lê o arquivo em modo binário automaticamente!
        dados_imagem = caminho_imagem.read_bytes()
        
        # Converte para base64 e transforma em texto (decode)
        texto_base64 = base64.b64encode(dados_imagem).decode('utf-8')
        
        # Retorna o texto formatado para a web
        return f"data:{mime_type};base64,{texto_base64}"
        
    except Exception as erro:
        print(f"Erro inesperado ao processar '{filename}': {erro}")
        return ""

# ==========================================
# TESTANDO / CARREGANDO AS IMAGENS
# ==========================================
img_hs = get_b64_image("headshot.ebebdce6.webp")
img_boom = get_b64_image("white-boom.41046c02.webp")
img_defuse = get_b64_image("white-defuse.ed852d7e.webp")
img_elim = get_b64_image("white-elimination.660aabac.webp")
img_yspike = get_b64_image("yellow-spike.png")
img_rspike = get_b64_image("red-spike.png")

# ==========================================
# 2. CSS PARA TELA CHEIA
# ==========================================
st.markdown("""
    <style>
        header {visibility: hidden;} #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        [data-testid="collapsedControl"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        .block-container {
            padding: 0rem !important; padding-bottom: 0rem !important;
            padding-left: 0rem !important; padding-right: 0rem !important;
            max-width: 100% !important; background-color: #050B14;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. LEITURA DE URL E ARQUIVOS
# ==========================================
if "series_id" not in st.query_params or "map_num" not in st.query_params:
    st.error("⚠️ Partida não identificada.")
    st.stop()

series_id = st.query_params["series_id"]
map_num = st.query_params["map_num"]
round_padrao_url = int(st.query_params.get("round_num", 1))

# --- CAMINHO RELATIVO PARA PORTABILIDADE ---
# O caminho para a pasta de replays agora é construído de forma relativa
# ao local deste script, garantindo que funcione em qualquer computador.
sitte_dir = Path(__file__).resolve().parent.parent # Vai de '.../pages' para '.../Sitte'
# ATENÇÃO: O nome "Masters_Santiago" está fixo. Se você tiver replays de outros torneios, talvez precise tornar esta parte do caminho dinâmica.
PASTA_ROUNDS = sitte_dir / "Replay" / "Masters_Santiago" / f"Serie_{series_id}" / f"Mapa_{map_num}"

if not os.path.exists(PASTA_ROUNDS):
    st.error(f"❌ A pasta do replay não foi encontrada: {PASTA_ROUNDS}")
    st.stop()

mapa_arquivos = {}
for f in os.listdir(PASTA_ROUNDS):
    if f.lower().endswith('.json') and 'round' in f.lower():
        num_match = re.search(r'\d+', f)
        if num_match: mapa_arquivos[int(num_match.group())] = f

numeros_rounds = sorted(mapa_arquivos.keys())
if not numeros_rounds: st.stop()
if round_padrao_url not in numeros_rounds: round_padrao_url = numeros_rounds[0]

@st.cache_data
def carregar_dados_do_round(pasta, nome_arquivo_exato):
    with open(os.path.join(pasta, nome_arquivo_exato), 'r', encoding='utf-8') as f:
        dados = json.load(f)
    config = dados.get('props', {}).get('pageProps', {}).get('matchMetadata', {}).get('configuration', {})
    frames = dados.get('props', {}).get('pageProps', {}).get('matchRoundFrames', [])
    return config, frames, dados

config_geral, frames_do_round, dados_raw = carregar_dados_do_round(PASTA_ROUNDS, mapa_arquivos[round_padrao_url])

# ==========================================
# 4. PLACAR E TIPO DE VITÓRIA (EXPLOSÃO/DEFUSE)
# ==========================================
jogadores_config = config_geral.get('players', [])
equipa_A = jogadores_config[:5]
equipa_B = jogadores_config[5:]
ids_A = [str(p['player_id']) for p in equipa_A]
ids_B = [str(p['player_id']) for p in equipa_B]

is_A_attack_start = True
try:
    _, frames_r1, _ = carregar_dados_do_round(PASTA_ROUNDS, mapa_arquivos[numeros_rounds[0]])
    is_A_attack_start = False
    for f in frames_r1:
        if str(f.get('spikeStatus', {}).get('carrier', '')) in ids_A: is_A_attack_start = True; break
        for s in f.get('playerStatus', []):
            if s.get('hasSpike') and str(s.get('playerId', '')) in ids_A: is_A_attack_start = True; break
        if is_A_attack_start: break
except: pass

if is_A_attack_start:
    ids_time_left, ids_time_right = ids_A, ids_B
    nome_left = equipa_A[0].get('display_name', 'ATK').split(' ')[0]
    nome_right = equipa_B[0].get('display_name', 'DEF').split(' ')[0]
else:
    ids_time_left, ids_time_right = ids_B, ids_A
    nome_left = equipa_B[0].get('display_name', 'ATK').split(' ')[0]
    nome_right = equipa_A[0].get('display_name', 'DEF').split(' ')[0]

def calcular_placar_real(pasta, rounds_totais, r_atual, ids_left, ids_right, jogadores, mapa_arq):
    score_L, score_R, historico = 0, 0, {}
    sinonimos_left = {'red', 'team1', 'ataque', 'attack', 't1'}
    sinonimos_right = {'blue', 'team2', 'defesa', 'defense', 't2'}
    
    for p in jogadores:
        pid = str(p.get('player_id'))
        t_id = str(p.get('teamId', p.get('team_id', ''))).lower()
        if pid in ids_left: sinonimos_left.update([t_id, str(p.get('team_name', '')).lower(), str(p.get('team_acronym', '')).lower()])
        elif pid in ids_right: sinonimos_right.update([t_id, str(p.get('team_name', '')).lower(), str(p.get('team_acronym', '')).lower()])
    sinonimos_left.discard(''); sinonimos_right.discard('')

    for r in rounds_totais:
        try:
            with open(os.path.join(pasta, mapa_arq[r]), 'r', encoding='utf-8') as f:
                d = json.load(f)
            
            winner_id = ""
            win_type = "elimination" # Padrão
            
            match_rounds = d.get('props', {}).get('pageProps', {}).get('matchRounds', [])
            for rnd in match_rounds:
                if str(rnd.get('roundNumber', rnd.get('roundNum', ''))) == str(r):
                    w = rnd.get('winningTeamId', rnd.get('winningTeam', ''))
                    if isinstance(w, dict): winner_id = str(w.get('id', w.get('name', ''))).lower()
                    else: winner_id = str(w).lower()
                    # Pega o motivo da vitória (Explosão, Defuse, etc)
                    win_type = str(rnd.get('roundResultCode', rnd.get('roundResult', 'elimination'))).lower()
                    break
            
            if winner_id in sinonimos_left:
                if r < r_atual: score_L += 1
                historico[r] = {'side': 'win-left', 'type': win_type}
            elif winner_id in sinonimos_right:
                if r < r_atual: score_R += 1
                historico[r] = {'side': 'win-right', 'type': win_type}
        except: pass
            
    return score_L, score_R, historico

score_team_left, score_team_right, cores_rondas = calcular_placar_real(PASTA_ROUNDS, numeros_rounds, round_padrao_url, ids_time_left, ids_time_right, jogadores_config, mapa_arquivos)

# ==========================================
# 5. MOTOR GEOMÉTRICO E LÓGICA DE SPIKE/HEADSHOTS
# ==========================================
def compilar_round_especifico(config, frames, dados_crus):
    mapa_info = config.get('selected_map', {})
    nome_mapa = mapa_info.get('name', '') if isinstance(mapa_info, dict) else str(mapa_info).split('/')[-1]
    mapas_api = requests.get("https://valorant-api.com/v1/maps").json()['data']
    mapa_oficial = next((m for m in mapas_api if m.get('displayName', '').lower() == nome_mapa.lower()), mapas_api[0])
    
    url_mapa = mapa_oficial['displayIcon']
    x_mult, y_mult = mapa_oficial.get('xMultiplier', 0.000078), mapa_oficial.get('yMultiplier', -0.000078)
    x_scalar, y_scalar = mapa_oficial.get('xScalarToAdd', 0.5), mapa_oficial.get('yScalarToAdd', 0.5)

    # Cores Laterais Atuais
    is_left_attack_now = False
    for f in frames:
        if str(f.get('spikeStatus', {}).get('carrier', '')) in ids_time_left: is_left_attack_now = True; break
        for s in f.get('playerStatus', []):
            if s.get('hasSpike') and str(s.get('playerId', '')) in ids_time_left: is_left_attack_now = True; break
        if is_left_attack_now: break
    
    color_left = "atk-color" if is_left_attack_now else "def-color"
    color_right = "def-color" if is_left_attack_now else "atk-color"

    # Extrator de Kills e Headshots
    agentes_db, todas_kills, memoria_kills = {}, [], set()
    for p in jogadores_config:
        try:
            d_ag = requests.get(f"https://valorant-api.com/v1/agents/{p['agent_guid']}").json()['data']
            habs = {h['slot']: h.get('displayIcon', '') for h in d_ag.get('abilities', [])}
            agentes_db[str(p['player_id'])] = {'nome': p['display_name'], 'foto': d_ag['displayIcon'], 'icone': d_ag['displayIconSmall'], 'habs': habs}
        except: agentes_db[str(p['player_id'])] = {'nome': p['display_name'], 'foto': '', 'icone': '', 'habs': {}}

    for i, f in enumerate(frames):
        for k in f.get('killFeed', []):
            kid, vid = str(k.get('killerId', '')), str(k.get('victimId', ''))
            is_hs = k.get('finishingDamage', {}).get('isHeadshot', False)
            if not is_hs: is_hs = k.get('isHeadshot', False) # Fallback
            
            k_hash = f"{kid}-{vid}-{i//20}" 
            if k_hash not in memoria_kills:
                memoria_kills.add(k_hash)
                todas_kills.append({'frame': i, 'k': kid, 'v': vid, 'hs': is_hs})

    # Extrator do Frame Exato da Spike Plantada
    plant_frame, defuse_frame = -1, -1
    try:
        match_rounds = dados_crus.get('props', {}).get('pageProps', {}).get('matchRounds', [])
        for rnd in match_rounds:
            if str(rnd.get('roundNumber', '')) == str(round_padrao_url):
                pt = rnd.get('plantRoundTime', 0)
                if pt > 0: plant_frame = int((pt / 1000) * 5)
                dt = rnd.get('defuseRoundTime', 0)
                if dt > 0: defuse_frame = int((dt / 1000) * 5)
                break
    except: pass

    slot_map = {'ABILITY_1': 'Ability1', 'ABILITY_2': 'Ability2', 'GRENADE_ABILITY': 'Grenade', 'ULTIMATE': 'Ultimate'}
    frames_js, popups_ativos, cargas_anteriores = [], {}, {}
    last_pos = {str(p['player_id']): {'x': -100, 'y': -100} for p in jogadores_config}
    
    for frame_idx, f in enumerate(frames):
        estado_frame = {'jogadores': {}}
        for pid in list(popups_ativos.keys()):
            if frame_idx >= popups_ativos[pid]['fim']: del popups_ativos[pid]
            
        for s in f.get('playerStatus', []):
            pid = str(s['playerId'])
            cargas = {slot_map[h['inventorySlot']]: h.get('totalCharges', 0) for h in s.get('abilities', []) if h.get('inventorySlot') in slot_map}
            if pid in cargas_anteriores:
                for slot in ['Ability1', 'Ability2', 'Grenade', 'Ultimate']:
                    if cargas.get(slot, 0) < cargas_anteriores[pid].get(slot, 0):
                        url_hab = agentes_db[pid]['habs'].get(slot, '')
                        if url_hab: popups_ativos[pid] = {'url': url_hab, 'fim': frame_idx + 15}
            cargas_anteriores[pid] = cargas
            
            if s.get('isAlive'):
                last_pos[pid]['x'] = ((s['locationY'] * x_mult) + x_scalar) * 100
                last_pos[pid]['y'] = ((s['locationX'] * y_mult) + y_scalar) * 100
            
            ult_max = 7
            for h in s.get('abilities', []):
                if h.get('inventorySlot') == 'ULTIMATE': ult_max = h.get('maxCharges', 7); break
            
            estado_frame['jogadores'][pid] = {
                'x': last_pos[pid]['x'], 'y': last_pos[pid]['y'],
                'vivo': s.get('isAlive', False), 'hp': s.get('health', 0) if s.get('isAlive') else 0, 
                'armor': s.get('armor', 0) if s.get('isAlive') else 0, 'creds': s.get('credits', 0), 
                'arma': s.get('equippedWeapon', {}).get('image', ''), 'spike': s.get('hasSpike', False), 
                'skill_popup': popups_ativos.get(pid, {}).get('url', None),
                'habilidades': {
                    'Ability1': cargas.get('Ability1', 0), 'Ability2': cargas.get('Ability2', 0), 
                    'Grenade': cargas.get('Grenade', 0), 'Ultimate': cargas.get('Ultimate', 0), 'UltMax': ult_max
                }
            }
        frames_js.append(estado_frame)
    return url_mapa, agentes_db, frames_js, color_left, color_right, todas_kills, nome_mapa, plant_frame, defuse_frame

with st.spinner(f"Renderizando Round {round_padrao_url}..."):
    url_mapa, agentes_db, frames_js, color_left, color_right, todas_kills, nome_mapa, p_frame, d_frame = compilar_round_especifico(config_geral, frames_do_round, dados_raw)

db_str = json.dumps(agentes_db).replace("'", "\\'")
frames_str = json.dumps(frames_js).replace("'", "\\'")
kills_str = json.dumps(todas_kills).replace("'", "\\'")
timeLeft_str = json.dumps(ids_time_left)

# ==========================================
# 6. HTML/JS TEMPLATE (HUD PREMIUM COM TODAS AS FUNÇÕES)
# ==========================================
html_template = """
<!DOCTYPE html>
<html>
<head>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Teko:wght@400;600;700&family=Rajdhani:wght@600;700&display=swap');
    body { background: transparent; color: #ECE8E1; font-family: 'Rajdhani', sans-serif; margin: 0; padding: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
    
    .vct-header { display: flex; justify-content: center; align-items: stretch; height: 60px; margin-top: 10px; z-index: 50; position: relative; filter: drop-shadow(0px 5px 10px rgba(0,0,0,0.5)); }
    .team-box { display: flex; align-items: center; justify-content: center; width: 320px; padding: 0 20px; font-family: 'Teko', sans-serif; font-size: 34px; font-weight: 700; text-transform: uppercase; transform: skewX(-15deg); }
    .team-box span { transform: skewX(15deg); }
    
    .score-center { display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; }
    .score-bar { display: flex; align-items: center; background: #0F1923; padding: 0 30px; font-family: 'Teko', sans-serif; font-size: 48px; font-weight: 700; z-index: 2; box-shadow: 0 0 15px rgba(0,0,0,0.8); transform: skewX(-15deg); border: 1px solid rgba(255,255,255,0.05); }
    .score-bar > * { transform: skewX(15deg); }
    .score-num { width: 50px; text-align: center; }
    
    /* 🔴 TIMER DA SPIKE (Abaixo do Placar Central) */
    .spike-timer-container {
        position: absolute; top: 75px; left: 50%; transform: translateX(-50%);
        display: none; flex-direction: column; align-items: center;
        background: rgba(10, 15, 20, 0.95); border: 1px solid rgba(255, 70, 85, 0.4);
        padding: 5px 20px 8px 20px; border-radius: 6px; box-shadow: 0 5px 15px rgba(0,0,0,0.8); z-index: 100;
    }
    .red-spike-icon { height: 32px; margin-bottom: 2px; filter: drop-shadow(0 0 5px rgba(255, 70, 85, 0.8)); }
    .spike-bar-bg { width: 120px; height: 6px; background: #222; border-radius: 3px; overflow: hidden; margin-bottom: 2px; }
    .spike-bar-fill { height: 100%; width: 0%; background: #FF4655; box-shadow: 0 0 5px #FF4655; transition: width 0.2s linear; }
    .spike-time-txt { font-family: 'Teko', sans-serif; font-size: 26px; color: #FF4655; line-height: 1; letter-spacing: 1px; }

    .atk-color { color: #FF4655; text-shadow: 0 0 8px rgba(255,70,85,0.6); border-bottom: 3px solid #FF4655; background: rgba(255,70,85,0.1); margin-right: -10px;} 
    .def-color { color: #00FFCC; text-shadow: 0 0 8px rgba(0,255,204,0.6); border-bottom: 3px solid #00FFCC; background: rgba(0,255,204,0.1); margin-left: -10px;}
    .round-info { font-size: 20px; color: #888; margin: 0 20px; display: flex; flex-direction: column; align-items: center; line-height: 1; text-transform: uppercase; }
    
    .broadcast-area { display: flex; justify-content: space-between; flex-grow: 1; padding: 10px 40px; position: relative; height: calc(100vh - 150px); }
    .hud-col { display: flex; flex-direction: column; gap: 4px; width: 380px; z-index: 20; justify-content: center; }
    
    /* CARDS */
    .player-row { display: flex; align-items: center; height: 80px; background: transparent; padding: 0 10px; border-bottom: 1px solid rgba(255,255,255,0.03); transition: 0.3s; position: relative; }
    .team-left .player-row { flex-direction: row; }
    .team-right .player-row { flex-direction: row-reverse; }

    .row-left { display: flex; align-items: center; gap: 8px; width: 110px; }
    .team-right .row-left { flex-direction: row-reverse; justify-content: flex-start; }
    .eye-icon { width: 16px; height: 16px; opacity: 0.2; }
    .inv-icons { display: flex; align-items: center; gap: 6px; }
    .team-right .inv-icons { flex-direction: row-reverse; }
    
    .inv-item { height: 14px; filter: brightness(0) invert(1); opacity: 0.5; object-fit: contain; }
    .weapon-main { height: 20px; filter: brightness(0) invert(1) drop-shadow(0 2px 2px rgba(0,0,0,0.8)); opacity: 0.9; max-width: 60px; object-fit: contain; }

    .row-center { display: flex; flex-direction: column; align-items: center; flex-grow: 1; padding: 0 10px; }
    .creds-text { font-family: 'Rajdhani', sans-serif; font-size: 14px; color: #E0E6EB; font-weight: 600; width: 100%; text-align: right; margin-bottom: -6px;}
    .team-right .creds-text { text-align: left; }
    .hp-armor { display: flex; align-items: baseline; gap: 6px; justify-content: flex-end; width: 100%; }
    .team-right .hp-armor { justify-content: flex-start; flex-direction: row-reverse; }
    .hp-text { font-family: 'Teko', sans-serif; font-size: 42px; color: #FFF; font-weight: 700; line-height: 1; margin-bottom: -2px;}
    .hp-text.low { color: #FF4655; text-shadow: 0 0 10px rgba(255,70,85,0.6); }
    .armor-text { font-family: 'Teko', sans-serif; font-size: 26px; color: #6D8B9B; font-weight: 600; line-height: 1; }
    
    .skills-bar { display: flex; align-items: flex-end; gap: 8px; justify-content: flex-end; width: 100%; }
    .team-right .skills-bar { justify-content: flex-start; flex-direction: row-reverse; }
    .skill-wrapper { display: flex; flex-direction: column; align-items: center; gap: 3px; }
    .skill-icon { width: 16px; height: 16px; opacity: 0.3; object-fit: contain; filter: brightness(0) invert(1); transition: 0.2s;}
    .skill-icon.active { opacity: 1; }
    
    .dot-container { display: flex; gap: 2px; height: 4px; justify-content: center; }
    .dot { width: 4px; height: 4px; background: rgba(255,255,255,0.2); border-radius: 50%; }
    .dot.active { background: #FFF; box-shadow: 0 0 3px #FFF; }
    .dot.ult-active { background: #FFD700; box-shadow: 0 0 5px #FFD700; opacity: 1; }

    /* CÍRCULO E SPIKE AMARELA */
    .row-right { position: relative; width: 68px; height: 68px; display: flex; justify-content: center; align-items: center; margin-left: 5px; }
    .team-right .row-right { margin-left: 0; margin-right: 5px; }
    .circle-frame { width: 100%; height: 100%; border-radius: 50%; border: 2px solid; overflow: hidden; display: flex; justify-content: center; align-items: center; box-shadow: inset 0 0 15px rgba(0,0,0,0.8); }
    .agent-portrait { height: 120%; object-fit: cover; margin-top: -10%; margin-left: -5%; }
    
    .name-badge { position: absolute; top: -8px; right: -5px; background: #050B14; color: #FFF; font-family: 'Rajdhani', sans-serif; font-size: 15px; font-weight: 700; padding: 1px 6px; border-radius: 4px; white-space: nowrap; z-index: 2; box-shadow: 0 2px 5px rgba(0,0,0,0.8); }
    .team-right .name-badge { right: auto; left: -5px; }

    .knife-icon { position: absolute; bottom: -5px; right: -10px; height: 26px; filter: brightness(0) invert(1) drop-shadow(0 2px 2px rgba(0,0,0,0.8)); z-index: 3; }
    .team-right .knife-icon { right: auto; left: -10px; transform: scaleX(-1); }
    
    .spike-indicator { position: absolute; top: -5px; right: 45px; display: none; z-index: 10; }
    .team-right .spike-indicator { right: auto; left: 45px; }
    .y-spike-img { height: 22px; filter: drop-shadow(0 0 5px rgba(255, 215, 0, 0.8)); }

    .dead { opacity: 0.25; filter: grayscale(100%); }

    /* MAPA E KILLFEED */
    .map-wrapper { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 70vh; height: 70vh; display: flex; justify-content: center; align-items: center; }
    #mapBg { position: absolute; max-width: 100%; max-height: 100%; opacity: 0.8; z-index: 1; filter: drop-shadow(0 0 15px rgba(0,0,0,0.5));}
    #gameCanvas { position: absolute; width: 100%; height: 100%; z-index: 10; filter: drop-shadow(0 0 15px rgba(0,0,0,0.8)); }
    
    #killfeed { position: absolute; top: 20px; right: 400px; display: flex; flex-direction: column; gap: 5px; z-index: 100; pointer-events: none; }
    .kf-item { display: flex; align-items: center; gap: 8px; background: rgba(10, 15, 20, 0.9); border: 1px solid rgba(255,255,255,0.1); padding: 4px 12px; transform: skewX(-15deg); box-shadow: 0 2px 10px rgba(0,0,0,0.5); font-weight: 700; font-size: 15px; text-transform: uppercase; }
    .kf-item > * { transform: skewX(15deg); } 
    .kf-weap { height: 16px; filter: brightness(0) invert(1); object-fit: contain; }
    .kf-hs { height: 18px; margin-left: 2px; } /* Headshot Icon */

    /* PAINEL INFERIOR */
    .bottom-panel { position: absolute; bottom: 0; left: 0; width: 100%; display: flex; flex-direction: column; z-index: 50; }
    .rounds-tracker-placeholder { height: 60px; background: linear-gradient(to top, #0A0F14, transparent); width: 100%; }
    .director-deck { height: 70px; background: #0A0F14; border-top: 1px solid rgba(255, 255, 255, 0.05); display: flex; align-items: center; padding: 0 40px; gap: 30px; box-shadow: 0 -5px 20px rgba(0,0,0,0.8); }
    #playBtn { background: rgba(0, 255, 204, 0.1); border: 2px solid #00FFCC; color: #00FFCC; padding: 8px 30px; border-radius: 4px; font-weight: bold; cursor: pointer; text-transform: uppercase; font-family: 'Rajdhani', sans-serif; font-size: 18px; transition: 0.3s; box-shadow: 0 0 10px rgba(0,255,204,0.2); }
    #playBtn:hover { background: #00FFCC; color: #000; box-shadow: 0 0 20px rgba(0,255,204,0.6); transform: scale(1.05); }
    #timeline { flex-grow: 1; accent-color: #00FFCC; cursor: pointer; height: 6px; }
    .clock { font-family: monospace; font-size: 18px; color: white; }
</style>
</head>
<body>
    <div class="vct-header">
        <div class="team-box __COLOR_LEFT__"><span class="__COLOR_LEFT__">__NOME_LEFT__</span></div>
        
        <div class="score-center">
            <div class="score-bar">
                <div class="score-num __COLOR_LEFT__" id="score-left">__PLACAR_LEFT__</div>
                <div class="round-info"><span>ROUND __ROUND_NUM__</span><span>__NOME_MAPA__</span></div>
                <div class="score-num __COLOR_RIGHT__" id="score-right">__PLACAR_RIGHT__</div>
            </div>
            <div class="spike-timer-container" id="spike-hud">
                <img src="__IMG_RSPIKE__" class="red-spike-icon">
                <div class="spike-bar-bg"><div class="spike-bar-fill" id="spike-bar"></div></div>
                <div class="spike-time-txt" id="spike-txt">45.00</div>
            </div>
        </div>
        
        <div class="team-box __COLOR_RIGHT__"><span class="__COLOR_RIGHT__">__NOME_RIGHT__</span></div>
    </div>

    <div id="killfeed"></div>

    <div class="broadcast-area">
        <div class="hud-col" id="panel-left"></div>
        <div class="map-wrapper">
            <img id="mapBg" src="__URL_MAPA__">
            <canvas id="gameCanvas" width="800" height="800"></canvas>
        </div>
        <div class="hud-col" id="panel-right"></div>
    </div>

    <div class="bottom-panel">
        <div class="rounds-tracker-placeholder"></div>
        <div class="director-deck">
            <button id="playBtn">▶ PLAY</button>
            <div class="clock" id="clock">00:00</div>
            <input type="range" id="timeline" min="0" max="__MAX_FRAMES__" value="0">
        </div>
    </div>

    <script>
        const agentesDb = JSON.parse('__DB_STR__');
        const frames = JSON.parse('__FRAMES_STR__');
        const globalKills = JSON.parse('__KILLS_STR__');
        const teamLeftIds = JSON.parse('__TEAM_LEFT_IDS__');
        
        const plantFrame = parseInt('__PLANT_FRAME__');
        const defuseFrame = parseInt('__DEFUSE_FRAME__');
        
        const colorClassLeft = '__COLOR_LEFT__';
        const ringColorLeft = colorClassLeft === 'atk-color' ? '#FF4655' : '#00FFCC';
        const ringColorRight = colorClassLeft === 'atk-color' ? '#00FFCC' : '#FF4655';
        
        const imgCache = {};
        function loadImg(url) { if (!url || imgCache[url]) return; let img = new Image(); img.src = url; imgCache[url] = img; }
        
        function initCards() {
            let htmlLeft = '', htmlRight = '';
            for (let pid in agentesDb) {
                let ag = agentesDb[pid];
                let isLeft = false; for(let i=0; i<teamLeftIds.length; i++) if(String(teamLeftIds[i]) === String(pid)) isLeft = true;
                let cClass = isLeft ? 'team-left' : 'team-right';
                let rColor = isLeft ? ringColorLeft : ringColorRight;
                
                loadImg(ag.icone); loadImg(ag.habs.Ability1); loadImg(ag.habs.Ability2); loadImg(ag.habs.Grenade); loadImg(ag.habs.Ultimate);
                
                let card = `
                <div class="player-row ${cClass}" id="card-${pid}">
                    <div class="row-left">
                        <svg class="eye-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24M1 1l22 22"></path></svg>
                        <div class="inv-icons">
                            <img src="https://media.valorant-api.com/equippables/b8418385-4428-2166-5150-13838274d82f/displayicon.png" class="inv-item" id="inv-arm-${pid}">
                            <img src="https://media.valorant-api.com/weapons/29a0cfab-485b-f5d5-779a-b59f85e204a8/displayicon.png" class="inv-item" style="transform: scaleX(-1);">
                            <img src="" class="weapon-main" id="weap-${pid}" style="transform: scaleX(-1);">
                        </div>
                    </div>

                    <div class="row-center">
                        <div class="creds-text" id="cred-${pid}">0 ¤</div>
                        <div class="hp-armor">
                            <span class="hp-text" id="hpt-${pid}">100</span>
                            <span class="armor-text" id="arm-${pid}">(50)</span>
                        </div>
                        <div class="skills-bar">
                            <div class="skill-wrapper">
                                <img src="${ag.habs.Ability1 || ''}" class="skill-icon" id="s1-${pid}">
                                <div class="dot-container" id="s1-dots-${pid}"></div>
                            </div>
                            <div class="skill-wrapper">
                                <img src="${ag.habs.Ability2 || ''}" class="skill-icon" id="s2-${pid}">
                                <div class="dot-container" id="s2-dots-${pid}"></div>
                            </div>
                            <div class="skill-wrapper">
                                <img src="${ag.habs.Grenade || ''}" class="skill-icon" id="sg-${pid}">
                                <div class="dot-container" id="sg-dots-${pid}"></div>
                            </div>
                            <div class="skill-wrapper">
                                <img src="${ag.habs.Ultimate || ''}" class="skill-icon" id="su-${pid}">
                                <div class="dot-container" id="su-dots-${pid}"></div>
                            </div>
                        </div>
                    </div>

                    <div class="row-right">
                        <div class="name-badge">${ag.nome}</div>
                        <div class="circle-frame" style="border-color: ${rColor};">
                            <img src="${ag.foto}" class="agent-portrait">
                        </div>
                        <img src="" class="knife-icon" id="knife-${pid}">
                        <div class="spike-indicator" id="yspike-${pid}"><img src="__IMG_YSPIKE__" class="y-spike-img"></div>
                    </div>
                </div>`;
                if (isLeft) htmlLeft += card; else htmlRight += card;
            }
            document.getElementById('panel-left').innerHTML = htmlLeft;
            document.getElementById('panel-right').innerHTML = htmlRight;
        }
        
        const canvas = document.getElementById('gameCanvas'); const ctx = canvas.getContext('2d');
        const timeline = document.getElementById('timeline'); const clock = document.getElementById('clock');
        const playBtn = document.getElementById('playBtn'); const killfeedDiv = document.getElementById('killfeed');
        const sHud = document.getElementById('spike-hud'); const sBar = document.getElementById('spike-bar'); const sTxt = document.getElementById('spike-txt');

        function updateUI(index) {
            const frame = frames[index]; if (!frame) return;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            let kfHtml = '';
            globalKills.forEach(ak => {
                if (index >= ak.frame && index < ak.frame + 20) {
                    let kAg = agentesDb[ak.k]; let vAg = agentesDb[ak.v];
                    if(kAg && vAg) {
                        let kLeft = false; for(let i=0; i<teamLeftIds.length; i++) if(String(teamLeftIds[i]) === String(ak.k)) kLeft = true;
                        let vLeft = false; for(let i=0; i<teamLeftIds.length; i++) if(String(teamLeftIds[i]) === String(ak.v)) vLeft = true;
                        let kColor = kLeft ? colorClassLeft : (colorClassLeft==='atk-color'?'def-color':'atk-color');
                        let vColor = vLeft ? colorClassLeft : (colorClassLeft==='atk-color'?'def-color':'atk-color');
                        let weapImg = frames[ak.frame]?.jogadores[ak.k]?.arma || '';
                        
                        // Headshot Icon Logic
                        let hsImg = ak.hs ? `<img src="__IMG_HS__" class="kf-hs">` : '';
                        
                        kfHtml += `<div class="kf-item"><span class="${kColor}">${kAg.nome}</span><img src="${weapImg}" class="kf-weap">${hsImg}<span class="${vColor}">${vAg.nome}</span></div>`;
                    }
                }
            });
            killfeedDiv.innerHTML = kfHtml;

            for (let pid in frame.jogadores) {
                let p = frame.jogadores[pid]; let card = document.getElementById('card-' + pid); if (!card) continue;
                if (!p.vivo) card.classList.add('dead'); else card.classList.remove('dead');
                
                let hpTxt = document.getElementById('hpt-' + pid); 
                hpTxt.innerText = p.hp; hpTxt.className = p.hp > 30 ? 'hp-text' : 'hp-text low';
                
                let armTxt = document.getElementById('arm-' + pid);
                armTxt.innerText = p.armor > 0 ? '(' + p.armor + ')' : '';
                document.getElementById('inv-arm-'+pid).style.opacity = p.armor > 0 ? '1' : '0.2';
                document.getElementById('cred-' + pid).innerText = p.creds + ' ¤';
                
                let w = document.getElementById('weap-' + pid); if(p.arma) { w.src = p.arma; w.style.display = 'block'; } else { w.style.display = 'none'; }
                let k = document.getElementById('knife-'+pid); if(p.arma) { k.src = p.arma; k.style.display = 'block'; } else { k.style.display = 'none'; }
                
                // Exibe Spike Amarela se o player estiver a carregar
                document.getElementById('yspike-'+pid).style.display = p.spike ? 'block' : 'none';
                
                let habs = p.habilidades;
                document.getElementById('s1-'+pid).className = habs.Ability1 > 0 ? 'skill-icon active' : 'skill-icon';
                document.getElementById('s1-dots-'+pid).innerHTML = '<div class="dot active"></div>'.repeat(habs.Ability1);
                
                document.getElementById('s2-'+pid).className = habs.Ability2 > 0 ? 'skill-icon active' : 'skill-icon';
                document.getElementById('s2-dots-'+pid).innerHTML = '<div class="dot active"></div>'.repeat(habs.Ability2);
                
                document.getElementById('sg-'+pid).className = habs.Grenade > 0 ? 'skill-icon active' : 'skill-icon';
                document.getElementById('sg-dots-'+pid).innerHTML = '<div class="dot active"></div>'.repeat(habs.Grenade);
                
                let isUltReady = habs.Ultimate >= habs.UltMax;
                document.getElementById('su-'+pid).className = isUltReady ? 'skill-icon active' : 'skill-icon';
                let ultDots = '';
                for(let i=0; i<habs.UltMax; i++) { ultDots += `<div class="dot ${i < habs.Ultimate ? 'ult-active' : ''}"></div>`; }
                document.getElementById('su-dots-'+pid).innerHTML = ultDots;
            }
            
            // LÓGICA DO TIMER DA SPIKE (Plantando -> 45s -> Defuse/Boom)
            if (plantFrame > 0 && index >= plantFrame - 20) {
                sHud.style.display = 'flex';
                if (index < plantFrame) {
                    let prog = ((index - (plantFrame - 20)) / 20) * 100;
                    sBar.style.width = prog + '%'; sBar.style.background = '#FFD700';
                    sTxt.innerText = "PLANTING"; sTxt.style.color = '#FFD700';
                } else {
                    let elapsed = (index - plantFrame) / 5;
                    let left = 45.0 - elapsed;
                    
                    if (defuseFrame > 0 && index >= defuseFrame) {
                        sBar.style.width = '100%'; sBar.style.background = '#00FFCC';
                        sTxt.innerText = "DEFUSED"; sTxt.style.color = '#00FFCC';
                    } else if (left <= 0) {
                        sBar.style.width = '0%';
                        sTxt.innerText = "DETONATED"; sTxt.style.color = '#FF4655';
                    } else {
                        sBar.style.width = ((left / 45) * 100) + '%'; sBar.style.background = '#FF4655';
                        sTxt.innerText = left.toFixed(1); sTxt.style.color = '#FF4655';
                    }
                }
            } else {
                sHud.style.display = 'none';
            }

            for (let pid in frame.jogadores) {
                let p = frame.jogadores[pid];
                if (!p.vivo && p.x !== -100) {
                    let px = (p.x / 100) * canvas.width; let py = (p.y / 100) * canvas.height;
                    let isLeft = false; for(let i=0; i<teamLeftIds.length; i++) if(String(teamLeftIds[i]) === String(pid)) isLeft = true;
                    ctx.strokeStyle = isLeft ? ringColorLeft : ringColorRight; ctx.lineWidth = 3;
                    ctx.beginPath(); ctx.moveTo(px - 7, py - 7); ctx.lineTo(px + 7, py + 7); ctx.moveTo(px + 7, py - 7); ctx.lineTo(px - 7, py + 7); ctx.stroke();
                }
            }
            
            for (let pid in frame.jogadores) {
                let p = frame.jogadores[pid];
                if (p.vivo) {
                    let px = (p.x / 100) * canvas.width; let py = (p.y / 100) * canvas.height;
                    let isLeft = false; for(let i=0; i<teamLeftIds.length; i++) if(String(teamLeftIds[i]) === String(pid)) isLeft = true;
                    let imgAgente = imgCache[agentesDb[pid].icone];
                    
                    if (imgAgente && imgAgente.complete) {
                        ctx.save(); ctx.beginPath(); ctx.arc(px, py, 14, 0, 2 * Math.PI); ctx.clip();
                        ctx.drawImage(imgAgente, px - 14, py - 14, 28, 28); ctx.restore();
                    } else { ctx.fillStyle = isLeft ? ringColorLeft : ringColorRight; ctx.beginPath(); ctx.arc(px, py, 14, 0, 2 * Math.PI); ctx.fill(); }
                    
                    ctx.beginPath(); ctx.arc(px, py, 14, 0, 2 * Math.PI); ctx.lineWidth = 3; ctx.strokeStyle = isLeft ? ringColorLeft : ringColorRight; ctx.stroke();
                    
                    // Desenha o icone de Spike a piscar no mapa
                    if (p.spike) {
                        ctx.beginPath(); ctx.arc(px, py, 14, 0, 2 * Math.PI); ctx.lineWidth = 4; ctx.strokeStyle = '#FFD700'; ctx.stroke();
                        const bx = px + 10, by = py + 10, r = 9;
                        ctx.beginPath(); ctx.arc(bx, by, r, 0, 2 * Math.PI); ctx.fillStyle = '#1a1a1a'; ctx.fill(); ctx.strokeStyle = '#FFD700'; ctx.lineWidth = 2; ctx.stroke();
                        ctx.beginPath(); ctx.moveTo(bx, by - 6); ctx.lineTo(bx + 5, by + 4); ctx.lineTo(bx - 5, by + 4); ctx.closePath(); ctx.fillStyle = '#FFD700'; ctx.fill();
                        ctx.fillStyle = '#1a1a1a'; ctx.font = 'bold 7px Arial'; ctx.textAlign = 'center'; ctx.fillText('!', bx, by + 4);
                    }
                    if (p.skill_popup) {
                        let imgSkill = imgCache[p.skill_popup];
                        if (imgSkill && imgSkill.complete) {
                            ctx.fillStyle = "rgba(0,0,0,0.8)"; ctx.fillRect(px - 14, py - 45, 28, 28);
                            ctx.strokeStyle = isLeft ? ringColorLeft : ringColorRight; ctx.lineWidth = 2; ctx.strokeRect(px - 14, py - 45, 28, 28);
                            ctx.drawImage(imgSkill, px - 12, py - 43, 24, 24); ctx.beginPath(); ctx.moveTo(px, py - 14); ctx.lineTo(px, py - 17); ctx.strokeStyle = "#FFF"; ctx.lineWidth = 2; ctx.stroke();
                        }
                    }
                }
            }
            let secs = Math.floor(index / 5); clock.innerText = Math.floor(secs / 60).toString().padStart(2, '0') + ":" + (secs % 60).toString().padStart(2, '0'); timeline.value = index;
        }
        
        initCards();
        let isPlaying = false; let currentFrame = 0; let lastTime = 0; const interval = 1000 / 5;
        function loop(timestamp) {
            if (!isPlaying) return; requestAnimationFrame(loop);
            if (timestamp - lastTime > interval) { lastTime = timestamp - ((timestamp - lastTime) % interval); if (currentFrame < frames.length - 1) { currentFrame++; updateUI(currentFrame); } else { isPlaying = false; playBtn.innerText = '▶ PLAY'; } }
        }
        playBtn.addEventListener('click', () => { isPlaying = !isPlaying; playBtn.innerText = isPlaying ? '⏸ PAUSE' : '▶ PLAY'; if (isPlaying) { lastTime = performance.now(); requestAnimationFrame(loop); } });
        timeline.addEventListener('input', (e) => { currentFrame = parseInt(e.target.value); updateUI(currentFrame); });
        setTimeout(() => updateUI(0), 500); 
    </script>
</body>
</html>
"""

html_final = html_template.replace('__DB_STR__', db_str)
html_final = html_final.replace('__FRAMES_STR__', frames_str)
html_final = html_final.replace('__KILLS_STR__', kills_str)
html_final = html_final.replace('__TEAM_LEFT_IDS__', json.dumps(ids_time_left))
html_final = html_final.replace('__URL_MAPA__', url_mapa)
html_final = html_final.replace('__NOME_LEFT__', nome_left)
html_final = html_final.replace('__NOME_RIGHT__', nome_right)
html_final = html_final.replace('__PLACAR_LEFT__', str(score_team_left))
html_final = html_final.replace('__PLACAR_RIGHT__', str(score_team_right))
html_final = html_final.replace('__COLOR_LEFT__', color_left)
html_final = html_final.replace('__COLOR_RIGHT__', color_right)
html_final = html_final.replace('__ROUND_NUM__', str(round_padrao_url))
html_final = html_final.replace('__NOME_MAPA__', nome_mapa.upper())
html_final = html_final.replace('__MAX_FRAMES__', str(len(frames_js)-1))
html_final = html_final.replace('__PLANT_FRAME__', str(p_frame))
html_final = html_final.replace('__DEFUSE_FRAME__', str(d_frame))

# Injeção das Imagens Base64 Locais no HTML
html_final = html_final.replace('__IMG_HS__', img_hs)
html_final = html_final.replace('__IMG_YSPIKE__', img_yspike)
html_final = html_final.replace('__IMG_RSPIKE__', img_rspike)

st.markdown("<style>iframe { background: transparent; }</style>", unsafe_allow_html=True)
components.html(html_final, height=1000)

# ==========================================
# 7. TRACKER HACK NATIVO (ICONES DE VITÓRIA NO RODAPÉ)
# ==========================================
html_rounds_tracker = '<div class="native-tracker">'
for r in numeros_rounds:
    side = cores_rondas.get(r, {}).get('side', '')
    w_type = cores_rondas.get(r, {}).get('type', '')
    ativo = "active" if r == round_padrao_url else ""
    
    # Decide qual ícone mostrar dependendo de como o round acabou
    icon_b64 = img_elim # Eliminação é o padrão
    if 'detonate' in w_type or 'boom' in w_type: icon_b64 = img_boom
    elif 'defuse' in w_type: icon_b64 = img_defuse
        
    icon_html = f'<img src="{icon_b64}" class="trk-icon">' if side else '<div style="height:12px;"></div>'
    
    html_rounds_tracker += f'<a href="?series_id={series_id}&map_num={map_num}&round_num={r}" target="_self" class="native-box {ativo} {side}"><div class="trk-content"><span>{r}</span>{icon_html}</div></a>'
html_rounds_tracker += '</div>'

css_native = """
<style>
    .native-tracker { display: flex; justify-content: center; gap: 6px; margin-top: -128px; position: relative; z-index: 9999; pointer-events: auto; padding: 10px 0; }
    .native-box { width: 36px; height: 42px; display: flex; align-items: center; justify-content: center; background: #0F1923; border-bottom: 3px solid #333; color: #888; font-family: 'Teko', sans-serif; font-size: 20px; font-weight: bold; text-decoration: none !important; transition: 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
    .native-box:hover { background: #1A222C; color: #FFF; transform: translateY(-2px); }
    .trk-content { display: flex; flex-direction: column; align-items: center; justify-content: center; line-height: 1; }
    .trk-icon { height: 12px; margin-top: 3px; opacity: 0.8; }
    
    .native-box.win-left { border-bottom-color: #FF4655; color: #ECE8E1; }
    .native-box.win-right { border-bottom-color: #00FFCC; color: #ECE8E1; }
    .native-box.active { background: #ECE8E1; color: #000; border-bottom-color: #ECE8E1; transform: scale(1.1); box-shadow: 0 0 10px rgba(255,255,255,0.5); }
</style>
"""
st.markdown(css_native + html_rounds_tracker, unsafe_allow_html=True)

#  e so um aviso nada do plat e spike no agente levando ela funcionou