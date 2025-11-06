import streamlit as st
import pandas as pd
import numpy as np
import random

# Configuração
st.set_page_config(page_title="NCAA Season Simulator", layout="wide")
st.title("🏈 Simulador Completo de Temporada NCAA")

# Carregar dados
@st.cache_data
def load_data(file_path):
    team_season = pd.read_excel(file_path, sheet_name='TeamSeason')
    team_season['Prestige'] = pd.to_numeric(team_season['Prestige'], errors='coerce').fillna(3.0)
    return team_season

file_path = "NCAA Dynasty.xlsx"
team_season_df = load_data(file_path)

# Função de probabilidade de vitória
def win_probability(home_overall, away_overall, home_prestige, away_prestige):
    diff = (home_overall + home_prestige * 0.1) - (away_overall + away_prestige * 0.1)
    return 1 / (1 + np.exp(-diff / 10))

# Parâmetros
season = st.sidebar.selectbox("Temporada", team_season_df["Season"].unique())
num_weeks = st.sidebar.slider("Número de Semanas", 8, 14, 12)
teams_this_season = team_season_df[team_season_df["Season"] == season].copy()

# Função de simulação de jogo
def simulate_game(home_team, away_team, df):
    home = df[df["Team"] == home_team].iloc[0]
    away = df[df["Team"] == away_team].iloc[0]

    prob = win_probability(home["Overall"], away["Overall"], home["Prestige"], away["Prestige"])
    if random.random() < prob:
        home_score = int(20 + random.gauss(15, 8))
        away_score = int(15 + random.gauss(10, 5))
        winner = home_team
    else:
        home_score = int(15 + random.gauss(10, 5))
        away_score = int(20 + random.gauss(15, 8))
        winner = away_team

    return {
        "Time Casa": home_team,
        "Time Fora": away_team,
        "Placar": f"{home_score}-{away_score}",
        "Vencedor": winner,
        "Conferência Casa": home["Conference"],
        "Conferência Fora": away["Conference"]
    }

if st.button("Simular Temporada Completa"):
    all_games = []

    # 🔹 Temporada regular
    for week in range(1, num_weeks + 1):
        available_teams = teams_this_season["Team"].tolist()
        random.shuffle(available_teams)
        week_games = []

        while len(available_teams) >= 2:
            home = available_teams.pop()
            away = available_teams.pop()
            week_games.append(simulate_game(home, away, teams_this_season) | {"Semana": week})

        all_games.extend(week_games)

    games_df = pd.DataFrame(all_games)
    st.subheader("📅 Resultados Semana a Semana")
    st.dataframe(games_df)

    # 🔹 Standings
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

    # Mostrar standings por conferência
    st.header("🏆 Standings por Conferência")
    for conf in sorted(standings_df["Conferência"].unique()):
        st.subheader(conf)
        st.dataframe(
            standings_df[standings_df["Conferência"] == conf]
            .sort_values(["Vitórias", "Aproveitamento"], ascending=[False, False])
            .reset_index(drop=True)
        )

    # 🔹 Finais de conferência
    st.header("🥇 Finais de Conferência")

    conf_champs = []
    conf_finals = []

    for conf in sorted(standings_df["Conferência"].unique()):
        conf_teams = standings_df[standings_df["Conferência"] == conf].sort_values(
            ["Vitórias", "Aproveitamento"], ascending=[False, False]
        ).head(2)

        if len(conf_teams) < 2:
            continue

        team1, team2 = conf_teams["Equipe"].iloc[0], conf_teams["Equipe"].iloc[1]
        final_game = simulate_game(team1, team2, teams_this_season)
        conf_finals.append(final_game | {"Semana": "Final Conf", "Conferência": conf})
        conf_champs.append(final_game["Vencedor"])

    conf_finals_df = pd.DataFrame(conf_finals)
    st.dataframe(conf_finals_df)

    # 🔹 Playoff de 12 times
    st.header("🏆 Playoffs Nacionais (12 times)")

    major_confs = ["ACC", "SEC", "Big Ten", "Big 12", "Pac-12", "American"]
    playoff_teams = set()

    # Campeões obrigatórios das principais conferências
    for conf in major_confs:
        champ = (
            standings_df[standings_df["Conferência"] == conf]
            .sort_values(["Vitórias", "Aproveitamento"], ascending=[False, False])
            .head(1)
        )
        if not champ.empty:
            playoff_teams.add(champ["Equipe"].iloc[0])

    # Preenche com os melhores restantes
    remaining = (
        standings_df[~standings_df["Equipe"].isin(playoff_teams)]
        .sort_values(["Vitórias", "Aproveitamento"], ascending=[False, False])
        .head(12 - len(playoff_teams))
    )
    playoff_teams.update(remaining["Equipe"].tolist())

    playoff_df = standings_df[standings_df["Equipe"].isin(playoff_teams)].sort_values(
        ["Vitórias", "Aproveitamento"], ascending=[False, False]
    ).reset_index(drop=True)

    st.dataframe(playoff_df)

    # 🔹 Simulação dos Playoffs
    st.subheader("🏁 Resultados do Playoff")
    playoff_list = playoff_df["Equipe"].tolist()

    # Round 1: 12 times → 6 vencedores
    random.shuffle(playoff_list)
    round1 = []
    for i in range(0, len(playoff_list), 2):
        if i + 1 >= len(playoff_list): break
        g = simulate_game(playoff_list[i], playoff_list[i + 1], teams_this_season)
        round1.append(g)
    winners_r1 = [g["Vencedor"] for g in round1]
    st.write("**Primeira Rodada:**")
    st.dataframe(pd.DataFrame(round1))

    # Round 2: 6 times → 3 vencedores
    random.shuffle(winners_r1)
    round2 = []
    for i in range(0, len(winners_r1), 2):
        if i + 1 >= len(winners_r1): break
        g = simulate_game(winners_r1[i], winners_r1[i + 1], teams_this_season)
        round2.append(g)
    winners_r2 = [g["Vencedor"] for g in round2]
    st.write("**Quartas de Final:**")
    st.dataframe(pd.DataFrame(round2))

    # Round 3: semifinais (se sobrar 3 times, o melhor aproveitamento avança direto)
    if len(winners_r2) == 3:
        bye_team = (
            standings_df[standings_df["Equipe"].isin(winners_r2)]
            .sort_values(["Vitórias", "Aproveitamento"], ascending=[False, False])
            .iloc[0]["Equipe"]
        )
        rest = [t for t in winners_r2 if t != bye_team]
        g = simulate_game(rest[0], rest[1], teams_this_season)
        semifinal_winners = [bye_team, g["Vencedor"]]
        st.write(f"**Semifinal:** {rest[0]} vs {rest[1]}")
    else:
        semifinal_winners = winners_r2[:2]

    # Final nacional
    final_game = simulate_game(semifinal_winners[0], semifinal_winners[1], teams_this_season)
    st.write("**Final Nacional:**")
    st.dataframe(pd.DataFrame([final_game]))
    st.success(f"🏆 Campeão Nacional: **{final_game['Vencedor']}** 🏆")
