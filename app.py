import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
import io

st.set_page_config(page_title="Cannabis Grow Tracker", layout="wide", page_icon="Cannabis")

# ===================== INITIALISE DATA =====================
def initialize_session_state():
    if 'plants' not in st.session_state:
        st.session_state.plants = pd.DataFrame(columns=[
            'Plant ID', 'Strain Name', 'Variety', 'Gender', 'Environment', 'Type', 'Source', 'Batch #',
            'Date Germination', 'Date Transplant Veg', 'Date Flip Flower', 'Date Harvest',
            'Wet Weight (g)', 'Dry Weight (g)', 'Trimmed Yield (g)', 'Mother ID',
            'Pot Size (L)', 'Medium', 'Phenotype Notes', 'Health Issues',
            'Rating (1-10)', 'Photos Link', 'Status'
        ])
    if 'strains' not in st.session_state:
        st.session_state.strains = pd.DataFrame(columns=[
            'Strain Name', 'Breeder', 'Variety', 'Expected Flower Time', 'THC %',
            'Terpene Profile', 'Average Yield (g/plant)', 'Times Grown', 'Best Pheno Notes', 'Keeper?'
        ])
    if 'expenses' not in st.session_state:
        st.session_state.expenses = pd.DataFrame(columns=[
            'Date', 'Category', 'Item', 'Supplier', 'Cost (ZAR)', 'Quantity', 'Paid To', 'Notes', 'Receipt Link'
        ])
    if 'income' not in st.session_state:
        st.session_state.income = pd.DataFrame(columns=[
            'Date', 'Strain', 'Grams Sold', 'Price per Gram', 'Buyer/Channel', 'Payment Method', 'Notes'
        ])
    if 'stock' not in st.session_state:
        st.session_state.stock = pd.DataFrame(columns=[
            'Strain', 'Breeder', 'Seeds/Clones Left', 'Pack Cost (ZAR)'
        ])

initialize_session_state()

# ===================== CALCULATIONS =====================
def calculate_flowering_days(flip, harvest):
    if pd.notna(flip) and pd.notna(harvest):
        return (harvest - flip).days
    return None

def calculate_total_days(germ, harvest):
    if pd.notna(germ) and pd.notna(harvest):
        return (harvest - germ).days
    return None

# ===================== EXCEL EXPORT =====================
def export_to_excel():
    wb = Workbook()
    wb.remove(wb.active)

    def header(ws, headers):
        for c, h in enumerate(headers, 1):
            cell = ws.cell(1, c, h)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

    # Dashboard sheet
    ws = wb.create_sheet("Dashboard")
    ws.append(["Cannabis Grow Tracker - Summary"])
    total_plants = len(st.session_state.plants)
    total_yield = st.session_state.plants["Trimmed Yield (g)"].sum()
    total_expenses = st.session_state.expenses["Cost (ZAR)"].sum()
    total_income = (st.session_state.income["Grams Sold"] * st.session_state.income["Price per Gram"]).sum() if len(st.session_state.income)>0 else 0
    ws.append(["Total Plants", total_plants])
    ws.append(["Total Yield (g)", total_yield])
    ws.append(["Total Expenses", total_expenses])
    ws.append(["Total Income", total_income])
    ws.append(["Net Profit", total_income - total_expenses])

    # Plants sheet
    ws = wb.create_sheet("Plants Tracker")
    plants_df = st.session_state.plants.copy()
    plants_df["Flowering Days"] = plants_df.apply(lambda row: calculate_flowering_days(row["Date Flip Flower"], row["Date Harvest"]), axis=1)
    plants_df["Total Days"] = plants_df.apply(lambda row: calculate_total_days(row["Date Germination"], row["Date Harvest"]), axis=1)
    header(ws, plants_df.columns.tolist())
    for r in pd.DataFrame(plants_df).itertuples(index=False):
        ws.append(list(r))

    # Strains, Expenses, Income, Stock sheets (simple copy)
    for name, df in [("Strains Library", st.session_state.strains),
                     ("Expenses", st.session_state.expenses),
                     ("Income", st.session_state.income),
                     ("Seed & Clone Stock", st.session_state.stock)]:
        ws = wb.create_sheet(name)
        header(ws, df.columns.tolist())
        for r in pd.DataFrame(df).itertuples(index=False):
            ws.append(list(r))

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

# ===================== SIDEBAR =====================
# === FIXED SIDEBAR WITH EMOJIS THAT ACTUALLY SHOW ===
st.sidebar.markdown("### Navigation")

pages = ["Dashboard","Plants Tracker","Strains Library","Expenses","Income","Seed & Clone Stock","Export to Excel"]
emojis = ["🏠","🌱","🧬","💰","💵","📦","📊"]

for i, name in enumerate(pages):
    if st.sidebar.button(f"{emojis[i]} {name}", use_container_width=True):
        st.session_state.page = name

page = st.session_state.get("page", "Dashboard")

# ===================== PAGES =====================
if page == "Dashboard":
    st.title("Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Plants", len(st.session_state.plants))
    c2.metric("Total Yield", f"{st.session_state.plants['Trimmed Yield (g)'].sum():.1f} g")
    c3.metric("Total Expenses", f"R {st.session_state.expenses['Cost (ZAR)'].sum():,.2f}")
    income = (st.session_state.income["Grams Sold"] * st.session_state.income["Price per Gram"]).sum() if len(st.session_state.income)>0 else 0
    c4.metric("Total Income", f"R {income:,.2f}")
    st.metric("Net Profit", f"R {income - st.session_state.expenses['Cost (ZAR)'].sum():,.2f}")

elif page == "Plants Tracker":
    st.title("Plants Tracker")
    tab1, tab2 = st.tabs(["View Plants", "Add New Plant"])

    with tab1:
        if len(st.session_state.plants) > 0:
            df = st.session_state.plants.copy()
            df["Flowering Days"] = df.apply(lambda r: calculate_flowering_days(r["Date Flip Flower"], r["Date Harvest"]), axis=1)
            df["Total Days"] = df.apply(lambda r: calculate_total_days(r["Date Germination"], r["Date Harvest"]), axis=1)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No plants yet")

    with tab2:
        c1, c2, c3 = st.columns(3)
        with c1:
            plant_id = st.text_input("Plant ID *")
            strain = st.text_input("Strain Name *")
            variety = st.selectbox("Variety", ["Sativa","Indica","Hybrid","Hybrid-Indica Dominant","Hybrid-Sativa Dominant","Autoflower"])
            gender = st.selectbox("Gender", ["Female","Male","Hermaphrodite"])
            environment = st.selectbox("Environment", ["Indoor","Outdoor","Greenhouse"])
            type_p = st.selectbox("Type", ["Seed","Clone","Mother"])
        with c2:
            source = st.text_input("Source")
            batch = st.text_input("Batch #")
            date_germ = st.date_input("Date Germination", value=None)
            date_trans = st.date_input("Date Transplant Veg", value=None)
            date_flip = st.date_input("Date Flip Flower", value=None)
            date_harvest = st.date_input("Date Harvest", value=None)
        with c3:
            pot = st.number_input("Pot Size (L)", 0.0, step=0.5)
            medium = st.text_input("Medium")
            rating = st.slider("Rating", 1, 10, 5)
            status = st.selectbox("Status", ["Germinating","Veg","Flower","Drying","Cured","Sold","Gifted","Lost"])

        notes = st.text_area("Phenotype Notes")
        health = st.text_area("Health Issues")
        photos = st.text_input("Photos Link")

        if st.button("Add Plant", type="primary") and plant_id and strain:
            new = pd.DataFrame([{
                "Plant ID": plant_id, "Strain Name": strain, "Variety": variety, "Gender": gender,
                "Environment": environment, "Type": type_p, "Source": source, "Batch #": batch,
                "Date Germination": date_germ, "Date Transplant Veg": date_trans,
                "Date Flip Flower": date_flip, "Date Harvest": date_harvest,
                "Wet Weight (g)": 0, "Dry Weight (g)": 0, "Trimmed Yield (g)": 0,
                "Mother ID": "", "Pot Size (L)": pot, "Medium": medium,
                "Phenotype Notes": notes, "Health Issues": health,
                "Rating (1-10)": rating, "Photos Link": photos, "Status": status
            }])
            st.session_state.plants = pd.concat([st.session_state.plants, new], ignore_index=True)
            st.success("Plant added!")
            st.rerun()

elif page == "Strains Library":
    st.title("Strains Library")
    t1, t2 = st.tabs(["View Strains", "Add New Strain"])
    with t1:
        if len(st.session_state.strains)>0:
            st.dataframe(st.session_state.strains, use_container_width=True, hide_index=True)
        else:
            st.info("No strains recorded yet")
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Strain Name *")
            breeder = st.text_input("Breeder")
            variety = st.selectbox("Variety", ["Sativa","Indica","Hybrid","Autoflower"])
        with c2:
            thc = st.number_input("THC %", 0.0, 40.0, step=0.1)
            weeks = st.text_input("Expected Flower Time (weeks)")
            keeper = st.selectbox("Keeper?", ["Yes","No","Maybe"])
        notes = st.text_area("Best Pheno Notes")
        if st.button("Add Strain", type="primary") and name:
            new = pd.DataFrame([{"Strain Name": name, "Breeder": breeder, "Variety": variety,
                                "Expected Flower Time": weeks, "THC %": thc, "Terpene Profile": "",
                                "Average Yield (g/plant)": 0, "Times Grown": 0,
                                "Best Pheno Notes": notes, "Keeper?": keeper}])
            st.session_state.strains = pd.concat([st.session_state.strains, new], ignore_index=True)
            st.success("Strain added!")
            st.rerun()

elif page == "Expenses":
    st.title("Expenses Tracker")
    categories = ["Seeds","Clones","Nutrients","Soil/Substrate","Pots/Fabric pots","Grow Lights","Tents/Fans",
                  "Electricity","Water","Pest control","Labor","Salaries","Dividends","Donations","Marketing","Taxes","Misc"]
    t1, t2 = st.tabs(["View", "Add Expense"])
    with t1:
        if len(st.session_state.expenses)>0:
            st.dataframe(st.session_state.expenses, use_container_width=True, hide_index=True)
        else:
            st.info("No expenses yet")
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            date_e = st.date_input("Date", date.today())
            cat = st.selectbox("Category", categories)
            item = st.text_input("Item *")
            cost = st.number_input("Cost (ZAR)", 0.0, step=0.01)
        with c2:
            qty = st.number_input("Quantity", 1, step=1)
            paid = st.text_input("Paid To")
        if st.button("Add Expense", type="primary"):
            new = pd.DataFrame([{"Date": date_e, "Category": cat, "Item": item, "Supplier": "", "Cost (ZAR)": cost,
                                "Quantity": qty, "Paid To": paid, "Notes": "", "Receipt Link": ""}])
            st.session_state.expenses = pd.concat([st.session_state.expenses, new], ignore_index=True)
            st.rerun()

elif page == "Income":
    st.title("Income Tracker")
    t1, t2 = st.tabs(["View", "Add Income"])
    with t1:
        if len(st.session_state.income)>0:
            df = st.session_state.income.copy()
            df["Total"] = df["Grams Sold"] * df["Price per Gram"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No income yet")
    with t2:
        c1, c2 = st.columns(2)
        with c1:
            date_i = st.date_input("Date", date.today())
            strain_i = st.text_input("Strain")
            grams = st.number_input("Grams Sold", 0.0, step=0.1)
            ppg = st.number_input("Price per Gram", 0.0, step=0.01)
            source = st.selectbox("Source", ["Harvest Sale","Clone Sale","Capital Invested","Other"])
        with c2:
            buyer = st.text_input("Buyer/Channel")
            method = st.selectbox("Payment Method", ["Cash","EFT","Crypto","Other"])
        if st.button("Add Income", type="primary"):
            new = pd.DataFrame([{"Date": date_i, "Strain": strain_i, "Grams Sold": grams,
                                "Price per Gram": ppg, "Buyer/Channel": buyer,
                                "Payment Method": method, "Notes": ""}])
            st.session_state.income = pd.concat([st.session_state.income, new], ignore_index=True)
            st.rerun()

elif page == "Seed & Clone Stock":
    st.title("Seed & Clone Stock")
    t1, t2 = st.tabs(["View", "Add Stock"])
    with t1:
        if len(st.session_state.stock)>0:
            df = st.session_state.stock.copy()
            df["Cost/Unit"] = df["Pack Cost (ZAR)"] / df["Seeds/Clones Left"].replace(0,1)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No stock recorded")
    with t2:
        c1, c2 = st.columns(2)
        with c1: strain_s = st.text_input("Strain *")
        with c2: left = st.number_input("Seeds/Clones Left", 0, step=1)
        with c1: cost_s = st.number_input("Pack Cost (ZAR)", 0.0, step=0.01)
        if st.button("Add Stock", type="primary"):
            new = pd.DataFrame([{"Strain": strain_s, "Breeder": "", "Seeds/Clones Left": left, "Pack Cost (ZAR)": cost_s}])
            st.session_state.stock = pd.concat([st.session_state.stock, new], ignore_index=True)
            st.rerun()

elif page == "Export to Excel":
    st.title("Export to Excel")
    if st.button("Generate Excel File", type="primary"):
        buf = export_to_excel()
        st.download_button("DOWNLOAD NOW", buf, f"Cannabis_Grow_Tracker_{date.today()}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.success("File ready!")

# ===================== FOOTER =====================
# === FINAL FOOTER WITH EMOJIS – 100% STABLE & BEAUTIFUL ===
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"<div style='text-align:center'>Plants<br><b>{len(st.session_state.plants)}</b></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div style='text-align:center'>Strains<br><b>{len(st.session_state.strains)}</b></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div style='text-align:center'>Expenses<br><b>{len(st.session_state.expenses)}</b></div>", unsafe_allow_html=True)
with c4:
    st.markdown(f"<div style='text-align:center'>Income<br><b>{len(st.session_state.income)}</b></div>", unsafe_allow_html=True)
with c5:
    st.markdown(f"<div style='text-align:center'>Stock<br><b>{len(st.session_state.stock)}</b></div>", unsafe_allow_html=True)
