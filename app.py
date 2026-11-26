
  import io, re
from datetime import date
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader

st.set_page_config(page_title="PathoTrack", page_icon="🧪", layout="wide")
st.title("🧪 PathoTrack")
st.caption("One-patient college demo | PDF analysis | comparison graph | JPG download")
st.warning("Demo only. Not for diagnosis or treatment. Verify all extracted values with the original lab report.")

# Example ranges only; use the ranges printed by the actual laboratory for real interpretation.
TESTS = {
 "Hemoglobin": (12,16,"g/dL",[r"hemoglobin",r"\bhb\b",r"\bhgb\b"]),
 "RBC Count": (4,5.5,"million/µL",[r"rbc count",r"red blood cell(?:s)?",r"\brbc\b"]),
 "WBC Count": (4000,11000,"/µL",[r"wbc count",r"total leukocyte count",r"\btlc\b",r"\bwbc\b"]),
 "Platelet Count": (150000,450000,"/µL",[r"platelet(?:s)? count",r"\bplatelet(?:s)?\b"]),
 "Neutrophils": (40,70,"%",[r"neutrophils?",r"\bneut\b"]),
 "Lymphocytes": (20,40,"%",[r"lymphocytes?",r"\blymph\b"]),
 "ESR": (0,20,"mm/hr",[r"\besr\b",r"erythrocyte sedimentation rate"]),
 "Fasting Blood Sugar": (70,100,"mg/dL",[r"fasting blood sugar",r"\bfbs\b",r"fasting glucose"]),
 "Creatinine": (0.6,1.3,"mg/dL",[r"\bcreatinine\b"]),
 "Total Cholesterol": (0,200,"mg/dL",[r"total cholesterol",r"\bcholesterol\b"]),
 "TSH": (0.4,4.0,"µIU/mL",[r"\btsh\b",r"thyroid stimulating hormone"]),
}

def pdf_text(file):
    if not file: return ""
    try:
        return "\n".join(p.extract_text() or "" for p in PdfReader(file).pages)
    except Exception:
        return ""

def extract(text):
    found = {}
    text = re.sub(r"[ \t]+"," ",text.replace("\u00a0"," "))
    for name, (_,_,_,aliases) in TESTS.items():
        for alias in aliases:
            m = re.search(rf"(?im)(?:^|[\n:])\s*(?:{alias})\s*(?:[:\-]|\s)\s*([-+]?\d[\d,]*(?:\.\d+)?)",text)
            if m:
                try:
                    found[name] = float(m.group(1).replace(",",""))
                    break
                except ValueError: pass
    return found

def flag(name, val):
    lo, hi, _, _ = TESTS[name]
    return "Low" if val < lo else ("High" if val > hi else "Within example range")

def jpg_report(patient, old, new, report_day):
    W,H = 1800,2300
    im = Image.new("RGB",(W,H),"white")
    d = ImageDraw.Draw(im)
    try:
        big=ImageFont.truetype("DejaVuSans-Bold.ttf",52)
        head=ImageFont.truetype("DejaVuSans-Bold.ttf",29)
        font=ImageFont.truetype("DejaVuSans.ttf",22)
    except Exception:
        big=head=font=ImageFont.load_default()
    navy=(23,54,93)
    d.rectangle((0,0,W,165),fill=navy)
    d.text((65,35),"PATHOTRACK",font=big,fill="white")
    d.text((68,105),"PATIENT LAB REPORT SUMMARY",font=head,fill="white")
    y=205
    for line in [
        "Patient Name: "+patient["name"],
        f'Age: {patient["age"]} years    Sex: {patient["sex"]}    Blood Group: {patient["blood"]}',
        "Report Date: "+str(report_day)
    ]:
        d.text((70,y),line,font=font,fill="black"); y+=48
    y+=20
    d.text((70,y),"TEST RESULTS",font=head,fill=navy); y+=55
    xs=[70,560,820,1120,1450]
    headers=["Test","Old value","New value","Unit","New flag*"]
    d.rectangle((55,y-8,W-55,y+48),fill=(31,78,121))
    for x,h in zip(xs,headers): d.text((x,y),h,font=font,fill="white")
    y+=65
    for name,(lo,hi,unit,_) in TESTS.items():
        if name not in old and name not in new: continue
        val=new.get(name)
        vals=[name,str(old.get(name,"—")),str(val if val is not None else "—"),unit,flag(name,val) if val is not None else "Not found"]
        for x,v in zip(xs,vals): d.text((x,y),str(v),font=font,fill=(25,25,25))
        y+=48
        d.line((60,y-5,W-60,y-5),fill=(220,225,230),width=1)
    y+=25
    # Two separate colour series. Values have different units; graph is for visual comparison only.
    labels=[n for n in TESTS if n in old or n in new]
    if labels:
        fig,ax=plt.subplots(figsize=(12,3.7))
        ix=list(range(len(labels))); width=.36
        ax.bar([i-width/2 for i in ix],[old.get(n,0) for n in labels],width,label="Old Report",color="#2878B5")
        ax.bar([i+width/2 for i in ix],[new.get(n,0) for n in labels],width,label="New Report",color="#20A486")
        ax.set_xticks(ix); ax.set_xticklabels(labels,rotation=35,ha="right",fontsize=8)
        ax.set_title("Old vs New (tests use different units)"); ax.legend(); ax.grid(axis="y",alpha=.2)
        fig.tight_layout()
        b=io.BytesIO(); fig.savefig(b,format="png",dpi=120); plt.close(fig); b.seek(0)
        chart=Image.open(b).convert("RGB"); chart.thumbnail((1650,480))
        if y+chart.height+100 < H: im.paste(chart,(70,y))
    d.text((70,H-100),"*Example flags only. Confirm against the laboratory's printed reference ranges.",font=font,fill=(70,70,70))
    d.text((70,H-55),"FICTIONAL / COLLEGE DEMO ONLY — NOT FOR CLINICAL USE",font=font,fill=(170,0,0))
    out=io.BytesIO(); im.save(out,format="JPEG",quality=94); out.seek(0); return out

st.header("1. Patient details")
with st.form("patient"):
    a,b=st.columns(2)
    with a:
        name=st.text_input("Patient name")
        age=st.number_input("Age",min_value=0,max_value=120,value=20)
        sex=st.selectbox("Sex",["Male","Female","Other","Not specified"])
    with b:
        blood=st.selectbox("Blood group",["Not provided","A+","A-","B+","B-","AB+","AB-","O+","O-"])
        day=st.date_input("Report date",value=date.today())
    save=st.form_submit_button("Save patient details")
if save:
    if not name.strip(): st.error("Patient name enter karo.")
    else:
        st.session_state.patient={"name":name.strip(),"age":int(age),"sex":sex,"blood":blood}
        st.session_state.report_day=str(day)
        st.success("Patient details saved for this current session.")

patient=st.session_state.get("patient")
if not patient:
    st.info("Patient details save karne ke baad reports upload karo.")
    st.stop()
st.success(f'Current patient: {patient["name"]}')

st.header("2. Upload reports")
c1,c2=st.columns(2)
with c1: old_pdf=st.file_uploader("Old report PDF",type=["pdf"])
with c2: new_pdf=st.file_uploader("New report PDF",type=["pdf"])
old=extract(pdf_text(old_pdf)); new=extract(pdf_text(new_pdf))

if old_pdf or new_pdf:
    st.header("3. Check and correct values")
    st.caption("PDF extraction galat ya incomplete ho sakta hai. Values original report se verify/correct karo.")
    data=[]
    for t,(lo,hi,unit,_) in TESTS.items():
        data.append({"Test":t,"Old value":old.get(t),"New value":new.get(t),"Unit":unit})
    edited=st.data_editor(pd.DataFrame(data),use_container_width=True,hide_index=True,
                          disabled=["Test","Unit"])
    old2={}; new2={}
    for _,r in edited.iterrows():
        if pd.notna(r["Old value"]): old2[r["Test"]]=float(r["Old value"])
        if pd.notna(r["New value"]): new2[r["Test"]]=float(r["New value"])
    st.header("4. New report analysis")
    rows=[]
    for t,v in new2.items():
        lo,hi,unit,_=TESTS[t]
        rows.append({"Test":t,"Result":v,"Unit":unit,"Example range":f"{lo} - {hi}","Flag":flag(t,v)})
    if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    else: st.info("Supported values nahi mile. Upar table mein manually values enter karo.")
    if old2 or new2:
        st.header("5. Comparison graph")
        graph=pd.DataFrame({"Old Report":[old2.get(t) for t in TESTS if t in old2 or t in new2],
                            "New Report":[new2.get(t) for t in TESTS if t in old2 or t in new2]},
                           index=[t for t in TESTS if t in old2 or t in new2])
        st.bar_chart(graph,color=["#2878B5","#20A486"])
        st.header("6. Download JPG")
        file=jpg_report(patient,old2,new2,st.session_state.get("report_day",str(date.today())))
        safe=re.sub(r"[^A-Za-z0-9_-]+","_",patient["name"]).strip("_") or "patient"
        st.download_button("Download patient report (JPG)",file,
                           file_name=f"PathoTrack_{safe}_Report.jpg",mime="image/jpeg",
                           use_container_width=True)
else:
    st.info("Old aur New PDF upload karne par analysis aur graph dikhega.")

st.divider()
st.caption("One patient at a time. Details sirf current app session mein rehti hain; app/session restart hone par permanently save nahi hongi. Text-based PDFs supported; scanned PDFs ke liye OCR baad mein add karna hoga. Sirf listed common tests detect hote hain.")
  