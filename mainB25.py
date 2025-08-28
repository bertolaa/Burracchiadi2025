import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Burracchiadi 2025", layout="wide")

# --- File paths ---
PARTICIPANTS_FILE = "participants.csv"
RESULTS_FILE = "results.csv"

# --- Load & Save CSV Helpers ---
def load_csv(file, cols):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=cols)

def save_csv(df, file):
    df.to_csv(file, index=False)

# --- RP Calculation ---
def calculate_rp(score_a, score_b):
    diff = abs(score_a - score_b)
    if diff <= 99:
        return (500, 500)
    elif diff <= 299:
        return (600, 400) if score_a > score_b else (400, 600)
    elif diff <= 499:
        return (700, 300) if score_a > score_b else (300, 700)
    elif diff <= 699:
        return (750, 250) if score_a > score_b else (250, 750)
    elif diff <= 999:
        return (800, 200) if score_a > score_b else (200, 800)
    else:
        return (900, 100) if score_a > score_b else (100, 900)

# --- Ranking Calculation ---
def update_ranking(participants_df, results_df):
    ranking = {p: {"total_rp": 0, "matches": 0} for p in participants_df["Participant"].tolist()}

    for _, result in results_df.iterrows():
        team_a = [result["a1"], result["a2"]]
        team_b = [result["b1"], result["b2"]]
        score_a, score_b = result["score_a"], result["score_b"]
        rp_a, rp_b = calculate_rp(score_a, score_b)

        for p in team_a:
            if p in ranking:
                ranking[p]["total_rp"] += rp_a
                ranking[p]["matches"] += 1
        for p in team_b:
            if p in ranking:
                ranking[p]["total_rp"] += rp_b
                ranking[p]["matches"] += 1

    ranking_data = []
    for participant, stats in ranking.items():
        avg_rp = stats["total_rp"] / stats["matches"] if stats["matches"] > 0 else 0
        ranking_data.append([participant, stats["total_rp"], stats["matches"], round(avg_rp, 2)])

    df = pd.DataFrame(ranking_data, columns=["Participant", "Total RP", "Partite giocate", "Media punteggio"])
    df = df.sort_values(by=["Media punteggio", "Partite giocate"], ascending=[False, False]).reset_index(drop=True)
    df.index = df.index + 1
    return df

# --- Load Data ---
participants_df = load_csv(PARTICIPANTS_FILE, ["Participant"])
results_df = load_csv(RESULTS_FILE, ["a1", "a2", "b1", "b2", "score_a", "score_b"])

# --- Title ---
st.title("🏆 Burracchiadi 2025")

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Ranking", "Manage Participants", "Add / Update Results"], index=0)

# --- Manage Participants ---
if menu == "Manage Participants":
    st.header("👥 Manage Participants")

    st.subheader("Add Participant")
    with st.form("add_participant_form"):
        new_participant = st.text_input("Participant name")
        submit_participant = st.form_submit_button("Add")
        if submit_participant and new_participant:
            if new_participant not in participants_df["Participant"].values:
                participants_df = pd.concat([participants_df, pd.DataFrame([[new_participant]], columns=["Participant"])], ignore_index=True)
                save_csv(participants_df, PARTICIPANTS_FILE)
                st.success(f"Added {new_participant}")
            else:
                st.error("Participant already exists")

    st.subheader("Participants List")
    for idx, row in participants_df.iterrows():
        cols = st.columns([3,1,1])
        cols[0].write(row["Participant"])
        if cols[1].button("Edit", key=f"edit_p_{idx}"):
            st.session_state["edit_participant"] = idx
        if cols[2].button("Delete", key=f"del_p_{idx}"):
            participants_df = participants_df.drop(idx).reset_index(drop=True)
            save_csv(participants_df, PARTICIPANTS_FILE)
            st.experimental_rerun()

    if "edit_participant" in st.session_state:
        idx = st.session_state["edit_participant"]
        st.subheader("Edit Participant")
        with st.form("edit_participant_form"):
            updated_name = st.text_input("Name", participants_df.at[idx, "Participant"])
            save_changes = st.form_submit_button("Save Changes")
            if save_changes and updated_name:
                participants_df.at[idx, "Participant"] = updated_name
                save_csv(participants_df, PARTICIPANTS_FILE)
                del st.session_state["edit_participant"]
                st.success("Participant updated!")
                st.experimental_rerun()

# --- Add / Update Results ---
elif menu == "Add / Update Results":
    st.header("🃏 Add / Update Results")

    passcode = st.text_input("Enter Passcode", type="password")
    if passcode == "Burracchiadi25":
        participants = participants_df["Participant"].tolist()

        st.subheader("Add Result")
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
                    new_result = pd.DataFrame([{ "a1": team_a[0], "a2": team_a[1], "b1": team_b[0], "b2": team_b[1], "score_a": score_a, "score_b": score_b }])
                    results_df = pd.concat([results_df, new_result], ignore_index=True)
                    save_csv(results_df, RESULTS_FILE)
                    st.success("Result added and saved!")

        st.subheader("Load Past Results from CSV")
        uploaded_file = st.file_uploader("Upload CSV file with past results", type=["csv"])
        if uploaded_file:
            try:
                csv_results = pd.read_csv(uploaded_file)
                expected_cols = {"a1", "a2", "b1", "b2", "score_a", "score_b"}
                if expected_cols.issubset(csv_results.columns):
                    results_df = pd.concat([results_df, csv_results[expected_cols]], ignore_index=True)
                    save_csv(results_df, RESULTS_FILE)
                    st.success("Past results have been loaded and saved!")
                else:
                    st.error(f"CSV file must contain the following columns: {expected_cols}")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")

        if not results_df.empty:
            st.subheader("Game History")
            for idx, row in results_df.iterrows():
                cols = st.columns([6,1,1])
                cols[0].write(f"{row['a1']} & {row['a2']} ({row['score_a']}) vs {row['b1']} & {row['b2']} ({row['score_b']})")
                if cols[1].button("Edit", key=f"edit_r_{idx}"):
                    st.session_state["edit_result"] = idx
                if cols[2].button("Delete", key=f"del_r_{idx}"):
                    results_df = results_df.drop(idx).reset_index(drop=True)
                    save_csv(results_df, RESULTS_FILE)
                    st.experimental_rerun()

            if "edit_result" in st.session_state:
                idx = st.session_state["edit_result"]
                st.subheader("Edit Result")
                with st.form("edit_result_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        team_a = st.multiselect("Team A", participants, default=[results_df.at[idx, "a1"], results_df.at[idx, "a2"]])
                        score_a = st.number_input("Score Team A", value=int(results_df.at[idx, "score_a"]))
                    with col2:
                        team_b = st.multiselect("Team B", participants, default=[results_df.at[idx, "b1"], results_df.at[idx, "b2"]])
                        score_b = st.number_input("Score Team B", value=int(results_df.at[idx, "score_b"]))

                    save_changes = st.form_submit_button("Save Changes")
                    if save_changes:
                        if len(team_a) != 2 or len(team_b) != 2:
                            st.error("Each team must have exactly 2 participants!")
                        elif set(team_a) & set(team_b):
                            st.error("A participant cannot play in both teams!")
                        else:
                            results_df.at[idx, "a1"], results_df.at[idx, "a2"] = team_a
                            results_df.at[idx, "b1"], results_df.at[idx, "b2"] = team_b
                            results_df.at[idx, "score_a"] = score_a
                            results_df.at[idx, "score_b"] = score_b
                            save_csv(results_df, RESULTS_FILE)
                            del st.session_state["edit_result"]
                            st.success("Result updated!")
                            st.experimental_rerun()

# --- Ranking ---
elif menu == "Ranking":
    st.header("📊 Ranking")

    if participants_df.empty:
        st.info("No participants yet.")
    else:
        ranking_df = update_ranking(participants_df, results_df)

        def highlight_rows(row):
            if row["Partite giocate"] >= 10:
                return ["background-color: lightgreen; text-align: center" for _ in row]
            elif row["Partite giocate"] >= 5:
                return ["background-color: khaki; text-align: center" for _ in row]
            else:
                return ["background-color: lightcoral; text-align: center" for _ in row]

        st.dataframe(ranking_df.style.apply(highlight_rows, axis=1).format({"Media punteggio": "{:.2f}"}))
