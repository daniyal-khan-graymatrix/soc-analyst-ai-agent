import streamlit as st
import os, json
from pathlib import Path
import shutil

from utils.log_access import log_access  
from main import main as run_pipeline

DATA_DIR = Path("data")

st.set_page_config(page_title="SOC Analyst Log Uploader", layout="centered")

st.header("📂 SOC Log Uploader")
st.markdown("Upload multiple `.csv` or `.json` log files. Once uploaded, they will be processed automatically.")

uploaded_files = st.file_uploader("Upload CSV or JSON logs", type=["csv", "json"], accept_multiple_files=True)

if uploaded_files:
    # Clear previous data directory
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for file in uploaded_files:
        file_path = DATA_DIR / file.name
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
    st.success(f"✅ Uploaded {len(uploaded_files)} files successfully!")

    if st.button("🚀 Run Incident Detection"):
        with st.spinner("Processing logs and detecting incidents..."):
            try:
                final_state = run_pipeline()
                report_filename = final_state.get("report_filename", "UNKNOWN_REPORT.json")
                st.success("✅ Pipeline completed successfully.")
                st.markdown(f"📄 **Generated Incident Report:** `{report_filename}`")
            except Exception as e:
                st.error(f"❌ Error during pipeline execution:\n```\n{e}\n```")


REPORT_DIR = "reports"

st.header("📁 Incident Report Viewer")

# List all JSON reports in the folder
report_files = [f for f in os.listdir(REPORT_DIR) if f.endswith(".json")]

if report_files:
    selected_report = st.selectbox("Select an incident report to view:", sorted(report_files, reverse=True))

    if st.button("📄 Open Report"):
        report_path = os.path.join(REPORT_DIR, selected_report)
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            st.success(f"Opened {selected_report}")
            st.json(report_data)

            # 🔐 Log the access
            log_access(selected_report, user="frontend_user")

        except Exception as e:
            st.error(f"Error opening report: {e}")
else:
    st.info("No incident reports available yet.")
