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
        st.session_state.ranking[p]["matches"] += 1

    for p in team_b:
        if p not in st.session_state.ranking:
            st.session_state.ranking[p] = {"total_rp": 0, "matches": 0}
        st.session_state.ranking[p]["total_rp"] += rp_b
        st.session_state.ranking[p]["matches"] += 1

# --- Title ---
st.title("ðŸ† Burracchiadi 2025")

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Add Participants", "Add Game Results", "Ranking"])

# --- Section: Add Participants ---
if menu == "Add Participants":
    st.header("ðŸ‘¥ Add Participants")

    with st.form("add_participant_form"):
        new_participant = st.text_input("Participant Name")
        submitted = st.form_submit_button("Add Participant")
        if submitted and new_participant.strip():
            if new_participant not in st.session_state.participants:
                st.session_state.participants.append(new_participant)
                st.success(f"Participant {new_participant} added!")
            else:
                st.warning("Participant already exists!")

    st.subheader("Upload Participants from CSV")
    uploaded_participants = st.file_uploader("Upload CSV with participants (one column: 'Participant')", type=["csv"], key="upload_participants")
    if uploaded_participants:
        df = pd.read_csv(uploaded_participants)
        if "Participant" in df.columns:
            for p in df["Participant"].dropna().unique():
                if p not in st.session_state.participants:
                    st.session_state.participants.append(p)
            st.success("Participants imported from CSV!")
        else:
            st.error("CSV must contain a 'Participant' column")

    if st.session_state.participants:
        st.subheader("Registered Participants")
        st.write(", ".join(st.session_state.participants))

# --- Section: Add Game Results ---
elif menu == "Add Game Results":
    st.header("ðŸƒ Add Game Results")

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
                    result = {
                        "team_a": team_a,
                        "team_b": team_b,
                        "score_a": score_a,
                        "score_b": score_b
                    }
                    st.session_state.results.append(result)
                    update_ranking(team_a, team_b, score_a, score_b)
                    st.success("Result added successfully!")

        st.subheader("Upload Game Results from CSV")
        uploaded_results = st.file_uploader(
            "Upload CSV with game results (columns: a1, a2, b1, b2, score_a, score_b)", type=["csv"], key="upload_results"
        )
        if uploaded_results:
            df = pd.read_csv(uploaded_results)
            required_cols = {"a1", "a2", "b1", "b2", "score_a", "score_b"}
            if required_cols.issubset(df.columns):
                for _, row in df.iterrows():
                    team_a = [row["a1"], row["a2"]]
                    team_b = [row["b1"], row["b2"]]
                    if all(p in st.session_state.participants for p in team_a + team_b):
                        result = {
                            "team_a": team_a,
                            "team_b": team_b,
                            "score_a": row["score_a"],
                            "score_b": row["score_b"]
                        }
                        st.session_state.results.append(result)
                        update_ranking(team_a, team_b, row["score_a"], row["score_b"])
                st.success("Game results imported from CSV!")
            else:
                st.error("CSV must contain columns: a1, a2, b1, b2, score_a, score_b")

    if st.session_state.results:
        st.subheader("Game History")
        st.table(pd.DataFrame(st.session_state.results))

# --- Section: Ranking ---
elif menu == "Ranking":
    st.header("ðŸ“Š Ranking")

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
            label="â¬‡ï¸ Download Ranking as CSV",
            data=csv,
            file_name="burracchiadi_2025_ranking.csv",
            mime="text/csv"
        )

        st.download_button(
            label="â¬‡ï¸ Download Ranking as Excel",
            data=open("ranking.xlsx", "rb").read(),
            file_name="burracchiadi_2025_ranking.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )