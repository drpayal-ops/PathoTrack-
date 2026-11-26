import io
import re
from datetime import date

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

st.set_page_config(
    page_title="PathoTrack",
    page_icon="🧪",
    layout="wide"
)

st.title("🧪 PathoTrack")
st.caption("One Patient | Report Comparison | Graph | JPG Download")

st.warning(
    "College demo only. Not for diagnosis or treatment. "
    "Always verify extracted values with the original report."
)

TESTS = {
    "Hemoglobin": (12, 16, "g/dL",
                   [r"hemoglobin", r"\bhb\b", r"\bhgb\b"]),
    "RBC Count": (4, 5.5, "million/µL",
                  [r"rbc count", r"red blood cell(?:s)?", r"\brbc\b"]),
    "WBC Count": (4000, 11000, "/µL",
                  [r"wbc count", r"total leukocyte count", r"\btlc\b", r"\bwbc\b"]),
    "Platelet Count": (150000, 450000, "/µL",
                       [r"platelet(?:s)? count", r"\bplatelet(?:s)?\b"]),
    "Neutrophils": (40, 70, "%",
                    [r"neutrophils?", r"\bneut\b"]),
    "Lymphocytes": (20, 40, "%",
                    [r"lymphocytes?", r"\blymph\b"]),
    "ESR": (0, 20, "mm/hr",
            [r"\besr\b", r"erythrocyte sedimentation rate"]),
    "Fasting Blood Sugar": (70, 100, "mg/dL",
                            [r"fasting blood sugar", r"\bfbs\b", r"fasting glucose"]),
    "Creatinine": (0.6, 1.3, "mg/dL",
                   [r"\bcreatinine\b"]),
    "Total Cholesterol": (0, 200, "mg/dL",
                          [r"total cholesterol", r"\bcholesterol\b"]),
    "TSH": (0.4, 4.0, "µIU/mL",
            [r"\btsh\b", r"thyroid stimulating hormone"])
}


def pdf_text(file):
    if not file:
        return ""

    try:
        reader = PdfReader(file)
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )
    except Exception:
        return ""


def extract(text):
    found = {}
    text = re.sub(r"[ \t]+", " ", text.replace("\u00a0", " "))

    for name, (_, _, _, aliases) in TESTS.items():
        for alias in aliases:
            pattern = (
                rf"(?im)(?:^|[\n:])\s*(?:{alias})"
                rf"\s*(?:[:\-]|\s)\s*([-+]?\d[\d,]*(?:\.\d+)?)"
            )

            match = re.search(pattern, text)

            if match:
                try:
                    found[name] = float(
                        match.group(1).replace(",", "")
                    )
                    break
                except ValueError:
                    pass

    return found


def flag(name, value):
    low, high, _, _ = TESTS[name]

    if value < low:
        return "Low"
    elif value > high:
        return "High"
    return "Within example range"


def jpg_report(patient, old, new, report_day):
    width, height = 1800, 2300

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    try:
        big = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
        heading = ImageFont.truetype("DejaVuSans-Bold.ttf", 29)
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except Exception:
        big = heading = font = ImageFont.load_default()

    navy = (23, 54, 93)

    draw.rectangle((0, 0, width, 165), fill=navy)
    draw.text((65, 35), "PATHOTRACK", font=big, fill="white")
    draw.text(
        (68, 105),
        "PATIENT LAB REPORT SUMMARY",
        font=heading,
        fill="white"
    )

    y = 205

    details = [
        "Patient Name: " + patient["name"],
        f'Age: {patient["age"]} years    Sex: {patient["sex"]}    Blood Group: {patient["blood"]}',
        "Report Date: " + str(report_day)
    ]

    for line in details:
        draw.text((70, y), line, font=font, fill="black")
        y += 48

    y += 20
    draw.text((70, y), "TEST RESULTS", font=heading, fill=navy)
    y += 55

    columns = [70, 560, 820, 1120, 1450]
    headers = ["Test", "Old value", "New value", "Unit", "New flag*"]

    draw.rectangle(
        (55, y - 8, width - 55, y + 48),
        fill=(31, 78, 121)
    )

    for x, title in zip(columns, headers):
        draw.text((x, y), title, font=font, fill="white")

    y += 65

    for name, (low, high, unit, _) in TESTS.items():

        if name not in old and name not in new:
            continue

        value = new.get(name)

        values = [
            name,
            str(old.get(name, "—")),
            str(value if value is not None else "—"),
            unit,
            flag(name, value) if value is not None else "Not found"
        ]

        for x, item in zip(columns, values):
            draw.text((x, y), str(item), font=font, fill=(25, 25, 25))

        y += 48
        draw.line(
            (60, y - 5, width - 60, y - 5),
            fill=(220, 225, 230),
            width=1
        )

    y += 25

    labels = [
        name for name in TESTS
        if name in old or name in new
    ]

    if labels:
        fig, ax = plt.subplots(figsize=(12, 3.7))

        positions = list(range(len(labels)))
        bar_width = 0.36

        ax.bar(
            [i - bar_width / 2 for i in positions],
            [old.get(name, 0) for name in labels],
            bar_width,
            label="Old Report",
            color="#2878B5"
        )

        ax.bar(
            [i + bar_width / 2 for i in positions],
            [new.get(name, 0) for name in labels],
            bar_width,
            label="New Report",
            color="#20A486"
        )

        ax.set_xticks(positions)
        ax.set_xticklabels(
            labels,
            rotation=35,
            ha="right",
            fontsize=8
        )

        ax.set_title("Old vs New Report")
        ax.legend()
        ax.grid(axis="y", alpha=0.2)

        fig.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=120)
        plt.close(fig)
        buffer.seek(0)

        chart = Image.open(buffer).convert("RGB")
        chart.thumbnail((1650, 480))

        if y + chart.height + 100 < height:
            image.paste(chart, (70, y))

    draw.text(
        (70, height - 100),
        "*Example flags only. Confirm with laboratory reference ranges.",
        font=font,
        fill=(70, 70, 70)
    )

    draw.text(
        (70, height - 55),
        "FICTIONAL / COLLEGE DEMO ONLY — NOT FOR CLINICAL USE",
        font=font,
        fill=(170, 0, 0)
    )

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=94)
    output.seek(0)

    return output


st.header("1. Patient Details")

with st.form("patient_form"):

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Patient Name")
        age = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=20
        )
        sex = st.selectbox(
            "Sex",
            ["Male", "Female", "Other", "Not specified"]
        )

    with col2:
        blood = st.selectbox(
            "Blood Group",
            ["Not provided", "A+", "A-", "B+", "B-",
             "AB+", "AB-", "O+", "O-"]
        )

        report_date = st.date_input(
            "Report Date",
            value=date.today()
        )

    save = st.form_submit_button("Save Patient Details")

if save:
    if not name.strip():
        st.error("Please enter patient name.")
    else:
        st.session_state.patient = {
            "name": name.strip(),
            "age": int(age),
            "sex": sex,
            "blood": blood
        }

        st.session_state.report_day = str(report_date)
        st.success("Patient details saved for this session.")

patient = st.session_state.get("patient")

if not patient:
    st.info("Save patient details first.")
    st.stop()

st.success("Current Patient: " + patient["name"])

st.header("2. Upload Old and New Reports")

col1, col2 = st.columns(2)

with col1:
    old_pdf = st.file_uploader(
        "Upload Old Report PDF",
        type=["pdf"],
        key="old_report"
    )

with col2:
    new_pdf = st.file_uploader(
        "Upload New Report PDF",
        type=["pdf"],
        key="new_report"
    )

old_values = extract(pdf_text(old_pdf))
new_values = extract(pdf_text(new_pdf))

if old_pdf or new_pdf:

    st.header("3. Check and Correct Values")

    st.caption(
        "Extracted values ko original report se verify karo. "
        "Zarurat ho to table mein manually correct karo."
    )

    data = []

    for test, (low, high, unit, _) in TESTS.items():
        data.append({
            "Test": test,
            "Old value": old_values.get(test),
            "New value": new_values.get(test),
            "Unit": unit
        })

    edited = st.data_editor(
        pd.DataFrame(data),
        width="stretch",
        hide_index=True,
        disabled=["Test", "Unit"]
    )

    old_corrected = {}
    new_corrected = {}

    for _, row in edited.iterrows():

        if pd.notna(row["Old value"]):
            old_corrected[row["Test"]] = float(row["Old value"])

        if pd.notna(row["New value"]):
            new_corrected[row["Test"]] = float(row["New value"])

    st.header("4. New Report Analysis")

    result_rows = []

    for test, value in new_corrected.items():

        low, high, unit, _ = TESTS[test]

        result_rows.append({
            "Test": test,
            "Result": value,
            "Unit": unit,
            "Example Range": f"{low} - {high}",
            "Flag": flag(test, value)
        })

    if result_rows:
        st.dataframe(
            pd.DataFrame(result_rows),
            width="stretch",
            hide_index=True
        )
    else:
        st.info(
            "No supported values found. "
            "Enter values manually in the table above."
        )

    if old_corrected or new_corrected:

        st.header("5. Old vs New Comparison Graph")

        graph_tests = [
            test for test in TESTS
            if test in old_corrected or test in new_corrected
        ]

        graph_data = pd.DataFrame({
            "Old Report": [
                old_corrected.get(test)
                for test in graph_tests
            ],
            "New Report": [
                new_corrected.get(test)
                for test in graph_tests
            ]
        }, index=graph_tests)

        st.bar_chart(
            graph_data,
            color=["#2878B5", "#20A486"],
            width="stretch"
        )

        st.caption(
            "Tests have different units. Graph is for visual comparison only."
        )

        st.header("6. Download Report as JPG")

        report_file = jpg_report(
            patient,
            old_corrected,
            new_corrected,
            st.session_state.get(
                "report_day",
                str(date.today())
            )
        )

        safe_name = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            patient["name"]
        ).strip("_") or "patient"

        st.download_button(
            "Download Patient Report (JPG)",
            report_file,
            file_name=f"PathoTrack_{safe_name}_Report.jpg",
            mime="image/jpeg",
            width="stretch"
        )

else:
    st.info("Upload Old and New PDF reports to start comparison.")

st.divider()

st.caption(
    "One patient at a time. Details are stored only in the current "
    "app session and are not permanently saved. Text-based PDFs only; "
    "scanned PDFs are not supported. Example ranges are not clinical advice."
)