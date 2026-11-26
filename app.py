
import streamlit as st
import pandas as pd
import plotly.express as px
from pypdf import PdfReader

st.set_page_config(
    page_title="PathoTrack",
    page_icon="🧬",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #f4f8fb;
}
h1, h2, h3 {
    color: #123b50;
}
[data-testid="stMetric"] {
    background: white;
    padding: 16px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.title("🧬 PathoTrack")
st.caption("SMART PATHOLOGY REPORT COMPARISON & ANALYSIS")

st.divider()

st.header("Patient Report Analysis")

patient_id = st.text_input(
    "Patient ID (optional)",
    placeholder="Enter patient ID"
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Old Report")
    old_file = st.file_uploader(
        "Upload previous report",
        type=["pdf"],
        key="old"
    )

with col2:
    st.subheader("📄 New Report")
    new_file = st.file_uploader(
        "Upload latest report",
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

if old_file and new_file:
    st.success("Both reports uploaded successfully!")

    with st.expander("View old report extracted text"):
        st.text(read_pdf(old_file) or "No readable text found.")

    with st.expander("View new report extracted text"):
        st.text(read_pdf(new_file) or "No readable text found.")

st.divider()

st.header("📊 Report Comparison Dashboard")

st.info(
    "This is the initial dashboard. "
    "Automatic test extraction and comparison "
    "will be added in the next development stages."
)

st.subheader("Sample Comparison")

sample = pd.DataFrame({
    "Test": ["Hemoglobin", "WBC", "Platelets"],
    "Old Report": [10.5, 12000, 150000],
    "New Report": [11.8, 9000, 200000]
})

st.dataframe(sample, use_container_width=True)

selected_test = st.selectbox(
    "Select test for graph",
    sample["Test"]
)

chart_data = sample[
    sample["Test"] == selected_test
].melt(
    id_vars="Test",
    var_name="Report",
    value_name="Value"
)

fig = px.bar(
    chart_data,
    x="Report",
    y="Value",
    color="Report",
    title=f"{selected_test} Comparison"
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Sample values are illustrative only. "
    "This application does not provide medical diagnosis."
)

st.divider()
st.write("© PathoTrack | Smart Health Report Analytics")
