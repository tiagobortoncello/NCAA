import streamlit as st
import pandas as pd
import numpy as np
import random

# Configuração da página
st.set_page_config(page_title="NCAA Dynasty Simulator", layout="wide")
st.title("Simulador de Dinastia NCAA: Vitórias e Calendários")

# Carregar dados da Excel (com correção de tipos)
@st.cache_data
def load_data(file_path):
    teams = pd.read_excel(file_path, sheet_name='GlobalTeams')
    team_season = pd.read_excel(file_path, sheet_name='TeamSeason')
    games = pd.read_excel(file_path, sheet_name='Games')

    # CORREÇÃO: Converte Prestige para número (evita datetime)
    team_season['Prestige'] = pd.to_numeric(team_season['Prestige'], errors='coerce')
    team_season['Prestige'] = team_season['Prestige'].fillna(3.0)  # Valor padrão

    return teams, team_season, games

file_path = 'NCAA Dynasty.xlsx'  # Certifique-se de que o arquivo está no repositório
teams_df, team_season_df, games_df = load_data(file_path)

# Função para calcular probabilidade de vitória (modelo logístico simples)
def win_probability(home_overall, away_overall, home_prestige, away_prestige):
    diff = (home_overall + home_prestige * 0.1) - (away_overall + away_prestige * 0.1)
    prob_home = 1 / (1 + np.exp(-diff / 10))
    return prob_home

# Sidebar para seleção
st.sidebar.header("Configurações")
selected_team = st.sidebar.selectbox("Selecione a Equipe", team_season_df['Team'].unique())
num_simulations = st.sidebar.slider("Número de Simulações", 100, 10000, 1000)
season = st.sidebar.selectbox("Temporada", team_season_df['Season'].unique())

# Filtrar dados da equipe selecionada
team_data = team_season_df[(team_season_df['Team'] == selected_team) & (team_season_df['Season'] == season)].iloc[0]
home_overall = team_data['Overall']
home_prestige = team_data['Prestige']  # Já é float graças à correção

# Seção: Cenários de Vitórias
st.header("Cenários de Vitórias")
st.write(f"Equipe: **{selected_team}** | Overall: {home_overall} | Prestige: {home_prestige:.1f}")

# Oponentes possíveis (baseado em conferência ou aleatórios)
conference = team_data['Conference']
opponents_df = team_season_df[(team_season_df['Conference'] == conference) & (team_season_df['Team'] != selected_team)]
if len(opponents_df) == 0:
    opponents_df = team_season_df.sample(min(10, len(team_season_df)))

st.subheader("Simulação de Jogos Restantes (12 jogos)")
num_games = 12
simulated_wins = []

for _ in range(num_simulations):
    wins = 0
    sample_opps = opponents_df.sample(min(num_games, len(opponents_df)), replace=False)
    
    for _, opp in sample_opps.iterrows():
        opp_overall = opp['Overall']
        opp_prestige = opp['Prestige']  # Já é float
        prob = win_probability(home_overall, opp_overall, home_prestige, opp_prestige)
        if random.random() < prob:
            wins += 1
    simulated_wins.append(wins)

avg_wins = np.mean(simulated_wins)
win_prob_playoff = np.mean(np.array(simulated_wins) >= 10) * 100
st.metric("Vitórias Médias Projetadas", f"{avg_wins:.1f}", delta=f"+{win_prob_playoff:.1f}% chance de Playoff")

# Tabela de probabilidades vs. oponentes
probs_df = pd.DataFrame({
    'Oponente': opponents_df['Team'].head(10).values,
    'Prob. Vitória (%)': [
        win_probability(home_overall, opp['Overall'], home_prestige, opp['Prestige']) * 100
        for _, opp in opponents_df.head(10).iterrows()
    ]
})
st.table(probs_df)

# Seção: Geração de Calendários
st.header("Gerador de Calendários")
st.write("Gera um calendário de 12 jogos regulares + 1 bowl game.")

if st.button("Gerar Calendário para 2025"):
    schedule = []
    
    # 6 jogos intra-conferência + 6 inter-conferência
    intra_opps = opponents_df.sample(min(6, len(opponents_df)), replace=False)['Team'].tolist()
    inter_opps = team_season_df[~team_season_df['Conference'].isin([conference])].sample(6, replace=True)['Team'].tolist()
    
    all_opps = intra_opps + inter_opps
    random.shuffle(all_opps)
    
    for i, opp in enumerate(all_opps, 1):
        opp_row = team_season_df[team_season_df['Team'] == opp]
        if not opp_row.empty:
            opp_overall = opp_row['Overall'].iloc[0]
            opp_prestige = opp_row['Prestige'].iloc[0]
        else:
            opp_overall = 75
            opp_prestige = 3.0
        
        prob = win_probability(home_overall, opp_overall, home_prestige, opp_prestige)
        score_home = int(20 + random.gauss(20, 10)) if random.random() < prob else int(20 + random.gauss(10, 5))
        score_away = int(20 + random.gauss(20, 10)) if random.random() >= prob else int(20 + random.gauss(10, 5))
        result = "W" if score_home > score_away else "L"
        
        schedule.append({
            'Semana': i,
            'Casa/Fora': random.choice(['Casa', 'Fora']),
            'Oponente': opp,
            'Placar': f"{score_home}-{score_away}",
            'Resultado': result
        })
    
    # Bowl Game: vs. melhor equipe geral
    bowl_opp = team_season_df.nlargest(1, 'Overall')['Team'].iloc[0]
    bowl_row = team_season_df[team_season_df['Team'] == bowl_opp]
    if not bowl_row.empty:
        bowl_overall = bowl_row['Overall'].iloc[0]
        bowl_prestige = bowl_row['Prestige'].iloc[0]
    else:
        bowl_overall = 85
        bowl_prestige = 5.0
    
    bowl_prob = win_probability(home_overall, bowl_overall, home_prestige, bowl_prestige)
    bowl_home = int(30 + random.gauss(15, 8)) if random.random() < bowl_prob else int(25 + random.gauss(10, 5))
    bowl_away = int(30 + random.gauss(15, 8)) if random.random() >= bowl_prob else int(25 + random.gauss(10, 5))
    
    schedule.append({
        'Semana': 'Bowl',
        'Casa/Fora': 'Neutro',
        'Oponente': bowl_opp,
        'Placar': f"{bowl_home}-{bowl_away}",
        'Resultado': "W" if bowl_home > bowl_away else "L"
    })
    
    schedule_df = pd.DataFrame(schedule)
    st.table(schedule_df)
    total_wins = schedule_df['Resultado'].value_counts().get('W', 0)
    st.success(f"Total de Vitórias no Calendário: {total_wins}/13")

# Rodapé
st.sidebar.markdown("---")
st.sidebar.info("Dados baseados em NCAA Dynasty.xlsx. Modelo probabilístico simplificado.")
