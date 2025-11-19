import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
import io

st.set_page_config(page_title="Cannabis Grow Tracker", layout="wide", page_icon="🌿")

def initialize_session_state():
    if 'plants' not in st.session_state:
        st.session_state.plants = pd.DataFrame(columns=[
            'Plant ID', 'Strain Name', 'Variety', 'Type', 'Source', 'Batch #',
            'Date Germination', 'Date Transplant Veg', 'Date Flip Flower', 'Date Harvest',
            'Wet Weight (g)', 'Dry Weight (g)', 'Trimmed Yield (g)', 'Mother ID',
            'Pot Size (L)', 'Medium', 'Phenotype Notes', 'Health Issues',
            'Rating (1-10)', 'Photos Link', 'Status'
        ])
    
    if 'strains' not in st.session_state:
        st.session_state.strains = pd.DataFrame(columns=[
            'Strain Name', 'Breeder', 'Variety', 'Expected Flower Time', 'THC %',
            'Terpene Profile', 'Average Yield (g/plant)', 'Times Grown',
            'Best Pheno Notes', 'Keeper?'
        ])
    
    if 'expenses' not in st.session_state:
        st.session_state.expenses = pd.DataFrame(columns=[
            'Date', 'Category', 'Item', 'Supplier', 'Cost (ZAR)', 'Quantity',
            'Paid To', 'Notes', 'Receipt Link'
        ])
    
    if 'income' not in st.session_state:
        st.session_state.income = pd.DataFrame(columns=[
            'Date', 'Strain', 'Grams Sold', 'Price per Gram', 'Buyer/Channel',
            'Payment Method', 'Notes'
        ])
    
    if 'stock' not in st.session_state:
        st.session_state.stock = pd.DataFrame(columns=[
            'Strain', 'Breeder', 'Seeds/Clones Left', 'Pack Cost (ZAR)'
        ])

initialize_session_state()

def calculate_flowering_days(flip_date, harvest_date):
    if pd.notna(flip_date) and pd.notna(harvest_date):
        return (harvest_date - flip_date).days
    return None

def calculate_total_days(germ_date, harvest_date):
    if pd.notna(germ_date) and pd.notna(harvest_date):
        return (harvest_date - germ_date).days
    return None

def export_to_excel():
    wb = Workbook()
    if wb.active:
        wb.remove(wb.active)
    
    def add_headers(ws, headers):
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
    
    ws1 = wb.create_sheet("Dashboard")
    ws1['A1'] = "Cannabis Grow Tracker - Dashboard"
    ws1['A1'].font = Font(bold=True, size=16)
    ws1.merge_cells('A1:C1')
    ws1['A1'].alignment = Alignment(horizontal='center')
    
    total_plants = len(st.session_state.plants)
    total_yield = st.session_state.plants['Trimmed Yield (g)'].sum() if 'Trimmed Yield (g)' in st.session_state.plants.columns else 0
    total_expenses = st.session_state.expenses['Cost (ZAR)'].sum() if 'Cost (ZAR)' in st.session_state.expenses.columns else 0
    
    if len(st.session_state.income) > 0:
        st.session_state.income['Total'] = st.session_state.income['Grams Sold'] * st.session_state.income['Price per Gram']
        total_income = st.session_state.income['Total'].sum()
    else:
        total_income = 0
    
    net_profit = total_income - total_expenses
    cost_per_gram = total_expenses / total_yield if total_yield > 0 else 0
    
    ws1['A2'] = "Total Plants Started:"
    ws1['B2'] = total_plants
    ws1['A3'] = "Total Yield (g):"
    ws1['B3'] = total_yield
    ws1['A4'] = "Total Expenses (ZAR):"
    ws1['B4'] = total_expenses
    ws1['A5'] = "Total Income (ZAR):"
    ws1['B5'] = total_income
    ws1['A6'] = "Net Profit (ZAR):"
    ws1['B6'] = net_profit
    ws1['A7'] = "Cost per Gram (ZAR):"
    ws1['B7'] = cost_per_gram
    
    for cell in ['B4', 'B5', 'B6', 'B7']:
        ws1[cell].number_format = '#,##0.00 "ZAR"'
    
    ws2 = wb.create_sheet("Plants Tracker")
    plants_df = st.session_state.plants.copy()
    
    for row_idx, row in plants_df.iterrows():
        if pd.notna(row.get('Date Flip Flower')) and pd.notna(row.get('Date Harvest')):
            plants_df.at[row_idx, 'Flowering Days'] = calculate_flowering_days(
                row['Date Flip Flower'], row['Date Harvest']
            )
        if pd.notna(row.get('Date Germination')) and pd.notna(row.get('Date Harvest')):
            plants_df.at[row_idx, 'Total Days'] = calculate_total_days(
                row['Date Germination'], row['Date Harvest']
            )
    
    headers2 = [
        "Plant ID", "Strain Name", "Variety", "Type", "Source", "Batch #",
        "Date Germination", "Date Transplant Veg", "Date Flip Flower", "Date Harvest",
        "Wet Weight (g)", "Dry Weight (g)", "Trimmed Yield (g)", "Flowering Days",
        "Total Days", "Mother ID", "Pot Size (L)", "Medium", "Phenotype Notes",
        "Health Issues", "Rating (1-10)", "Photos Link", "Status"
    ]
    add_headers(ws2, headers2)
    
    for r_idx, row in enumerate(plants_df.itertuples(index=False), start=2):
        for c_idx, value in enumerate(row, start=1):
            ws2.cell(row=r_idx, column=c_idx, value=value)
    
    ws3 = wb.create_sheet("Strains Library")
    headers3 = ["Strain Name", "Breeder", "Variety", "Expected Flower Time", "THC %",
                "Terpene Profile", "Average Yield (g/plant)", "Times Grown",
                "Best Pheno Notes", "Keeper?"]
    add_headers(ws3, headers3)
    for r_idx, row in enumerate(st.session_state.strains.itertuples(index=False), start=2):
        for c_idx, value in enumerate(row, start=1):
            ws3.cell(row=r_idx, column=c_idx, value=value)
    
    ws4 = wb.create_sheet("Expenses")
    expenses_df = st.session_state.expenses.copy()
    expenses_df['Unit Cost'] = expenses_df.apply(
        lambda row: row['Cost (ZAR)'] / row['Quantity'] if row['Quantity'] > 0 else 0,
        axis=1
    )
    headers4 = ["Date", "Category", "Item", "Supplier", "Cost (ZAR)", "Quantity",
                "Unit Cost", "Paid To", "Notes", "Receipt Link"]
    add_headers(ws4, headers4)
    for r_idx, row in enumerate(expenses_df.itertuples(index=False), start=2):
        for c_idx, value in enumerate(row, start=1):
            ws4.cell(row=r_idx, column=c_idx, value=value)
    
    ws5 = wb.create_sheet("Income")
    income_df = st.session_state.income.copy()
    income_df['Total (ZAR)'] = income_df['Grams Sold'] * income_df['Price per Gram']
    headers5 = ["Date", "Strain", "Grams Sold", "Price per Gram", "Total (ZAR)",
                "Buyer/Channel", "Payment Method", "Notes"]
    add_headers(ws5, headers5)
    for r_idx, row in enumerate(income_df.itertuples(index=False), start=2):
        for c_idx, value in enumerate(row, start=1):
            ws5.cell(row=r_idx, column=c_idx, value=value)
    
    ws6 = wb.create_sheet("Seed & Clone Stock")
    stock_df = st.session_state.stock.copy()
    stock_df['Cost per Seed'] = stock_df.apply(
        lambda row: row['Pack Cost (ZAR)'] / row['Seeds/Clones Left'] if row['Seeds/Clones Left'] > 0 else 0,
        axis=1
    )
    headers6 = ["Strain", "Breeder", "Seeds/Clones Left", "Pack Cost (ZAR)", "Cost per Seed"]
    add_headers(ws6, headers6)
    for r_idx, row in enumerate(stock_df.itertuples(index=False), start=2):
        for c_idx, value in enumerate(row, start=1):
            ws6.cell(row=r_idx, column=c_idx, value=value)
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

st.sidebar.title("🌿 Cannabis Grow Tracker")
page = st.sidebar.radio("Navigation", [
    "📊 Dashboard",
    "🌱 Plants Tracker",
    "🧬 Strains Library",
    "💰 Expenses",
    "💵 Income",
    "📦 Seed & Clone Stock",
    "📥 Export to Excel"
])

if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_plants = len(st.session_state.plants)
        st.metric("Total Plants", total_plants)
    
    with col2:
        total_yield = st.session_state.plants['Trimmed Yield (g)'].sum() if len(st.session_state.plants) > 0 else 0
        st.metric("Total Yield", f"{total_yield:.1f} g")
    
    with col3:
        total_expenses = st.session_state.expenses['Cost (ZAR)'].sum() if len(st.session_state.expenses) > 0 else 0
        st.metric("Total Expenses", f"R {total_expenses:,.2f}")
    
    with col4:
        if len(st.session_state.income) > 0:
            total_income = (st.session_state.income['Grams Sold'] * st.session_state.income['Price per Gram']).sum()
        else:
            total_income = 0
        st.metric("Total Income", f"R {total_income:,.2f}")
    
    col5, col6, col7 = st.columns(3)
    
    with col5:
        net_profit = total_income - total_expenses
        st.metric("Net Profit", f"R {net_profit:,.2f}", delta=f"{net_profit:,.2f}")
    
    with col6:
        cost_per_gram = total_expenses / total_yield if total_yield > 0 else 0
        st.metric("Cost per Gram", f"R {cost_per_gram:.2f}")
    
    with col7:
        avg_price = total_income / total_yield if total_yield > 0 else 0
        st.metric("Avg Selling Price/g", f"R {avg_price:.2f}")
    
    st.markdown("---")
    
    if len(st.session_state.plants) > 0:
        st.subheader("Plants by Status")
        status_counts = st.session_state.plants['Status'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index, title="Plant Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    if len(st.session_state.expenses) > 0:
        st.subheader("Expenses by Category")
        expense_by_cat = st.session_state.expenses.groupby('Category')['Cost (ZAR)'].sum().sort_values(ascending=False)
        fig2 = px.bar(x=expense_by_cat.index, y=expense_by_cat.values, labels={'x': 'Category', 'y': 'Cost (ZAR)'})
        st.plotly_chart(fig2, use_container_width=True)

elif page == "🌱 Plants Tracker":
    st.title("🌱 Plants Tracker")
    
    tab1, tab2 = st.tabs(["View Plants", "Add New Plant"])
    
    with tab1:
        if len(st.session_state.plants) > 0:
            df_display = st.session_state.plants.copy()
            
            for idx, row in df_display.iterrows():
                if pd.notna(row.get('Date Flip Flower')) and pd.notna(row.get('Date Harvest')):
                    df_display.at[idx, 'Flowering Days'] = calculate_flowering_days(
                        row['Date Flip Flower'], row['Date Harvest']
                    )
                if pd.notna(row.get('Date Germination')) and pd.notna(row.get('Date Harvest')):
                    df_display.at[idx, 'Total Days'] = calculate_total_days(
                        row['Date Germination'], row['Date Harvest']
                    )
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.subheader("Delete Plant")
            if len(st.session_state.plants) > 0:
                plant_to_delete = st.selectbox("Select plant to delete", st.session_state.plants['Plant ID'].tolist())
                if st.button("Delete Plant"):
                    st.session_state.plants = st.session_state.plants[st.session_state.plants['Plant ID'] != plant_to_delete]
                    st.success(f"Plant {plant_to_delete} deleted!")
                    st.rerun()
        else:
            st.info("No plants recorded yet. Add your first plant in the 'Add New Plant' tab!")
    
    with tab2:
        st.subheader("Add New Plant")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            plant_id = st.text_input("Plant ID *", placeholder="e.g., P001")
            strain_name = st.text_input("Strain Name *", placeholder="e.g., Blue Dream")
            variety = st.selectbox("Variety", ["Sativa", "Indica", "Hybrid", "Hybrid-Indica Dominant", "Hybrid-Sativa Dominant"])
            type_plant = st.selectbox("Type", ["Seed", "Clone", "Mother"])
            source = st.text_input("Source", placeholder="e.g., Seedbank name")
            batch = st.text_input("Batch #")
        
        with col2:
            date_germ = st.date_input("Date Germination", value=None)
            date_transplant = st.date_input("Date Transplant to Veg", value=None)
            date_flip = st.date_input("Date Flip to Flower", value=None)
            date_harvest = st.date_input("Date Harvest", value=None)
            wet_weight = st.number_input("Wet Weight (g)", min_value=0.0, step=0.1)
            dry_weight = st.number_input("Dry Weight (g)", min_value=0.0, step=0.1)
        
        with col3:
            trimmed_yield = st.number_input("Trimmed Yield (g)", min_value=0.0, step=0.1)
            mother_id = st.text_input("Mother ID (if clone)")
            pot_size = st.number_input("Pot Size (L)", min_value=0.0, step=0.5)
            medium = st.text_input("Medium", placeholder="e.g., Soil, Coco, Hydro")
            rating = st.slider("Rating (1-10)", 1, 10, 5)
            status = st.selectbox("Status", ["Germinating", "Veg", "Flower", "Drying", "Cured", "Sold", "Gifted", "Lost"])
        
        pheno_notes = st.text_area("Phenotype Notes")
        health_issues = st.text_area("Health Issues")
        photos_link = st.text_input("Photos Link (URL)")
        
        if st.button("Add Plant", type="primary"):
            if plant_id and strain_name:
                new_plant = {
                    'Plant ID': plant_id,
                    'Strain Name': strain_name,
                    'Variety': variety,
                    'Type': type_plant,
                    'Source': source,
                    'Batch #': batch,
                    'Date Germination': date_germ if date_germ else None,
                    'Date Transplant Veg': date_transplant if date_transplant else None,
                    'Date Flip Flower': date_flip if date_flip else None,
                    'Date Harvest': date_harvest if date_harvest else None,
                    'Wet Weight (g)': wet_weight,
                    'Dry Weight (g)': dry_weight,
                    'Trimmed Yield (g)': trimmed_yield,
                    'Mother ID': mother_id,
                    'Pot Size (L)': pot_size,
                    'Medium': medium,
                    'Phenotype Notes': pheno_notes,
                    'Health Issues': health_issues,
                    'Rating (1-10)': rating,
                    'Photos Link': photos_link,
                    'Status': status
                }
                st.session_state.plants = pd.concat([st.session_state.plants, pd.DataFrame([new_plant])], ignore_index=True)
                st.success(f"Plant {plant_id} added successfully!")
                st.rerun()
            else:
                st.error("Plant ID and Strain Name are required!")

elif page == "🧬 Strains Library":
    st.title("🧬 Strains Library")
    
    tab1, tab2 = st.tabs(["View Strains", "Add New Strain"])
    
    with tab1:
        if len(st.session_state.strains) > 0:
            st.dataframe(st.session_state.strains, use_container_width=True, hide_index=True)
            
            st.subheader("Delete Strain")
            strain_to_delete = st.selectbox("Select strain to delete", st.session_state.strains['Strain Name'].tolist())
            if st.button("Delete Strain"):
                st.session_state.strains = st.session_state.strains[st.session_state.strains['Strain Name'] != strain_to_delete]
                st.success(f"Strain {strain_to_delete} deleted!")
                st.rerun()
        else:
            st.info("No strains recorded yet. Add your first strain in the 'Add New Strain' tab!")
    
    with tab2:
        st.subheader("Add New Strain")
        
        col1, col2 = st.columns(2)
        
        with col1:
            strain_name = st.text_input("Strain Name *", key="strain_name")
            breeder = st.text_input("Breeder")
            variety = st.selectbox("Variety", ["Sativa", "Indica", "Hybrid", "Hybrid-Indica Dominant", "Hybrid-Sativa Dominant"], key="strain_variety")
            flower_time = st.text_input("Expected Flower Time", placeholder="e.g., 8-10 weeks")
            thc = st.number_input("THC %", min_value=0.0, max_value=100.0, step=0.1)
        
        with col2:
            terpene = st.text_input("Terpene Profile", placeholder="e.g., Myrcene, Limonene")
            avg_yield = st.number_input("Average Yield (g/plant)", min_value=0.0, step=1.0)
            times_grown = st.number_input("Times Grown", min_value=0, step=1)
            keeper = st.selectbox("Keeper?", ["Yes", "No", "Maybe"])
        
        pheno_notes = st.text_area("Best Pheno Notes", key="strain_pheno")
        
        if st.button("Add Strain", type="primary"):
            if strain_name:
                new_strain = {
                    'Strain Name': strain_name,
                    'Breeder': breeder,
                    'Variety': variety,
                    'Expected Flower Time': flower_time,
                    'THC %': thc,
                    'Terpene Profile': terpene,
                    'Average Yield (g/plant)': avg_yield,
                    'Times Grown': times_grown,
                    'Best Pheno Notes': pheno_notes,
                    'Keeper?': keeper
                }
                st.session_state.strains = pd.concat([st.session_state.strains, pd.DataFrame([new_strain])], ignore_index=True)
                st.success(f"Strain {strain_name} added successfully!")
                st.rerun()
            else:
                st.error("Strain Name is required!")

elif page == "💰 Expenses":
    st.title("💰 Expenses Tracker")
    
    tab1, tab2 = st.tabs(["View Expenses", "Add New Expense"])
    
    with tab1:
        if len(st.session_state.expenses) > 0:
            df_display = st.session_state.expenses.copy()
            df_display['Unit Cost'] = df_display.apply(
                lambda row: row['Cost (ZAR)'] / row['Quantity'] if row['Quantity'] > 0 else 0,
                axis=1
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            total = df_display['Cost (ZAR)'].sum()
            st.metric("Total Expenses", f"R {total:,.2f}")
            
            st.subheader("Delete Expense")
            if len(st.session_state.expenses) > 0:
                expense_idx = st.number_input("Enter row number to delete (0-based index)", min_value=0, max_value=len(st.session_state.expenses)-1, step=1)
                if st.button("Delete Expense"):
                    st.session_state.expenses = st.session_state.expenses.drop(st.session_state.expenses.index[expense_idx]).reset_index(drop=True)
                    st.success("Expense deleted!")
                    st.rerun()
        else:
            st.info("No expenses recorded yet. Add your first expense in the 'Add New Expense' tab!")
    
    with tab2:
        st.subheader("Add New Expense")
        
        categories = ["Seeds", "Clones", "Nutrients", "Soil/Substrate", "Pots/Fabric pots", 
                     "Grow Lights", "Tents/Fans", "Extraction", "Trimming", "Drying racks",
                     "Packaging", "Scales", "Printer+labels", "Rosin press", "Electricity",
                     "Water", "Pest control", "Phone credit", "Transport", "Fuel", "Labor",
                     "Marketing", "Licenses", "Misc"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            expense_date = st.date_input("Date *", value=date.today())
            category = st.selectbox("Category *", categories)
            item = st.text_input("Item *", placeholder="e.g., Fox Farm Nutrients")
            supplier = st.text_input("Supplier")
            cost = st.number_input("Cost (ZAR) *", min_value=0.0, step=0.01)
        
        with col2:
            quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
            paid_to = st.text_input("Paid To")
            notes = st.text_area("Notes")
            receipt_link = st.text_input("Receipt Link (URL)")
        
        if st.button("Add Expense", type="primary"):
            if expense_date and category and item and cost > 0:
                new_expense = {
                    'Date': expense_date,
                    'Category': category,
                    'Item': item,
                    'Supplier': supplier,
                    'Cost (ZAR)': cost,
                    'Quantity': quantity,
                    'Paid To': paid_to,
                    'Notes': notes,
                    'Receipt Link': receipt_link
                }
                st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_expense])], ignore_index=True)
                st.success(f"Expense for {item} added successfully!")
                st.rerun()
            else:
                st.error("Date, Category, Item, and Cost are required!")

elif page == "💵 Income":
    st.title("💵 Income Tracker")
    
    tab1, tab2 = st.tabs(["View Income", "Add New Sale"])
    
    with tab1:
        if len(st.session_state.income) > 0:
            df_display = st.session_state.income.copy()
            df_display['Total (ZAR)'] = df_display['Grams Sold'] * df_display['Price per Gram']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            total = df_display['Total (ZAR)'].sum()
            st.metric("Total Income", f"R {total:,.2f}")
            
            st.subheader("Delete Income Record")
            if len(st.session_state.income) > 0:
                income_idx = st.number_input("Enter row number to delete (0-based index)", min_value=0, max_value=len(st.session_state.income)-1, step=1)
                if st.button("Delete Income"):
                    st.session_state.income = st.session_state.income.drop(st.session_state.income.index[income_idx]).reset_index(drop=True)
                    st.success("Income record deleted!")
                    st.rerun()
        else:
            st.info("No income recorded yet. Add your first sale in the 'Add New Sale' tab!")
    
    with tab2:
        st.subheader("Add New Sale")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sale_date = st.date_input("Date *", value=date.today(), key="sale_date")
            strain = st.text_input("Strain *")
            grams_sold = st.number_input("Grams Sold *", min_value=0.0, step=0.1)
            price_per_gram = st.number_input("Price per Gram (ZAR) *", min_value=0.0, step=0.01)
        
        with col2:
            buyer = st.text_input("Buyer/Channel")
            payment_method = st.selectbox("Payment Method", ["Cash", "EFT", "Crypto", "Other"])
            notes = st.text_area("Notes", key="income_notes")
        
        if st.button("Add Sale", type="primary"):
            if sale_date and strain and grams_sold > 0 and price_per_gram > 0:
                new_income = {
                    'Date': sale_date,
                    'Strain': strain,
                    'Grams Sold': grams_sold,
                    'Price per Gram': price_per_gram,
                    'Buyer/Channel': buyer,
                    'Payment Method': payment_method,
                    'Notes': notes
                }
                st.session_state.income = pd.concat([st.session_state.income, pd.DataFrame([new_income])], ignore_index=True)
                st.success(f"Sale of {grams_sold}g of {strain} added successfully!")
                st.rerun()
            else:
                st.error("Date, Strain, Grams Sold, and Price per Gram are required!")

elif page == "📦 Seed & Clone Stock":
    st.title("📦 Seed & Clone Stock")
    
    tab1, tab2 = st.tabs(["View Stock", "Add New Stock"])
    
    with tab1:
        if len(st.session_state.stock) > 0:
            df_display = st.session_state.stock.copy()
            df_display['Cost per Seed'] = df_display.apply(
                lambda row: row['Pack Cost (ZAR)'] / row['Seeds/Clones Left'] if row['Seeds/Clones Left'] > 0 else 0,
                axis=1
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.subheader("Delete Stock")
            if len(st.session_state.stock) > 0:
                stock_idx = st.number_input("Enter row number to delete (0-based index)", min_value=0, max_value=len(st.session_state.stock)-1, step=1)
                if st.button("Delete Stock"):
                    st.session_state.stock = st.session_state.stock.drop(st.session_state.stock.index[stock_idx]).reset_index(drop=True)
                    st.success("Stock deleted!")
                    st.rerun()
        else:
            st.info("No stock recorded yet. Add your first stock in the 'Add New Stock' tab!")
    
    with tab2:
        st.subheader("Add New Stock")
        
        col1, col2 = st.columns(2)
        
        with col1:
            strain = st.text_input("Strain *", key="stock_strain")
            breeder = st.text_input("Breeder", key="stock_breeder")
        
        with col2:
            seeds_left = st.number_input("Seeds/Clones Left *", min_value=0, step=1)
            pack_cost = st.number_input("Pack Cost (ZAR) *", min_value=0.0, step=0.01)
        
        if st.button("Add Stock", type="primary"):
            if strain and seeds_left >= 0 and pack_cost >= 0:
                new_stock = {
                    'Strain': strain,
                    'Breeder': breeder,
                    'Seeds/Clones Left': seeds_left,
                    'Pack Cost (ZAR)': pack_cost
                }
                st.session_state.stock = pd.concat([st.session_state.stock, pd.DataFrame([new_stock])], ignore_index=True)
                st.success(f"Stock for {strain} added successfully!")
                st.rerun()
            else:
                st.error("Strain, Seeds/Clones Left, and Pack Cost are required!")

elif page == "📥 Export to Excel":
    st.title("📥 Export to Excel")
    
    st.write("Download all your data in Excel format matching the original structure with formulas and formatting.")
    
    if st.button("Generate Excel File", type="primary"):
        excel_buffer = export_to_excel()
        
        st.download_button(
            label="Download CannabisGrowTracker.xlsx",
            data=excel_buffer,
            file_name=f"CannabisGrowTracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("Excel file generated! Click the download button above.")
    
    st.markdown("---")
    st.subheader("What's included in the export:")
    st.markdown("""
    - **Dashboard**: Summary metrics with formulas
    - **Plants Tracker**: All plant records with calculated flowering/total days
    - **Strains Library**: All strain information
    - **Expenses**: All expenses with unit cost calculations
    - **Income**: All sales with total calculations
    - **Seed & Clone Stock**: Inventory with cost per seed calculations
    """)

st.sidebar.markdown("---")
st.sidebar.info(f"**Data Status:**\n- Plants: {len(st.session_state.plants)}\n- Strains: {len(st.session_state.strains)}\n- Expenses: {len(st.session_state.expenses)}\n- Income: {len(st.session_state.income)}\n- Stock: {len(st.session_state.stock)}")
