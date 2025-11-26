import streamlit as st
import pandas as pd
from datetime import date
import io
from openpyxl import Workbook
from openpyxl.styles import Font

st.set_page_config(
    page_title="Grow Tracker",
    page_icon="https://raw.githubusercontent.com/michaelreed452/cannabis-grow-tracker/main/leaf.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== PASSWORD + USER LOGIN =====================
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
    with col2:
        password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        valid_users = {
            "michael": "grow123",
            "tyson": "420tyson",
            "john": "secret123",
            # add more users here
        }
        if username.lower() in valid_users and valid_users[username.lower()] == password:
            st.session_state.user = username.lower()
            st.success(f"Welcome {username.title()}!")
            st.rerun()
        else:
            st.error("Wrong username or password")
    st.stop()

# Show clean name in sidebar
st.sidebar.success(f"Logged in as **{st.session_state.user.title()}**")

# ===================== INITIALISE DATA =====================
def init():
    if "plants" not in st.session_state:
        st.session_state.plants = pd.DataFrame(columns=[
            "Plant ID","Strain Name","Variety","Gender","Environment","Type","Source","Batch #",
            "Date Germination","Date Transplant Veg","Date Flip Flower","Date Harvest",
            "Wet Weight (g)","Dry Weight (g)","Trimmed Yield (g)","Mother ID",
            "Growing Medium","Container Size","Phenotype Notes","Health Issues",
            "Rating (1-10)","Photos Link","Status"
        ])
    if "feeding" not in st.session_state:
        st.session_state.feeding = pd.DataFrame(columns=[
            "Date","Plant IDs","Stage","Nutrient 1","Amount 1","Nutrient 2","Amount 2",
            "Nutrient 3","Amount 3","Nutrient 4","Amount 4","Nutrient 5","Amount 5","Notes"
        ])
    # ... keep your other dataframes (strains, expenses, etc.)

init()

NUTRIENTS = ["CalMag Essential","NC32","Pot Grow","Pot Flora","Pot Radix","Bio-Blend","Carbon K","Multi Foliar Spray Concentrate","Other"]

# Auto calculate current stage
def get_stage(row):
    today = date.today()
    germ = row["Date Germination"]
    veg = row["Date Transplant Veg"]
    flip = row["Date Flip Flower"]
    if pd.isna(germ): return "Not Started"
    if pd.notna(row["Date Harvest"]) and row["Date Harvest"] <= today: return "Harvested"
    if pd.notna(flip) and flip <= today:
        weeks = (today - flip).days // 7 + 1
        return f"Flower Week {weeks}"
    if pd.notna(veg) and veg <= today:
        weeks = (today - veg).days // 7 + 1
        return f"Veg Week {weeks}"
    weeks = (today - germ).days // 7 + 1
    return f"Seedling Week {weeks}"

if len(st.session_state.plants) > 0:
    st.session_state.plants["Current Stage"] = st.session_state.plants.apply(get_stage, axis=1)

# ===================== SIDEBAR =====================
st.sidebar.markdown("# Grow Tracker")
pages = ["Dashboard","Plants Tracker","Strains Library","Expenses","Income","Seed & Clone Stock","Feeding Schedule","Export to Excel"]
emojis = ["Home","Plants","Strains","Expenses","Income","Stock","Feeding","Excel"]

for i, p in enumerate(pages):
    if st.sidebar.button(f"{emojis[i]} {p}", use_container_width=True, 
                        type="primary" if st.session_state.get("page") == p else "secondary"):
        st.session_state.page = p
page = st.session_state.get("page", "Dashboard")

# ===================== FEEDING SCHEDULE =====================
elif page == "Feeding Schedule":
    st.title("Feeding Schedule")
    tab1, tab2 = st.tabs(["Add Feeding", "History"])

    with tab1:
        with st.form("feed"):
            date_feed = st.date_input("Date", date.today())

            # Plant selection
            if len(st.session_state.plants) == 0:
                st.warning("No plants")
            else:
                mode = st.radio("Select", ["Single Plant", "Group"])
                if mode == "Single Plant":
                    pid = st.selectbox("Plant ID", st.session_state.plants["Plant ID"])
                    plant_ids = [pid]
                    stage = st.session_state.plants[st.session_state.plants["Plant ID"] == pid]["Current Stage"].iloc[0]
                else:
                    group = st.selectbox("Group", ["All Plants", "All Veg", "All Flower"] + sorted(st.session_state.plants["Current Stage"].dropna().unique()))
                    if group == "All Plants":
                        plant_ids = st.session_state.plants["Plant ID"].tolist()
                    elif group == "All Veg":
                        plant_ids = st.session_state.plants[st.session_state.plants["Current Stage"].str.contains("Veg|Seedling")]["Plant ID"].tolist()
                    elif group == "All Flower":
                        plant_ids = st.session_state.plants[st.session_state.plants["Current Stage"].str.contains("Flower")]["Plant ID"].tolist()
                    else:
                        plant_ids = st.session_state.plants[st.session_state.plants["Current Stage"] == group]["Plant ID"].tolist()
                    stage = group
                    st.info(f"Selected: {', '.join(plant_ids)}")

            # Nutrients
            nut1 = st.selectbox("Nutrient 1", NUTRIENTS)
            amt1 = st.number_input("Amount 1 (ml/g)", 0.0, step=0.1)
            if nut1 == "Other":
                nut1 = st.text_input("Specify other nutrient")

            more = st.checkbox("Add more nutrients (up to 5 total)")
            extras = []
            if more:
                count = st.slider("How many more?", 1, 4, 1)
                for i in range(count):
                    n = st.selectbox(f"Nutrient {i+2}", NUTRIENTS, key=f"n{i}")
                    a = st.number_input(f"Amount {i+2}", 0.0, step=0.1, key=f"a{i}")
                    if n == "Other":
                        n = st.text_input(f"Specify other {i+2}", key=f"o{i}")
                    extras.append((n, a))

            notes = st.text_area("Notes (optional)")

            if st.form_submit_button("Save Feeding"):
                row = {"Date": date_feed, "Plant IDs": ", ".join(plant_ids), "Stage": stage,
                       "Nutrient 1": nut1, "Amount 1": amt1}
                for i, (n, a) in enumerate(extras):
                    row[f"Nutrient {i+2}"] = n
                    row[f"Amount {i+2}"] = a
                row["Notes"] = notes
                st.session_state.feeding = pd.concat([st.session_state.feeding, pd.DataFrame([row])], ignore_index=True)
                st.success("Feeding saved!")
                st.rerun()

    with tab2:
        if len(st.session_state.feeding) > 0:
            st.dataframe(st.session_state.feeding.sort_values("Date", ascending=False), use_container_width=True)
        else:
            st.info("No feedings yet")

# ===================== PLANTS TRACKER WITH EDIT =====================
elif page == "Plants Tracker":
    st.title("Plants Tracker")
    tab1, tab2 = st.tabs(["View & Edit", "Add New"])

    with tab1:
        if len(st.session_state.plants) > 0:
            edited = st.data_editor(
                st.session_state.plants,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True
            )
            if st.button("Save Changes"):
                st.session_state.plants = edited
                st.success("Plants updated!")
                st.rerun()
        else:
            st.info("No plants yet")

    with tab2:
        with st.form("add_plant"):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Plant ID *", key="pid")
                st.text_input("Strain Name *", key="strain")
                st.selectbox("Growing Medium", ["Fabric Pot", "Plastic Pot", "Direct Soil", "Coco", "Hydro", "Air Pot"], key="medium")
                st.number_input("Container Size (L or bed size)", 0.0, step=0.5, key="size")
            # ... rest of your plant form
            # (kept short — you already have this)

# ===================== EXPORT WITH FEEDING TAB =====================
elif page == "Export to Excel":
    if st.button("Download Full Tracker"):
        wb = Workbook()
        wb.remove(wb.active)
        for name, df in [("Plants", st.session_state.plants), ("Feeding", st.session_state.feeding),
                         ("Strains", st.session_state.strains), ("Expenses", st.session_state.expenses),
                         ("Income", st.session_state.income), ("Stock", st.session_state.stock)]:
            ws = wb.create_sheet(name[:31])
            for c, col in enumerate(df.columns, 1):
                ws.cell(1, c, col).font = Font(bold=True)
            for r, row in enumerate(df.itertuples(index=False), 2):
                for col, val in enumerate(row, 1):
                    ws.cell(r, col, val)
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        st.download_button("Download Excel", buffer, f"GrowTracker_{date.today()}.xlsx")

# ===================== FOOTER =====================
st.markdown("---")
c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.markdown(f"<div style='text-align:center'>Plants<br><b>{len(st.session_state.plants)}</b></div>", True)
with c2: st.markdown(f"<div style='text-align:center'>Strains<br><b>{len(st.session_state.strains)}</b></div>", True)
with c3: st.markdown(f"<div style='text-align:center'>Expenses<br><b>{len(st.session_state.expenses)}</b></div>", True)
with c4: st.markdown(f"<div style='text-align:center'>Income<br><b>{len(st.session_state.income)}</b></div>", True)
with c5: st.markdown(f"<div style='text-align:center'>Stock<br><b>{len(st.session_state.stock)}</b></div>", True)
