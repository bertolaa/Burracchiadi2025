import streamlit as st
import pandas as pd

st.set_page_config(page_title="Burracchiadi 2025", layout="wide")

# --- Initialize session state ---
if "participants" not in st.session_state:
    st.session_state.participants = []
if "results" not in st.session_state:
    st.session_state.results = []
if "ranking" not in st.session_state:
    st.session_state.ranking = {}  # {participant: {"total_rp": int, "matches": int}}

# --- Helper Functions ---
def calculate_rp(score_a, score_b):
    diff = abs(score_a - score_b)
    if diff <= 100:
        return (600, 400) if score_a > score_b else (400, 600)
    elif diff <= 300:
        return (700, 300) if score_a > score_b else (300, 700)
    else:
        return (800, 200) if score_a > score_b else (200, 800)

def update_ranking(team_a, team_b, score_a, score_b):
    rp_a, rp_b = calculate_rp(score_a, score_b)

    for p in team_a:
        if p not in st.session_state.ranking:
            st.session_state.ranking[p] = {"total_rp": 0, "matches": 0}
        st.session_state.ranking[p]["total_rp"] += rp_a
        st.session_state.ranking[p]["matches"] +=king.get(p, 0) + rp_b

# --- Title ---
st.title("🏆 Burracchiadi 2025")

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Add Teams & Participants", "Add Game Results", "Ranking"])

# --- Section: Add Teams & Participants ---
if menu == "Add Teams & Participants":
    st.header("👥 Add Teams and Participants")

    with st.form("add_participant_form"):
        new_participant = st.text_input("Participant Name")
        submitted = st.form_submit_button("Add Participant")
        if submitted and new_participant.strip():
            if new_participant not in st.session_state.participants:
                st.session_state.participants.append(new_participant)
                st.success(f"Participant {new_participant} added!")
            else:
                st.warning("Participant already exists!")

    st.subheader("Create a Team")
    with st.form("add_team_form"):
        team_name = st.text_input("Team Name")
        team_members = st.multiselect("Select 2 Participants", st.session_state.participants)
        team_submit = st.form_submit_button("Create Team")
        if team_submit:
            if team_name in st.session_state.teams:
                st.warning("Team already exists!")
            elif len(team_members) != 2:
                st.error("A team must have exactly 2 participants!")
            else:
                st.session_state.teams[team_name] = team_members
                st.success(f"Team {team_name} created with {team_members}!")

    if st.session_state.teams:
        st.subheader("Registered Teams")
        for team, members in st.session_state.teams.items():
            st.write(f"**{team}**: {', '.join(members)}")

# --- Section: Add Game Results ---
elif menu == "Add Game Results":
    st.header("🃏 Add Game Results")

    if len(st.session_state.teams) < 2:
        st.warning("You need at least 2 teams to add results!")
    else:
        with st.form("add_result_form"):
            col1, col2 = st.columns(2)
            with col1:
                team_a = st.selectbox("Team A", list(st.session_state.teams.keys()), key="team_a")
                score_a = st.number_input("Score Team A", min_value=0, step=10)
            with col2:
                team_b = st.selectbox("Team B", list(st.session_state.teams.keys()), key="team_b")
                score_b = st.number_input("Score Team B", min_value=0, step=10)

            result_submit = st.form_submit_button("Add Result")
            if result_submit:
                if team_a == team_b:
                    st.error("A team cannot play against itself!")
                elif score_a < 2000 and score_b < 2000:
                    st.error("At least one team must reach 2000 points to win!")
                else:
                    st.session_state.results.append({
                        "team_a": team_a,
                        "team_b": team_b,
                        "score_a": score_a,
                        "score_b": score_b
                    })
                    update_ranking(team_a, team_b, score_a, score_b)
                    st.success("Result added successfully!")

    if st.session_state.results:
        st.subheader("Game History")
        st.table(pd.DataFrame(st.session_state.results))

# --- Section: Ranking ---
elif menu == "Ranking":
    st.header("📊 Ranking")

    if not st.session_state.ranking:
        st.info("No results yet. Rankings will appear here after games are played.")
    else:
        ranking_df = pd.DataFrame(list(st.session_state.ranking.items()), columns=["Participant", "Ranking Points"])
        ranking_df = ranking_df.sort_values(by="Ranking Points", ascending=False).reset_index(drop=True)
        st.table(ranking_df)
