
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from pypdf import PdfReader

st.set_page_config(
    page_title="PathoTrack",
    page_icon="🧬",
    layout="wide"
)

st.markdown("""
<style>
.stApp {background-color: #f4f8fb;}
h1, h2, h3 {color: #123b50;}
</style>
""", unsafe_allow_html=True)

st.title("🧬 PathoTrack")
st.caption("SMART PATHOLOGY REPORT COMPARISON & ANALYSIS")

st.divider()
st.header("Patient Report Analysis")

patient_id = st.text_input(
    "Patient ID (optional)"
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Old Report")
    old_file = st.file_uploader(
        "Upload previous PDF",
        type=["pdf"],
        key="old"
    )

with col2:
    st.subheader("📄 New Report")
    new_file = st.file_uploader(
        "Upload latest PDF",
        type=["pdf"],
        key="new"
    )


def read_pdf(file):
    if file is None:
        return ""
    try:
        reader = PdfReader(file)
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )
    except Exception:
        return ""


TESTS = {
    "Hemoglobin": ["hemoglobin", "hb"],
    "WBC": ["wbc", "total leukocyte count", "tlc"],
    "RBC": ["rbc", "red blood cell"],
    "Platelets": ["platelet", "platelets", "plt"],
    "Neutrophils": ["neutrophils"],
    "Lymphocytes": ["lymphocytes"],
    "Eosinophils": ["eosinophils"],
    "Monocytes": ["monocytes"],
    "ESR": ["esr", "erythrocyte sedimentation rate"],
    "Fasting Blood Sugar": ["fasting blood sugar", "fbs"],
    "Random Blood Sugar": ["random blood sugar", "rbs"],
    "HbA1c": ["hba1c", "glycated hemoglobin"],
    "Creatinine": ["creatinine"],
    "Urea": ["blood urea", "urea"],
    "Uric Acid": ["uric acid"],
    "Total Cholesterol": ["total cholesterol"],
    "Triglycerides": ["triglycerides", "triglyceride"],
    "HDL": ["hdl"],
    "LDL": ["ldl"],
    "SGOT": ["sgot", "ast"],
    "SGPT": ["sgpt", "alt"],
    "Bilirubin": ["total bilirubin", "bilirubin"],
    "TSH": ["tsh"],
    "T3": ["total t3", "t3"],
    "T4": ["total t4", "t4"]
}


def extract_tests(text):
    results = {}

    for line in text.splitlines():
        clean = line.strip()
        lower = clean.lower()

        for test, aliases in TESTS.items():
            if test in results:
                continue

            for alias in aliases:
                pattern = (
                    r"(?<![a-z])" + re.escape(alias) +
                    r"(?![a-z])"
                )

                if re.search(pattern, lower):
                    numbers = re.findall(
                        r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",
                        clean
                    )

                    if numbers:
                        results[test] = float(numbers[0])
                    break

    return results


old_text = read_pdf(old_file)
new_text = read_pdf(new_file)

if old_file and new_file:
    st.success("Both reports uploaded!")

    old_data = extract_tests(old_text)
    new_data = extract_tests(new_text)

    all_tests = sorted(
        set(old_data.keys()) | set(new_data.keys())
    )

    if all_tests:
        comparison = pd.DataFrame({
            "Test": all_tests,
            "Old Value": [
                old_data.get(test) for test in all_tests
            ],
            "New Value": [
                new_data.get(test) for test in all_tests
            ]
        })

        st.divider()
        st.header("📊 Report Comparison")

        st.info(
            "Check extracted values carefully. "
            "You can correct them in the table below."
        )

        edited = st.data_editor(
            comparison,
            num_rows="dynamic",
            use_container_width=True
        )

        st.subheader("Individual Test Graph")

        valid_tests = edited["Test"].dropna().tolist()

        if valid_tests:
            selected = st.selectbox(
                "Select a test",
                valid_tests
            )

            graph_row = edited[
                edited["Test"] == selected
            ].iloc[0]

            chart = pd.DataFrame({
                "Report": ["Old Report", "New Report"],
                "Value": [
                    graph_row["Old Value"],
                    graph_row["New Value"]
                ]
            })

            chart["Value"] = pd.to_numeric(
                chart["Value"], errors="coerce"
            )
            chart = chart.dropna()

            if not chart.empty:
                fig = px.bar(
                    chart,
                    x="Report",
                    y="Value",
                    color="Report",
                    title=f"{selected} Comparison"
                )
                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        csv = edited.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Comparison CSV",
            data=csv,
            file_name="PathoTrack_Comparison.csv",
            mime="text/csv"
        )

    else:
        st.warning(
            "No supported test values were detected. "
            "Try a text-based PDF or enter values manually."
        )

elif old_file or new_file:
    st.info("Please upload both old and new reports.")

st.divider()

st.caption(
    "PathoTrack is an educational report comparison tool. "
    "It does not provide medical diagnosis. "
    "Always verify extracted values with the original report."
)

st.write("© PathoTrack | Smart Health Report Analytics")
