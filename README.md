# Projeto de conclusão de curso - O Projeto ainda nao foi colocado 100%, falta o retorno sobre a base de dados.
# 📊 Valorant Tactical Analytics & VCT HUD Replay

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)
![JS](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)

Um ecossistema completo de análise de dados e reprodução tática para partidas de **Valorant**. Este projeto foi desenvolvido para processar grandes volumes de dados brutos de partidas (arquivos JSON), transformando-os em insights estatísticos através de um Dashboard interativo, além de recriar os momentos da partida com um HUD de transmissão premium inspirado no **Valorant Champions Tour (VCT)**.

---

## 🎯 Visão Geral do Projeto

Este sistema foi arquitetado com foco em **Ciência de Dados** e Engenharia de Software para fornecer uma ferramenta analítica profunda. Ele atua em duas frentes principais:
1.  **Dashboard Analítico:** Focado em métricas de performance, economia e eficiência tática (abates, sobrevivência, uso de habilidades e controle financeiro).
2.  **Replay Tático:** Um reprodutor visual em tempo real que mapeia as coordenadas dos jogadores (X, Y) e eventos (Kills, Spike Plant/Defuse) em um minimapa interativo, renderizado nativamente no navegador.

---

## ✨ Funcionalidades Principais

### 📈 Módulo 1: Dashboard Analítico
*   **Métricas de Performance:** Cálculo avançado de KDA, Headshot Percentage, e impacto de dano.
*   **Análise Econômica:** Rastreamento do gerenciamento de créditos e compras de armamento round a round.
*   **Estatísticas de Agentes:** Eficiência no uso de habilidades e geração de pontos de Ultimate.
*   **Visualização de Dados:** Gráficos interativos renderizados de forma responsiva para facilitar a tomada de decisão.

### 🎬 Módulo 2: Replay Tático
*   **Motor Geométrico de Mapa:** Conversão matemática de coordenadas brutas em posições escalonadas no Canvas HTML5, exibindo a movimentação precisa de todos os agentes.
*   **Killfeed Inteligente:** Sistema anti-duplicação de eventos que consome a API oficial da Riot Games para exibir armas, habilidades e assistências dinamicamente.
*   **Mecânica de Spike Realista:** Tracking de posse da Spike, barra de progresso de plant e cronômetro exato de detonação (45 segundos).
*   **Interface Premium:** Design utilizando *True Black*, tipografia oficial e elementos visuais assimétricos que replicam a experiência de uma transmissão profissional de eSports.

---

## 🛠️ Tecnologias e Arquitetura

O projeto adota uma arquitetura orientada a dados, garantindo fluidez mesmo no processamento de replays de alta densidade (milhares de frames por round).

*   **Linguagem Core:** `Python`
*   **Front-end & Web Framework:** `Streamlit`, `HTML5`, `CSS3`, `JavaScript` (Vanilla, Canvas API).
*   **Manipulação de Dados:** `Pandas` e bibliotecas nativas de manipulação estrutural de `JSON`.
*   **Integração Externa:** [Valorant-API.com](https://valorant-api.com/) para extração de assets (ícones de habilidades, armamentos e mapas) via `Requests`.

---

## ⚙️ Guia de Instalação e Execução

### Pré-requisitos
*   **Python 3.9** ou superior.
*   (Opcional) Ambiente virtual (venv/conda) configurado.

### 1. Clonando o Repositório
```bash
git clone [https://github.com/SEU_USUARIO/nome-do-repositorio.git](https://github.com/SEU_USUARIO/nome-do-repositorio.git)
cd nome-do-repositorio
