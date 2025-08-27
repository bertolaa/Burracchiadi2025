import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Burracchiadi 2025", layout="wide")

# --- File paths ---
PARTICIPANTS_FILE = "participants.csv"
RESULTS_FILE = "results.csv"

# --- Load participants ---
def load_participants():
    if os.path.exists(PARTICIPANTS_FILE):
        return pd.read_csv(PARTICIPANTS_FILE)["Participant"].tolist()
    return []

def save_participants(participants):
    pd.DataFrame(participants, columns=["Participant"]).to_csv(PARTICIPANTS_FILE, index=False)

# --- Load results ---
def load_results():
    if os.path.exists(RESULTS_FILE):
        df = pd.read_csv(RESULTS_FILE)
        return df.to_dict("records")
    return []

def save_results(results):
    pd.DataFrame(results).to_csv(RESULTS_FILE, index=False)

# --- RP Calculation ---
def calculate_rp(score_a, score_b):
    diff = abs(score_a - score_b)
    if diff <= 100:
        return (600, 400) if score_a > score_b else (400, 600)
    elif diff <= 300:
        return (700, 300) if score_a > score_b else (300, 700)
    else:
        return (800, 200) if score_a > score_b else (200, 800)

# --- Ranking Calculation ---
def update_ranking(results):
    ranking = {}
    for result in results:
        team_a = [result["a1"], result["a2"]]
        team_b = [result["b1"], result["b2"]]
        score_a, score_b = result["score_a"], result["score_b"]
        rp_a, rp_b = calculate_rp(score_a, score_b)

        for p in team_a:
            if p not in ranking:
                ranking[p] = {"total_rp": 0, "matches": 0}
            ranking[p]["total_rp"] += rp_a
            ranking[p]["matches"] += 1

        for p in team_b:
            if p not in ranking:
                ranking[p] = {"total_rp": 0, "matches": 0}
            ranking[p]["total_rp"] += rp_b
            ranking[p]["matches"] += 1

    ranking_data = []
    for participant, stats in ranking.items():
        avg_rp = stats["total_rp"] / stats["matches"] if stats["matches"] > 0 else 0
        ranking_data.append([participant, stats["total_rp"], stats["matches"], round(avg_rp, 2)])

    df = pd.DataFrame(ranking_data, columns=["Participant", "Total RP", "Matches Played", "Average RP"])
    df = df.sort_values(by=["Average RP", "Matches Played"], ascending=[False, False]).reset_index(drop=True)
    return df

# --- Initialize data ---
participants = load_participants()
results = load_results()

# --- Title ---
st.title("🏆 Burracchiadi 2025")

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Manage Participants", "Add / Update Results", "Ranking"])

# --- Manage Participants ---
if menu == "Manage Participants":
    st.header("👥 Manage Participants")

    with st.form("add_participant_form"):
        new_participant = st.text_input("Participant Name")
        submitted = st.form_submit_button("Add Participant")
        if submitted and new_participant.strip():
            if new_participant not in participants:
                participants.append(new_participant)
                save_participants(participants)
                st.success(f"Participant {new_participant} added!")
            else:
                st.warning("Participant already exists!")

    if participants:
        st.subheader("Registered Participants")
        st.write(", ".join(participants))

# --- Add / Update Results ---
elif menu == "Add / Update Results":
    st.header("🃏 Add / Update Game Results")

    if len(participants) < 4:
        st.warning("You need at least 4 participants to add results!")
    else:
        with st.form("add_result_form"):
            col1, col2 = st.columns(2)
            with col1:
                team_a = st.multiselect("Select 2 Participants for Team A", participants, key="team_a")
                score_a = st.number_input("Score Team A", min_value=0, step=10)
            with col2:
                team_b = st.multiselect("Select 2 Participants for Team B", participants, key="team_b")
                score_b = st.number_input("Score Team B", min_value=0, step=10)

            result_submit = st.form_submit_button("Add Result")
            if result_submit:
                if len(team_a) != 2 or len(team_b) != 2:
                    st.error("Each team must have exactly 2 participants!")
                elif set(team_a) & set(team_b):
                    st.error("A participant cannot play in both teams!")
                elif score_a < 2000 and score_b < 2000:
                    st.error("At least one team must reach 2000 points to win!")
                else:
                    result = {"a1": team_a[0], "a2": team_a[1], "b1": team_b[0], "b2": team_b[1], "score_a": score_a, "score_b": score_b}
                    results.append(result)
                    save_results(results)
                    st.success("Result added and saved!")

    if results:
        st.subheader("Game History (from file)")
        st.dataframe(pd.DataFrame(results))

# --- Ranking ---
elif menu == "Ranking":
    st.header("📊 Ranking")

    if not results:
        st.info("No results yet. Rankings will appear here after games are played.")
    else:
        ranking_df = update_ranking(results)

        # Alternate row coloring
        def highlight_rows(row):
            return ["background-color: #f2f2f2" if row.name % 2 == 0 else "background-color: white" for _ in row]

        st.dataframe(ranking_df.style.apply(highlight_rows, axis=1))