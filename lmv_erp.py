import streamlit as st
import pandas as pd
import os
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image

# --- 1. MODERN UI CONFIG ---
st.set_page_config(page_title="LOG MASTER VENTURES", layout="wide", page_icon="⚖️")

def apply_modern_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stMetric { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; }
        [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
        .stButton>button { border-radius: 8px; font-weight: 600; transition: 0.3s; width: 100%; background-color: #3b82f6; color: white; border: none; }
        .stButton>button:hover { background-color: #2563eb; transform: translateY(-2px); }
        </style>
    """, unsafe_allow_html=True)

apply_modern_ui()

# --- 2. IDENTITY & DB ARCHITECTURE ---
COMPANY_NAME = "LOG MASTER VENTURES"
COMPANY_PHONE = "0545531632"
COMPANY_EMAIL = "logmastergh@gmail.com"
MASTER_PASS = "master77" # Default Admin Password

FILES = {"sales": "lmv_sales.csv", "inventory": "lmv_stock.csv", "users": "lmv_users.csv"}
IMG_DIR, BACKUP_DIR = "product_images", "backups"

HEADERS = {
    "sales": ["Timestamp", "Type", "Item", "Qty", "Price", "Total", "Cost", "Profit", "Staff", "Cust_Name", "Cust_Phone", "IMEI_Serial", "Device_Fault", "Parts_Needed", "Status", "Notes"],
    "inventory": ["Product Name", "Brand", "Cost Price", "Selling Price", "Stock", "Min_Stock", "Image_Path"],
    "users": ["username", "password", "role"]
}

# --- 3. CRASH-PROOF INITIALIZATION ---
def init_system():
    for folder in [IMG_DIR, BACKUP_DIR]:
        if not os.path.exists(folder): os.makedirs(folder)
    
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        else:
            df = pd.read_csv(path)
            # Force add any missing columns without breaking existing data
            missing = [c for c in HEADERS[key] if c not in df.columns]
            if missing:
                for col in missing:
                    df[col] = 0.0 if col in ["Price", "Total", "Cost", "Profit", "Qty", "Stock", "Cost Price", "Selling Price"] else ""
                df.to_csv(path, index=False)

    # Ensure Admin exists
    u_df = pd.read_csv(FILES["users"])
    if u_df.empty:
        pd.DataFrame([{"username": "ADMIN", "password": MASTER_PASS, "role": "OWNER"}]).to_csv(FILES["users"], index=False)

init_system()

# --- 4. DATA LOADING (NUMERIC ENFORCEMENT) ---
def load_data(key):
    df = pd.read_csv(FILES[key])
    if key == "inventory":
        for col in ["Cost Price", "Selling Price", "Stock"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    elif key == "sales":
        for col in ["Total", "Cost", "Profit", "Price", "Qty"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- 5. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"<h1 style='text-align:center;'>⚖️ {COMPANY_NAME}</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Username").upper().strip()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN"):
                udb = load_data("users")
                match = udb[(udb['username'] == u) & (udb['password'].astype(str) == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user, st.session_state.role = True, u, match.iloc[0]['role']
                    st.rerun()
                else: st.error("Access Denied")
    st.stop()

# --- 6. GLOBAL REFRESH ---
stock_df = load_data("inventory")
sales_df = load_data("sales")
users_df = load_data("users")

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    st.caption(f"Role: {st.session_state.role}")
    st.divider()
    nav = ["📊 Insights", "🛒 Sales POS", "🛠️ Repairs", "📦 Inventory", "⚙️ Admin"]
    if st.session_state.role != "OWNER": nav.remove("⚙️ Admin")
    menu = st.radio("MAIN MENU", nav)
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 8. MODULES ---

if menu == "📊 Insights":
    st.title("📊 Enterprise Analytics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Asset Value", f"GHS {(stock_df['Stock'] * stock_df['Cost Price']).sum():,.2f}")
    if st.session_state.role == "OWNER":
        c2.metric("Gross Revenue", f"GHS {sales_df['Total'].sum():,.2f}")
        c3.metric("Net Profit", f"GHS {sales_df['Profit'].sum():,.2f}")
    
    st.subheader("Latest Transactions")
    if not sales_df.empty:
        st.dataframe(sales_df.tail(15).iloc[::-1], use_container_width=True)
    else:
        st.info("No transactions logged yet.")

elif menu == "🛒 Sales POS":
    st.title("🛒 Sales Terminal")
    if stock_df.empty:
        st.warning("Your inventory is empty. Please add products in the Inventory tab first.")
    else:
        with st.container(border=True):
            with st.form("sale_form", clear_on_submit=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    cn = st.text_input("Customer Name")
                    cp = st.text_input("Customer Phone")
                    valid_items = stock_df[stock_df['Stock'] > 0]['Product Name'].tolist()
                    item = st.selectbox("Product", valid_items if valid_items else ["OUT OF STOCK"])
                    q = st.number_input("Quantity", min_value=1, step=1)
                    p = st.number_input("Selling Price (GHS)", min_value=0.0)
                    imei = st.text_input("IMEI / Serial Number")
                    note = st.text_input("Additional Notes")
                with col2:
                    if item != "OUT OF STOCK":
                        s_row = stock_df[stock_df['Product Name'] == item].iloc[0]
                        st.write(f"**In Stock:** {s_row['Stock']}")
                        if pd.notnull(s_row['Image_Path']) and os.path.exists(str(s_row['Image_Path'])):
                            st.image(str(s_row['Image_Path']), use_column_width=True)
                
                if st.form_submit_button("PROCESS SALE", use_container_width=True):
                    if item != "OUT OF STOCK":
                        cost = float(stock_df[stock_df['Product Name'] == item]['Cost Price'].iloc[0])
                        total = q * p
                        # Enforce exact 16 columns
                        new_sale = {
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "PRODUCT", "Item": item,
                            "Qty": q, "Price": p, "Total": total, "Cost": cost*q, "Profit": total-(cost*q),
                            "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": imei,
                            "Device_Fault": "", "Parts_Needed": "", "Status": "Sold", "Notes": note
                        }
                        pd.concat([sales_df, pd.DataFrame([new_sale])], ignore_index=True).to_csv(FILES["sales"], index=False)
                        stock_df.loc[stock_df['Product Name'] == item, 'Stock'] -= q
                        stock_df.to_csv(FILES["inventory"], index=False)
                        st.success(f"Sale successful! {q}x {item} deducted from stock.")
                        st.rerun()

elif menu == "🛠️ Repairs":
    st.title("🛠️ Repair Intake")
    with st.container(border=True):
        with st.form("rep_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                cn = st.text_input("Customer Name")
                cp = st.text_input("Phone Number")
                dev = st.text_input("Device Model")
                sn = st.text_input("IMEI / Serial")
            with c2:
                f = st.text_area("Reported Fault")
                p = st.text_area("Parts Needed")
                fee = st.number_input("Service Fee (GHS)", min_value=0.0)
            
            if st.form_submit_button("REGISTER REPAIR JOB", use_container_width=True):
                # Enforce exact 16 columns
                new_rep = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "SERVICE", "Item": dev,
                    "Qty": 1, "Price": fee, "Total": fee, "Cost": 0.0, "Profit": fee,
                    "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": sn,
                    "Device_Fault": f, "Parts_Needed": p, "Status": "Repairing", "Notes": ""
                }
                pd.concat([sales_df, pd.DataFrame([new_rep])], ignore_index=True).to_csv(FILES["sales"], index=False)
                st.success("Repair Job registered successfully!")
                st.rerun()

elif menu == "📦 Inventory":
    st.title("📦 Stock Control")
    t1, t2, t3 = st.tabs(["Warehouse View", "Stock Adjustment", "Add New Item"])
    
    with t1:
        st.dataframe(stock_df, use_container_width=True, column_config={"Image_Path": st.column_config.ImageColumn()})

    with t2:
        st.subheader("Update Stock Levels")
        if stock_df.empty:
            st.warning("No products to adjust. Add a product first.")
        else:
            with st.form("adj_form"):
                target = st.selectbox("Select Product", stock_df['Product Name'].tolist())
                # Safe extraction to prevent index crashes
                current_q = stock_df.loc[stock_df['Product Name'] == target, 'Stock'].iloc[0]
                st.info(f"Current Stock for **{target}**: {current_q}")
                
                mode = st.radio("Action Type", ["Add New Stock (+)", "Remove Stock (-)"])
                amt = st.number_input("Amount to Adjust", min_value=1, step=1)
                
                if st.form_submit_button("PROCESS ADJUSTMENT"):
                    new_q = current_q + amt if "Add" in mode else current_q - amt
                    if new_q < 0:
                        st.error("Operation failed: Stock cannot fall below zero.")
                    else:
                        stock_df.loc[stock_df['Product Name'] == target, 'Stock'] = new_q
                        stock_df.to_csv(FILES["inventory"], index=False)
                        st.success(f"Stock adjusted! New quantity for {target} is {new_q}.")
                        st.rerun()

    with t3:
        with st.form("add_prod_form"):
            n = st.text_input("Product Name")
            b = st.text_input("Brand")
            cp = st.number_input("Cost Price", min_value=0.0)
            sp = st.number_input("Selling Price", min_value=0.0)
            s = st.number_input("Initial Stock Quantity", min_value=0, step=1)
            up = st.file_uploader("Upload Image (Optional)", type=['jpg','png'])
            
            if st.form_submit_button("SAVE NEW PRODUCT"):
                if not n:
                    st.error("Product Name is required!")
                else:
                    path = os.path.join(IMG_DIR, f"{n.replace(' ','_')}.png") if up else ""
                    if up: Image.open(up).save(path)
                    new_item = pd.DataFrame([{"Product Name": n, "Brand": b, "Cost Price": cp, "Selling Price": sp, "Stock": s, "Min_Stock": 2, "Image_Path": path}])
                    pd.concat([stock_df, new_item], ignore_index=True).to_csv(FILES["inventory"], index=False)
                    st.success(f"{n} added to warehouse!")
                    st.rerun()

elif menu == "⚙️ Admin":
    st.title("⚙️ System Control")
    t1, t2 = st.tabs(["📑 Order & Repair Manager", "👥 User Control"])
    
    with t1:
        if sales_df.empty:
            st.info("No records available to manage.")
        else:
            q = st.text_input("Search (Customer Name, Device, IMEI)").lower()
            filtered = sales_df[sales_df.apply(lambda r: q in r.astype(str).str.lower().values, axis=1)] if q else sales_df.tail(10)
            
            if not filtered.empty:
                sel = st.selectbox("Select Record to Manage", filtered.index, format_func=lambda x: f"ID: {x} | {sales_df.at[x, 'Item']} | Cust: {sales_df.at[x, 'Cust_Name']}")
                r = sales_df.loc[sel]
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🗑️ Delete This Record"):
                        sales_df.drop(sel).to_csv(FILES["sales"], index=False)
                        st.rerun()
                with c2:
                    msg = f"LOG MASTER VENTURES: Hello {r['Cust_Name']}, your {r['Item']} is currently {r['Status']}."
                    url = f"https://wa.me/{r['Cust_Phone']}?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{url}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; border-radius:8px; width:100%; font-weight:bold;">WhatsApp Notify</button></a>', unsafe_allow_html=True)
                
                with st.form("status_update"):
                    st.write(f"Updating status for: **{r['Item']}**")
                    ns = st.selectbox("Change Status", ["Repairing", "Ready", "Collected", "Sold", "Cancelled", "Refunded"])
                    if st.form_submit_button("UPDATE STATUS"):
                        sales_df.at[sel, 'Status'] = ns
                        sales_df.to_csv(FILES["sales"], index=False)
                        st.success("Status updated!")
                        st.rerun()
            else:
                st.warning("No records found matching your search.")

    with t2:
        st.subheader("Manage Staff Credentials")
        st.dataframe(users_df[['username', 'role']], use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🔑 Change Password")
            with st.form("pass_form"):
                target_u = st.selectbox("Select User", users_df['username'].tolist())
                new_p = st.text_input("Enter New Password", type="password")
                if st.form_submit_button("SAVE NEW PASSWORD"):
                    users_df.loc[users_df['username'] == target_u, 'password'] = new_p
                    users_df.to_csv(FILES["users"], index=False)
                    st.success(f"Password for {target_u} updated successfully!")
        
        with c2:
            st.markdown("### ➕ Register New Staff")
            with st.form("new_u_form"):
                nu = st.text_input("Username").upper().strip()
                nup = st.text_input("Initial Password", type="password")
                nur = st.selectbox("Role", ["STAFF", "OWNER"])
                if st.form_submit_button("CREATE ACCOUNT"):
                    if not nu or not nup:
                        st.error("Username and Password are required.")
                    elif nu in users_df['username'].values:
                        st.error("Username already exists!")
                    else:
                        pd.concat([users_df, pd.DataFrame([{"username": nu, "password": nup, "role": nur}])], ignore_index=True).to_csv(FILES["users"], index=False)
                        st.success(f"User {nu} created!")
                        st.rerun()