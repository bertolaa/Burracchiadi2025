import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Burracchiadi 2025", layout="wide")

# --- File paths ---
PARTICIPANTS_FILE = "participants.csv"
RESULTS_FILE = "results.csv"

# --- Initialize session state ---
if "participants" not in st.session_state:
    if os.path.exists(PARTICIPANTS_FILE):
        st.session_state.participants = pd.read_csv(PARTICIPANTS_FILE)["Participant"].tolist()
    else:
        st.session_state.participants = []

if "results" not in st.session_state:
    if os.path.exists(RESULTS_FILE):
        st.session_state.results = pd.read_csv(RESULTS_FILE).to_dict("records")
    else:
        st.session_state.results = []

if "ranking" not in st.session_state:
    st.session_state.ranking = {}

# --- Helper Functions ---
def calculate_rp(score_a, score_b):
    diff = abs(score_a - score_b)
    if diff <= 100:
        return (600, 400) if score_a > score_b else (400, 600)
    elif diff <= 300:
        return (700, 300) if score_a > score_b else (300, 700)
    else:
        return (800, 200) if score_a > score_b else (200, 800)

def update_ranking():
    st.session_state.ranking = {}
    for result in st.session_state.results:
        team_a = [result["a1"], result["a2"]]
        team_b = [result["b1"], result["b2"]]
        score_a, score_b = result["score_a"], result["score_b"]
        rp_a, rp_b = calculate_rp(score_a, score_b)

        for p in team_a:
            if p not in st.session_state.ranking:
                st.session_state.ranking[p] = {"total_rp": 0, "matches": 0}
            st.session_state.ranking[p]["total_rp"] += rp_a
            st.session_state.ranking[p]["matches"] += 1

        for p in team_b:
            if p not in st.session_state.ranking:
                st.session_state.ranking[p] = {"total_rp": 0, "matches": 0}
            st.session_state.ranking[p]["total_rp"] += rp_b
            st.session_state.ranking[p]["matches"] += 1

update_ranking()

# --- Title ---
st.title("🏆 Burracchiadi 2025")

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Manage Participants", "Add Game Results", "Ranking"])

# --- Section: Manage Participants ---
if menu == "Manage Participants":
    st.header("👥 Manage Participants")

    with st.form("add_participant_form"):
        new_participant = st.text_input("Participant Name")
        submitted = st.form_submit_button("Add Participant")
        if submitted and new_participant.strip():
            if new_participant not in st.session_state.participants:
                st.session_state.participants.append(new_participant)
                pd.DataFrame(st.session_state.participants, columns=["Participant"]).to_csv(PARTICIPANTS_FILE, index=False)
                st.success(f"Participant {new_participant} added and saved!")
            else:
                st.warning("Participant already exists!")

    if st.session_state.participants:
        st.subheader("Registered Participants")
        st.write(", ".join(st.session_state.participants))

# --- Section: Add Game Results ---
elif menu == "Add Game Results":
    st.header("🃏 Add / Manage Game Results")

    if len(st.session_state.participants) < 4:
        st.warning("You need at least 4 participants to add results!")
    else:
        with st.form("add_result_form"):
            col1, col2 = st.columns(2)
            with col1:
                team_a = st.multiselect("Select 2 Participants for Team A", st.session_state.participants, key="team_a")
                score_a = st.number_input("Score Team A", min_value=0, step=10)
            with col2:
                team_b = st.multiselect("Select 2 Participants for Team B", st.session_state.participants, key="team_b")
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
                    st.session_state.results.append(result)
                    pd.DataFrame(st.session_state.results).to_csv(RESULTS_FILE, index=False)
                    update_ranking()
                    st.success("Result added and saved!")

    if st.session_state.results:
        st.subheader("Game History")
        results_df = pd.DataFrame(st.session_state.results)
        st.table(results_df)

        # Edit/Delete functionality
        st.subheader("✏️ Edit or 🗑️ Delete Results")
        for i, result in enumerate(st.session_state.results):
            with st.expander(f"Match {i+1}: {result['a1']} & {result['a2']} vs {result['b1']} & {result['b2']}"):
                col1, col2, col3 = st.columns([2,2,1])
                with col1:
                    new_score_a = st.number_input(f"Score for {result['a1']} & {result['a2']}", value=int(result['score_a']), key=f"edit_score_a_{i}")
                with col2:
                    new_score_b = st.number_input(f"Score for {result['b1']} & {result['b2']}", value=int(result['score_b']), key=f"edit_score_b_{i}")
                with col3:
                    if st.button("Save Edit", key=f"save_{i}"):
                        st.session_state.results[i]['score_a'] = new_score_a
                        st.session_state.results[i]['score_b'] = new_score_b
                        pd.DataFrame(st.session_state.results).to_csv(RESULTS_FILE, index=False)
                        update_ranking()
                        st.success("Result updated!")
                if st.button("Delete", key=f"delete_{i}"):
                    st.session_state.results.pop(i)
                    pd.DataFrame(st.session_state.results).to_csv(RESULTS_FILE, index=False)
                    update_ranking()
                    st.warning("Result deleted!")
                    st.experimental_rerun()

# --- Section: Ranking ---
elif menu == "Ranking":
    st.header("📊 Ranking")

    if not st.session_state.ranking:
        st.info("No results yet. Rankings will appear here after games are played.")
    else:
        ranking_data = []
        for participant, stats in st.session_state.ranking.items():
            avg_rp = stats["total_rp"] / stats["matches"] if stats["matches"] > 0 else 0
            ranking_data.append([participant, stats["total_rp"], stats["matches"], round(avg_rp, 2)])

        ranking_df = pd.DataFrame(ranking_data, columns=["Participant", "Total RP", "Matches Played", "Average RP"])
        ranking_df = ranking_df.sort_values(by="Average RP", ascending=False).reset_index(drop=True)
        st.table(ranking_df)

        # Download options
        csv = ranking_df.to_csv(index=False).encode("utf-8")
        ranking_df.to_excel("ranking.xlsx", index=False)

        st.download_button(
            label="⬇️ Download Ranking as CSV",
            data=csv,
            file_name="burracchiadi_2025_ranking.csv",
            mime="text/csv"
        )

        st.download_button(
            label="⬇️ Download Ranking as Excel",
            data=open("ranking.xlsx", "rb").read(),
            file_name="burracchiadi_2025_ranking.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
