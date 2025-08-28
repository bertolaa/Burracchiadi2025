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
def update_ranking(results_df, participants_df):
    ranking = {p: {"total_rp": 0, "matches": 0} for p in participants_df["Participant"].tolist()}

    for _, result in results_df.iterrows():
        team_a = [result["a1"], result["a2"]]
        team_b = [result["b1"], result["b2"]]
        score_a, score_b = result["score_a"], result["score_b"]
        rp_a, rp_b = calculate_rp(score_a, score_b)

        for p in team_a:
            ranking[p]["total_rp"] += rp_a
            ranking[p]["matches"] += 1

        for p in team_b:
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

    with st.form("add_participant_form"):
        new_participant = st.text_input("Enter new participant name")
        add_submit = st.form_submit_button("Add Participant")
        if add_submit and new_participant:
            if new_participant not in participants_df["Participant"].values:
                participants_df = pd.concat([participants_df, pd.DataFrame([[new_participant]], columns=["Participant"])], ignore_index=True)
                save_csv(participants_df, PARTICIPANTS_FILE)
                st.success(f"Participant {new_participant} added!")
            else:
                st.warning("This participant already exists!")

    st.subheader("Participants List")
    for idx, row in participants_df.iterrows():
        col1, col2 = st.columns([3, 1])
        col1.write(row["Participant"])
        if col2.button("Delete", key=f"del_{idx}"):
            participants_df = participants_df.drop(idx).reset_index(drop=True)
            save_csv(participants_df, PARTICIPANTS_FILE)
            st.experimental_rerun()

# --- Add / Update Results ---
elif menu == "Add / Update Results":
    st.header("🃏 Add / Update Results")

    passcode = st.text_input("Enter Passcode", type="password")
    if passcode == "Burracchiadi25":
        participants = participants_df["Participant"].tolist()

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
                        new_result = pd.DataFrame([{ "a1": team_a[0], "a2": team_a[1], "b1": team_b[0], "b2": team_b[1], "score_a": score_a, "score_b": score_b }])
                        results_df = pd.concat([results_df, new_result], ignore_index=True)
                        save_csv(results_df, RESULTS_FILE)
                        st.success("Result added and saved!")

        if not results_df.empty:
            st.subheader("Game History")
            st.dataframe(results_df)
            for idx, row in results_df.iterrows():
                if st.button("Delete", key=f"res_del_{idx}"):
                    results_df = results_df.drop(idx).reset_index(drop=True)
                    save_csv(results_df, RESULTS_FILE)
                    st.experimental_rerun()

    elif passcode:
        st.error("Incorrect passcode")

# --- Ranking ---
elif menu == "Ranking":
    st.header("📊 Classifica")

    ranking_df = update_ranking(results_df, participants_df)

    def style_rows(row):
        if row["Partite giocate"] >= 10:
            return ["background-color: lightgreen; text-align: center"] * len(row)
        elif row["Partite giocate"] >= 5:
            return ["background-color: khaki; text-align: center"] * len(row)
        else:
            return ["background-color: lightcoral; text-align: center"] * len(row)

    st.dataframe(ranking_df.style.apply(style_rows, axis=1).format({"Media punteggio": "{:.2f}"}))
