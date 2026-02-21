import streamlit as st
import pandas as pd
import os
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image

# --- 1. SYSTEM SETTINGS & UI ---
st.set_page_config(page_title="LOG MASTER VENTURES", layout="wide", page_icon="⚖️")

def apply_custom_style():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stMetric { background-color: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
        [data-testid="stSidebar"] { background-color: #0f172a; }
        .stButton>button { border-radius: 10px; font-weight: bold; height: 3em; width: 100%; transition: 0.3s; }
        .stDataFrame { border: 1px solid #334155; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- 2. SECURE IDENTITY ---
COMPANY_NAME = "LOG MASTER VENTURES"
COMPANY_PHONE = st.secrets.get("COMPANY_PHONE", "0545531632")
COMPANY_EMAIL = st.secrets.get("COMPANY_EMAIL", "logmastergh@gmail.com")
MASTER_PASS = st.secrets.get("ADMIN_PASSWORD", "master77")

# --- 3. DATABASE STRUCTURE ---
FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
IMG_DIR, BACKUP_DIR = "product_images", "backups"

HEADERS = {
    "sales": [
        "Timestamp", "Type", "Item", "Qty", "Price", "Total", 
        "Cost", "Profit", "Staff", "Cust_Name", "Cust_Phone", 
        "IMEI_Serial", "Device_Fault", "Parts_Needed", "Status", "Notes"
    ],
    "inventory": ["Product Name", "Brand", "Cost Price", "Selling Price", "Stock", "Min_Stock", "Image_Path"],
    "users": ["username", "password", "role"]
}

# --- 4. INITIALIZATION ENGINE ---
def init_db():
    for folder in [IMG_DIR, BACKUP_DIR]:
        if not os.path.exists(folder): os.makedirs(folder)
    
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        else:
            # Deep structure check
            df = pd.read_csv(path)
            missing = [c for c in HEADERS[key] if c not in df.columns]
            if missing:
                for col in missing:
                    df[col] = 0.0 if col in ["Price", "Total", "Cost", "Profit", "Qty", "Stock", "Cost Price", "Selling Price"] else ("" if col != "Min_Stock" else 2.0)
                df.to_csv(path, index=False)
    
    # Ensure Master Admin exists
    u_df = pd.read_csv(FILES["users"])
    if u_df.empty:
        pd.DataFrame([{"username": "ADMIN", "password": MASTER_PASS, "role": "OWNER"}]).to_csv(FILES["users"], index=False)

init_db()

# --- 5. DATA LOADING (WITH TYPE ENFORCEMENT) ---
def load_data(key):
    df = pd.read_csv(FILES[key])
    if key == "sales":
        for col in ["Total", "Cost", "Profit", "Price", "Qty"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    if key == "inventory":
        for col in ["Cost Price", "Selling Price", "Stock", "Min_Stock"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 6. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title(f"⚖️ {COMPANY_NAME}")
    l_tab, t_tab = st.tabs(["🔒 Staff Login", "🔎 Repair Tracker"])
    with l_tab:
        with st.form("login"):
            u = st.text_input("User ID").upper().strip()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN"):
                udb = load_data("users")
                match = udb[(udb['username'] == u) & (udb['password'].astype(str) == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user, st.session_state.role = True, u, match.iloc[0]['role']
                    st.rerun()
                else: st.error("Invalid credentials.")
    with t_tab:
        track = st.text_input("Enter Phone/IMEI").strip()
        if track:
            sdb = load_data("sales")
            found = sdb[(sdb['Cust_Phone'].astype(str) == track) | (sdb['IMEI_Serial'].astype(str) == track)]
            for _, r in found.iterrows():
                st.info(f"**Item:** {r['Item']} | **Current Status:** {r['Status']}")
    st.stop()

# --- 7. GLOBAL STATE ---
sales_df = load_data("sales")
stock_df = load_data("inventory")
users_df = load_data("users")

# --- 8. SIDEBAR ---
with st.sidebar:
    st.title(f"👤 {st.session_state.user}")
    st.caption(f"Role: {st.session_state.role}")
    st.divider()
    nav = ["📊 Insights", "🛒 Sales POS", "🛠️ Repairs", "📦 Inventory", "⚙️ Admin"]
    if st.session_state.role != "OWNER": nav.remove("⚙️ Admin")
    menu = st.radio("Menu", nav)
    st.divider()
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 9. MODULES ---

if menu == "📊 Insights":
    st.header("📊 Dashboard")
    low = stock_df[stock_df['Stock'] <= stock_df['Min_Stock']]
    if not low.empty: st.error(f"⚠️ {len(low)} items need restocking!")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Stock Assets", f"GHS {(stock_df['Stock'] * stock_df['Cost Price']).sum():,.2f}")
    if st.session_state.role == "OWNER":
        c2.metric("Revenue", f"GHS {sales_df['Total'].sum():,.2f}")
        c3.metric("Net Profit", f"GHS {sales_df['Profit'].sum():,.2f}")
    
    st.subheader("Recent Activity Log")
    st.dataframe(sales_df.tail(15).iloc[::-1], use_container_width=True)

elif menu == "🛒 Sales POS":
    st.header("🛒 Point of Sale")
    with st.form("pos", clear_on_submit=True):
        col_l, col_r = st.columns([2, 1])
        with col_l:
            cn, cp = st.text_input("Customer Name"), st.text_input("Customer Phone")
            valid_items = stock_df[stock_df['Stock'] > 0]['Product Name'].tolist()
            item = st.selectbox("Select Product", valid_items if valid_items else ["OUT OF STOCK"])
            qty = st.number_input("Qty", 1, step=1)
            price = st.number_input("Unit Price", 0.0)
            sn, notes = st.text_input("IMEI / Serial"), st.text_input("Notes")
        with col_r:
            if item != "OUT OF STOCK":
                s_info = stock_df[stock_df['Product Name'] == item].iloc[0]
                st.write(f"In Stock: {s_info['Stock']}")
                if pd.notnull(s_info['Image_Path']) and os.path.exists(str(s_info['Image_Path'])):
                    st.image(str(s_info['Image_Path']), use_column_width=True)
        
        if st.form_submit_button("Complete Sale"):
            if item != "OUT OF STOCK":
                cost_p = float(stock_df[stock_df['Product Name'] == item]['Cost Price'].iloc[0])
                total_p = qty * price
                new_row = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "PRODUCT", "Item": item,
                    "Qty": qty, "Price": price, "Total": total_p, "Cost": cost_p * qty, "Profit": total_p - (cost_p * qty),
                    "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": sn,
                    "Device_Fault": "", "Parts_Needed": "", "Status": "Sold", "Notes": notes
                }
                pd.concat([sales_df, pd.DataFrame([new_row])], ignore_index=True).to_csv(FILES["sales"], index=False)
                stock_df.loc[stock_df['Product Name'] == item, 'Stock'] -= qty
                stock_df.to_csv(FILES["inventory"], index=False)
                st.success("Sale Recorded Successfully!")
                st.rerun()

elif menu == "🛠️ Repairs":
    st.header("🛠️ Repair Intake")
    with st.form("repair_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            cn, cp = st.text_input("Customer Name"), st.text_input("Customer Phone")
            dev, imei = st.text_input("Device Model"), st.text_input("IMEI / Serial")
        with c2:
            fault, parts = st.text_area("Problem Description"), st.text_area("Parts Needed")
            fee = st.number_input("Service Fee", 0.0)
        if st.form_submit_button("Register Job"):
            new_job = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "SERVICE", "Item": dev,
                "Qty": 1, "Price": fee, "Total": fee, "Cost": 0.0, "Profit": fee,
                "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": imei,
                "Device_Fault": fault, "Parts_Needed": parts, "Status": "Repairing", "Notes": ""
            }
            pd.concat([sales_df, pd.DataFrame([new_job])], ignore_index=True).to_csv(FILES["sales"], index=False)
            st.success("Repair Job Logged!")
            st.rerun()

elif menu == "📦 Inventory":
    st.header("📦 Inventory")
    v_tab, a_tab = st.tabs(["Stock View", "Add Item"])
    with v_tab:
        st.dataframe(stock_df, use_container_width=True, column_config={"Image_Path": st.column_config.ImageColumn()})
    with a_tab:
        with st.form("add_item"):
            n, b, cp, sp, s = st.text_input("Name"), st.text_input("Brand"), st.number_input("Cost"), st.number_input("Sell"), st.number_input("Qty")
            up = st.file_uploader("Image", type=['jpg', 'png'])
            if st.form_submit_button("Save Product"):
                path = os.path.join(IMG_DIR, f"{n.replace(' ','_')}.png") if up else ""
                if up: Image.open(up).save(path)
                pd.concat([stock_df, pd.DataFrame([{"Product Name": n, "Brand": b, "Cost Price": cp, "Selling Price": sp, "Stock": s, "Min_Stock": 2, "Image_Path": path}])], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.rerun()

elif menu == "⚙️ Admin":
    st.header("⚙️ Owner Control")
    tab_m, tab_u = st.tabs(["📑 Transaction Manager", "👥 Staff Management"])
    
    with tab_m:
        search = st.text_input("Search Name/IMEI").lower()
        # Keep track of original index
        filtered = sales_df[sales_df.apply(lambda r: search in r.astype(str).str.lower().values, axis=1)] if search else sales_df.tail(10)
        
        if not filtered.empty:
            sel_idx = st.selectbox("Select Record", filtered.index, format_func=lambda x: f"ID: {x} | {sales_df.at[x, 'Item']} | {sales_df.at[x, 'Cust_Name']}")
            r = sales_df.loc[sel_idx]
            
            st.info(f"**Staff:** {r['Staff']} | **Fault:** {r.get('Device_Fault', 'None')}")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Delete Record"):
                    sales_df.drop(sel_idx).to_csv(FILES["sales"], index=False)
                    st.rerun()
            with c2:
                msg = f"LOG MASTER: Hello {r['Cust_Name']}, your {r['Item']} is {r['Status']}."
                url = f"https://wa.me/{r['Cust_Phone']}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; border-radius:10px; width:100%;">WhatsApp Alert</button></a>', unsafe_allow_html=True)
            
            with st.form("status_up"):
                new_s = st.selectbox("Update Status", ["Repairing", "Ready", "Collected", "Sold", "Cancelled"])
                if st.form_submit_button("Save Update"):
                    sales_df.at[sel_idx, 'Status'] = new_s
                    sales_df.to_csv(FILES["sales"], index=False)
                    st.rerun()