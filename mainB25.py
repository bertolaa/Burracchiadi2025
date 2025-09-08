import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import base64
from io import BytesIO

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

# --- Ranking Calculation with bar chart thumbnails ---
def update_ranking(participants_df, results_df):
    ranking = {p: {"total_rp": 0, "matches": 0, "scores": []} for p in participants_df["Participant"].tolist()}

    for _, result in results_df.iterrows():
        team_a = [result["a1"], result["a2"]]
        team_b = [result["b1"], result["b2"]]
        score_a, score_b = result["score_a"], result["score_b"]
        rp_a, rp_b = calculate_rp(score_a, score_b)

        for p in team_a:
            if p in ranking:
                ranking[p]["total_rp"] += rp_a
                ranking[p]["matches"] += 1
                ranking[p]["scores"].append(rp_a)
        for p in team_b:
            if p in ranking:
                ranking[p]["total_rp"] += rp_b
                ranking[p]["matches"] += 1
                ranking[p]["scores"].append(rp_b)

    def make_barchart(scores):
        if not scores:
            return ""
        fig, ax = plt.subplots(figsize=(2, 0.5))
        ax.bar(range(1, len(scores)+1), scores, color="cornflowerblue", edgecolor="black")
        ax.set_ylim(0, 1000)  # RP max 900
        ax.axis("off")
        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f'<img src="data:image/png;base64,{img_b64}" width="120" height="30">'

    ranking_data = []
    for participant, stats in ranking.items():
        avg_rp = stats["total_rp"] / stats["matches"] if stats["matches"] > 0 else 0
        bar_img = make_barchart(stats["scores"])
        ranking_data.append([
            participant,
            stats["total_rp"],
            stats["matches"],
            round(avg_rp, 2),
            bar_img
        ])

    df = pd.DataFrame(
        ranking_data,
        columns=["Partecipante", "Total RP", "Partite giocate", "Media punteggio", "Punteggi"]
    )
    df = df.sort_values(by=["Media punteggio", "Partite giocate"], ascending=[False, False]).reset_index(drop=True)
    df.index = df.index + 1
    
    
    
    
    return df

# --- Load Data ---
participants_df = load_csv(PARTICIPANTS_FILE, ["Participant"])
results_df = load_csv(RESULTS_FILE, ["a1", "a2", "b1", "b2", "score_a", "score_b"])

# --- Title ---
st.title("🏆 Burracchiadi 2025")

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Classifica", "Manage Participants", "Add / Update Results"], index=0)

# --- Password input for management sections ---
password = st.text_input("Enter Passcode for Management Sections", type="password") if menu != "Classifica" else None

# --- Manage Participants Section ---
if menu == "Manage Participants":
    if password != "Burracchiadi25":
        st.error("Incorrect passcode")
    else:
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

        st.subheader("Load Participants from CSV")
        uploaded_file = st.file_uploader("Upload CSV file with participants", type=["csv"])
        if uploaded_file:
            try:
                csv_participants = pd.read_csv(uploaded_file)
                if "Participant" in csv_participants.columns:
                    participants_df = pd.concat([participants_df, csv_participants[["Participant"]]], ignore_index=True)
                    save_csv(participants_df, PARTICIPANTS_FILE)
                    st.success("Participants loaded and saved!")
                else:
                    st.error("CSV must have a 'Participant' column")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")

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

        st.download_button("Download Participants CSV", participants_df.to_csv(index=False), file_name="participants.csv")

# --- Add / Update Results Section ---
elif menu == "Add / Update Results":
    if password != "Burracchiadi25":
        st.error("Incorrect passcode")
    else:
        st.header("🃏 Add / Update Results")

        # Add new result
        st.subheader("Add Result")
        with st.form("add_result_form"):
            col1, col2 = st.columns(2)
            with col1:
                team_a = st.multiselect("Select 2 Participants for Team A", participants_df["Participant"].tolist(), key="team_a")
                score_a = st.number_input("Score Team A", min_value=0, step=10)
            with col2:
                team_b = st.multiselect("Select 2 Participants for Team B", participants_df["Participant"].tolist(), key="team_b")
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
                    new_result = pd.DataFrame([{"a1": team_a[0], "a2": team_a[1], "b1": team_b[0], "b2": team_b[1], "score_a": score_a, "score_b": score_b}])
                    results_df = pd.concat([results_df, new_result], ignore_index=True)
                    save_csv(results_df, RESULTS_FILE)
                    st.success("Result added and saved!")

        # Load past results from CSV
        st.subheader("Load Past Results from CSV")
        uploaded_file_results = st.file_uploader("Upload CSV file with past results", type=["csv"])
        if uploaded_file_results:
            try:
                csv_results = pd.read_csv(uploaded_file_results)
                expected_cols = ["a1", "a2", "b1", "b2", "score_a", "score_b"]
                if all(col in csv_results.columns for col in expected_cols):
                    results_df = pd.concat([results_df, csv_results[expected_cols]], ignore_index=True)
                    save_csv(results_df, RESULTS_FILE)
                    st.success("Past results loaded and saved!")
                else:
                    st.error(f"CSV file must contain the columns: {expected_cols}")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")

        # Display past results with edit/delete
        if not results_df.empty:
            st.subheader("Past Results")
            for idx, row in results_df.iterrows():
                cols = st.columns([2,2,2,2,1,1])
                cols[0].write(f"{row['a1']} & {row['a2']}")
                cols[1].write(f"{row['b1']} & {row['b2']}")
                cols[2].write(row['score_a'])
                cols[3].write(row['score_b'])
                if cols[4].button("Edit", key=f"edit_r_{idx}"):
                    st.session_state["edit_result"] = idx
                if cols[5].button("Delete", key=f"del_r_{idx}"):
                    results_df = results_df.drop(idx).reset_index(drop=True)
                    save_csv(results_df, RESULTS_FILE)
                    st.experimental_rerun()

            if "edit_result" in st.session_state:
                idx = st.session_state["edit_result"]
                st.subheader("Edit Result")
                with st.form("edit_result_form"):
                    team_a_edit = st.multiselect("Team A", participants_df["Participant"].tolist(), default=[results_df.at[idx,"a1"], results_df.at[idx,"a2"]])
                    team_b_edit = st.multiselect("Team B", participants_df["Participant"].tolist(), default=[results_df.at[idx,"b1"], results_df.at[idx,"b2"]])
                    score_a_edit = st.number_input("Score Team A", value=int(results_df.at[idx,"score_a"]), min_value=0, step=10)
                    score_b_edit = st.number_input("Score Team B", value=int(results_df.at[idx,"score_b"]), min_value=0, step=10)
                    save_edit = st.form_submit_button("Save Changes")
                    if save_edit:
                        if len(team_a_edit) != 2 or len(team_b_edit) != 2:
                            st.error("Each team must have exactly 2 participants!")
                        elif set(team_a_edit) & set(team_b_edit):
                            st.error("A participant cannot play in both teams!")
                        else:
                            results_df.at[idx,"a1"], results_df.at[idx,"a2"] = team_a_edit
                            results_df.at[idx,"b1"], results_df.at[idx,"b2"] = team_b_edit
                            results_df.at[idx,"score_a"] = score_a_edit
                            results_df.at[idx,"score_b"] = score_b_edit
                            save_csv(results_df, RESULTS_FILE)
                            del st.session_state["edit_result"]
                            st.success("Result updated!")
                            st.experimental_rerun()

        st.download_button("Download Results CSV", results_df.to_csv(index=False), file_name="results.csv")

# --- Ranking Section ---
elif menu == "Classifica":
    st.header("📊 Classifica")
    if participants_df.empty:
        st.info("Nessun partecipante")
    else:
        ranking_df = update_ranking(participants_df, results_df)

        # Build detailed RP history and match info
        detailed_ranking = {
            p: {"scores": [], "details": []}
            for p in participants_df["Participant"].tolist()
        }

        for _, result in results_df.iterrows():
            team_a = [result["a1"], result["a2"]]
            team_b = [result["b1"], result["b2"]]
            score_a, score_b = result["score_a"], result["score_b"]
            rp_a, rp_b = calculate_rp(score_a, score_b)

            for p in team_a:
                if p in detailed_ranking:
                    detailed_ranking[p]["scores"].append(rp_a)
                    detailed_ranking[p]["details"].append({
                        "team": "A",
                        "opponents": team_b,
                        "score_a": score_a,
                        "score_b": score_b,
                        "rp": rp_a
                    })
            for p in team_b:
                if p in detailed_ranking:
                    detailed_ranking[p]["scores"].append(rp_b)
                    detailed_ranking[p]["details"].append({
                        "team": "B",
                        "opponents": team_a,
                        "score_a": score_a,
                        "score_b": score_b,
                        "rp": rp_b
                    })

        # Highlight rows
        def highlight_rows(row):
            if row["Partite giocate"] >= 10:
                return ["background-color: lightgreen; text-align: center" for _ in row]
            elif row["Partite giocate"] >= 5:
                return ["background-color: khaki; text-align: center" for _ in row]
            else:
                return ["background-color: lightcoral; text-align: center" for _ in row]

        styled_df = ranking_df.style.apply(highlight_rows, axis=1)
        st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)

        # Add expandable details per participant
        for i, row in ranking_df.iterrows():
            participant = row["Partecipante"]
            with st.expander(f"📈 Dettagli per {participant}"):
                scores = detailed_ranking[participant]["scores"]
                details = detailed_ranking[participant]["details"]

                # Line chart of RP progression
                fig, ax = plt.subplots()
                ax.plot(range(1, len(scores)+1), scores, marker='o', linestyle='-', color='blue')
                ax.set_title("Progressione RP")
                ax.set_xlabel("Partita #")
                ax.set_ylabel("RP")
                ax.grid(True)
                st.pyplot(fig)

                # Match details
                st.subheader("Dettagli partite")
                for d in details:
                    st.write(
                        f"Squadra {d['team']} vs {d['opponents'][0]} & {d['opponents'][1]} | "
                        f"Punteggio: {d['score_a']} - {d['score_b']} | RP: {d['rp']}"
                    )
