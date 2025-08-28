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
def update_ranking(results_df):
    ranking = {}
    for _, result in results_df.iterrows():
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
    df.index = df.index + 1
    return df

# --- Load Data ---
participants_df = load_csv(PARTICIPANTS_FILE, ["Participant"])
results_df = load_csv(RESULTS_FILE, ["a1", "a2", "b1", "b2", "score_a", "score_b"])

# --- Title ---
st.title("🏆 Burracchiadi 2025")

# --- Sidebar Navigation ---
menu = st.sidebar.radio("Navigation", ["Ranking", "Manage Participants", "Manage Results"], index=0)

# --- Manage Participants ---
if menu == "Manage Participants":
    st.header("👥 Manage Participants")

    # Add participant
    with st.form("add_participant_form"):
        new_name = st.text_input("Add new participant")
        add_submit = st.form_submit_button("Add")
        if add_submit and new_name:
            if new_name not in participants_df["Participant"].values:
                participants_df = pd.concat([participants_df, pd.DataFrame({"Participant": [new_name]})], ignore_index=True)
                save_csv(participants_df, PARTICIPANTS_FILE)
                st.success(f"Added participant {new_name}")
            else:
                st.error("Participant already exists!")

    # Display participants
    st.subheader("Participants List")
    for idx, row in participants_df.iterrows():
        col1, col2, col3 = st.columns([4,1,1])
        col1.write(row["Participant"])
        if col2.button("Edit", key=f"edit_part_{idx}"):
            st.session_state["edit_participant"] = idx
        if col3.button("Delete", key=f"delete_part_{idx}"):
            participants_df = participants_df.drop(idx).reset_index(drop=True)
            save_csv(participants_df, PARTICIPANTS_FILE)
            st.experimental_rerun()

    # Edit form
    if "edit_participant" in st.session_state:
        idx = st.session_state["edit_participant"]
        with st.form("edit_participant_form"):
            updated_name = st.text_input("Edit name", value=participants_df.loc[idx, "Participant"])
            update_submit = st.form_submit_button("Update")
            if update_submit and updated_name:
                participants_df.loc[idx, "Participant"] = updated_name
                save_csv(participants_df, PARTICIPANTS_FILE)
                del st.session_state["edit_participant"]
                st.success("Participant updated!")
                st.experimental_rerun()

# --- Manage Results ---
elif menu == "Manage Results":
    st.header("🃏 Manage Results")

    participants = participants_df["Participant"].tolist()

    # Add result
    with st.form("add_result_form"):
        col1, col2 = st.columns(2)
        with col1:
            team_a = st.multiselect("Select 2 Participants for Team A", participants, key="team_a")
            score_a = st.number_input("Score Team A", min_value=0, step=10)
        with col2:
            team_b = st.multiselect("Select 2 Participants for Team B", participants, key="team_b")
            score_b = st.number_input("Score Team B", min_value=0, step=10)
        submit_result = st.form_submit_button("Add Result")
        if submit_result:
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
                st.success("Result added!")

    # Display results
    st.subheader("Results List")
    for idx, row in results_df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([6,2,2,1,1])
        col1.write(f"{row['a1']} & {row['a2']} ({row['score_a']}) vs {row['b1']} & {row['b2']} ({row['score_b']})")
        if col4.button("Edit", key=f"edit_result_{idx}"):
            st.session_state["edit_result"] = idx
        if col5.button("Delete", key=f"delete_result_{idx}"):
            results_df = results_df.drop(idx).reset_index(drop=True)
            save_csv(results_df, RESULTS_FILE)
            st.experimental_rerun()

    # Edit result form
    if "edit_result" in st.session_state:
        idx = st.session_state["edit_result"]
        with st.form("edit_result_form"):
            col1, col2 = st.columns(2)
            with col1:
                team_a = st.multiselect("Edit Team A", participants, default=[results_df.loc[idx,"a1"], results_df.loc[idx,"a2"]])
                score_a = st.number_input("Edit Score Team A", min_value=0, step=10, value=int(results_df.loc[idx,"score_a"]))
            with col2:
                team_b = st.multiselect("Edit Team B", participants, default=[results_df.loc[idx,"b1"], results_df.loc[idx,"b2"]])
                score_b = st.number_input("Edit Score Team B", min_value=0, step=10, value=int(results_df.loc[idx,"score_b"]))
            update_submit = st.form_submit_button("Update Result")
            if update_submit:
                if len(team_a) != 2 or len(team_b) != 2:
                    st.error("Each team must have exactly 2 participants!")
                elif set(team_a) & set(team_b):
                    st.error("A participant cannot play in both teams!")
                elif score_a < 2000 and score_b < 2000:
                    st.error("At least one team must reach 2000 points to win!")
                else:
                    results_df.loc[idx] = [team_a[0], team_a[1], team_b[0], team_b[1], score_a, score_b]
                    save_csv(results_df, RESULTS_FILE)
                    del st.session_state["edit_result"]
                    st.success("Result updated!")
                    st.experimental_rerun()

# --- Ranking ---
elif menu == "Ranking":
    st.header("📊 Ranking")

    if results_df.empty:
        st.info("No results yet. Rankings will appear here after games are played.")
    else:
        ranking_df = update_ranking(results_df)

        def highlight_rows(row):
            return ["background-color: #f2f2f2" if row.name % 2 == 0 else "background-color: white" for _ in row]

        st.dataframe(ranking_df.style.apply(highlight_rows, axis=1))
