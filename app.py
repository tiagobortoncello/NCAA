import streamlit as st
import pandas as pd
import numpy as np
import random

# Configuração
st.set_page_config(page_title="NCAA Season Simulator", layout="wide")
st.title("Simulador de Temporada NCAA")

# Carregar dados
@st.cache_data
def load_data(file_path):
    teams = pd.read_excel(file_path, sheet_name='GlobalTeams')
    team_season = pd.read_excel(file_path, sheet_name='TeamSeason')
    team_season['Prestige'] = pd.to_numeric(team_season['Prestige'], errors='coerce').fillna(3.0)
    return teams, team_season

file_path = "NCAA Dynasty.xlsx"
_, team_season_df = load_data(file_path)

# Função para probabilidade de vitória
def win_probability(home_overall, away_overall, home_prestige, away_prestige):
    diff = (home_overall + home_prestige * 0.1) - (away_overall + away_prestige * 0.1)
    prob_home = 1 / (1 + np.exp(-diff / 10))
    return prob_home

# Parâmetros
season = st.sidebar.selectbox("Temporada", team_season_df["Season"].unique())
num_weeks = st.sidebar.slider("Número de Semanas", 8, 14, 12)
teams_this_season = team_season_df[team_season_df["Season"] == season].copy()

if st.button("Simular Temporada Completa"):
    all_games = []

    for week in range(1, num_weeks + 1):
        week_games = []
        available_teams = teams_this_season["Team"].tolist()
        random.shuffle(available_teams)

        # Cada time joga uma vez por semana (aproximadamente)
        while len(available_teams) >= 2:
            home = available_teams.pop()
            away = available_teams.pop()

            home_data = teams_this_season[teams_this_season["Team"] == home].iloc[0]
            away_data = teams_this_season[teams_this_season["Team"] == away].iloc[0]

            prob = win_probability(home_data["Overall"], away_data["Overall"],
                                   home_data["Prestige"], away_data["Prestige"])

            if random.random() < prob:
                home_score = int(20 + random.gauss(15, 8))
                away_score = int(15 + random.gauss(10, 5))
            else:
                home_score = int(15 + random.gauss(10, 5))
                away_score = int(20 + random.gauss(15, 8))

            result = "Home Win" if home_score > away_score else "Away Win"

            week_games.append({
                "Semana": week,
                "Time Casa": home,
                "Time Fora": away,
                "Placar": f"{home_score}-{away_score}",
                "Vencedor": home if result == "Home Win" else away,
                "Conferência Casa": home_data["Conference"],
                "Conferência Fora": away_data["Conference"]
            })

        all_games.extend(week_games)

    games_df = pd.DataFrame(all_games)
    st.subheader("Resultados Semana a Semana")
    st.dataframe(games_df)

    # Calcular standings
    standings = []

    for team in teams_this_season["Team"]:
        wins = len(games_df[games_df["Vencedor"] == team])
        total_games = len(games_df[(games_df["Time Casa"] == team) | (games_df["Time Fora"] == team)])
        losses = total_games - wins
        conf = teams_this_season[teams_this_season["Team"] == team]["Conference"].iloc[0]

        standings.append({
            "Equipe": team,
            "Conferência": conf,
            "Vitórias": wins,
            "Derrotas": losses,
            "Aproveitamento": wins / total_games if total_games > 0 else 0
        })

    standings_df = pd.DataFrame(standings)
    st.header("🏆 Standings por Conferência")

    for conf in sorted(standings_df["Conferência"].unique()):
        st.subheader(conf)
        conf_df = standings_df[standings_df["Conferência"] == conf].sort_values(
            ["Vitórias", "Aproveitamento"], ascending=[False, False]
        )
        st.table(conf_df.reset_index(drop=True))
