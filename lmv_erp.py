import streamlit as st
import pandas as pd
import os
import shutil
import urllib.parse
from datetime import datetime
from PIL import Image

# --- 1. THE FACELIFT (CUSTOM CSS) ---
def apply_modern_ui():
    st.markdown("""
        <style>
        /* Main Background and Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0e1117;
            border-right: 1px solid #30363d;
        }
        
        /* Dashboard Card Styling */
        .stMetric {
            background-color: #161b22;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid #30363d;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* Button Styling */
        .stButton>button {
            border-radius: 8px;
            text-transform: uppercase;
            font-weight: 600;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        /* Success/Error Styling */
        .stAlert { border-radius: 12px; }
        
        /* Header Styling */
        h1, h2, h3 { color: #f0f6fc; font-weight: 800; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURATION & SECRETS ---
COMPANY_NAME = "LOG MASTER VENTURES"
COMPANY_PHONE = st.secrets.get("COMPANY_PHONE", "0545531632")
COMPANY_EMAIL = st.secrets.get("COMPANY_EMAIL", "logmastergh@gmail.com")
MASTER_PASS = st.secrets.get("ADMIN_PASSWORD", "master77")

st.set_page_config(page_title=COMPANY_NAME, layout="wide", page_icon="⚖️")
apply_modern_ui()

# --- 3. DATA ARCHITECTURE ---
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

# --- 4. SYSTEM INITIALIZATION ---
def init_system():
    for d in [IMG_DIR, BACKUP_DIR]:
        if not os.path.exists(d): os.makedirs(d)
    
    for key, path in FILES.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=HEADERS[key]).to_csv(path, index=False)
        else:
            df = pd.read_csv(path)
            missing = [c for c in HEADERS[key] if c not in df.columns]
            if missing:
                for col in missing:
                    df[col] = 0.0 if col in ["Price", "Total", "Cost", "Profit", "Qty", "Stock", "Cost Price", "Selling Price"] else ("" if col != "Min_Stock" else 2.0)
                df.to_csv(path, index=False)
    
    u_df = pd.read_csv(FILES["users"])
    if u_df.empty:
        pd.DataFrame([{"username": "ADMIN", "password": MASTER_PASS, "role": "OWNER"}]).to_csv(FILES["users"], index=False)

init_system()

# --- 5. RECEIPT DESIGN ---
def get_receipt_html(row):
    return f"""
    <div style="border:1px solid #30363d; padding:20px; width:300px; font-family:sans-serif; margin:auto; background:#ffffff; color:#000000; border-radius:10px;">
        <h2 style="text-align:center; margin-bottom:5px;">{COMPANY_NAME}</h2>
        <p style="text-align:center; font-size:12px; color:#666;">{COMPANY_PHONE}</p>
        <hr>
        <div style="font-size:12px;">
            <p><b>REF:</b> {row['Timestamp'].replace(' ', '')}<br><b>STAFF:</b> {row['Staff']}</p>
            <p><b>ITEM:</b> {row['Item']}<br><b>S/N:</b> {row['IMEI_Serial']}</p>
        </div>
        <hr>
        <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:16px;">
            <span>TOTAL</span>
            <span>GHS {row['Total']:.2f}</span>
        </div>
        <hr>
        <p style="text-align:center; font-size:10px;">Modern Solutions for Modern Devices.</p>
        <button onclick="window.print()" style="width:100%; background:#000; color:#fff; border:none; padding:10px; border-radius:5px; cursor:pointer;">PRINT RECEIPT</button>
    </div>
    """

# --- 6. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"<h1 style='text-align:center;'>{COMPANY_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;'>Enterprise Resource Planning</p>", unsafe_allow_html=True)
        with st.form("login_modern"):
            u = st.text_input("Username").upper().strip()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("UNLOCK SYSTEM", use_container_width=True):
                udb = pd.read_csv(FILES["users"])
                match = udb[(udb['username'] == u) & (udb['password'].astype(str) == p)]
                if not match.empty:
                    st.session_state.auth, st.session_state.user, st.session_state.role = True, u, match.iloc[0]['role']
                    st.rerun()
                else: st.error("Access Credentials Incorrect")
    st.stop()

# --- 7. REFRESH DATA ---
sales_df = pd.read_csv(FILES["sales"])
stock_df = pd.read_csv(FILES["inventory"])
users_df = pd.read_csv(FILES["users"])

# --- 8. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user}")
    st.markdown(f"**Level:** `{st.session_state.role}`")
    st.divider()
    nav = ["📊 Insights", "🛒 Sales POS", "🛠️ Repairs", "📦 Inventory", "⚙️ Admin"]
    if st.session_state.role != "OWNER": nav.remove("⚙️ Admin")
    choice = st.radio("MAIN MENU", nav)
    st.divider()
    if st.button("🚪 LOG OUT", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

# --- 9. MODULES ---

if choice == "📊 Insights":
    st.title("📊 Business Intelligence")
    low_stock = stock_df[stock_df['Stock'] <= stock_df['Min_Stock']]
    if not low_stock.empty: st.warning(f"Restock Required: {len(low_stock)} items are low.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Assets", f"GHS {(stock_df['Stock'] * stock_df['Cost Price']).sum():,.2f}")
    if st.session_state.role == "OWNER":
        col2.metric("Total Revenue", f"GHS {sales_df['Total'].sum():,.2f}")
        col3.metric("Net Profit", f"GHS {sales_df['Profit'].sum():,.2f}", delta_color="normal")
    
    st.subheader("Recent Activity Stream")
    st.dataframe(sales_df.tail(15).iloc[::-1], use_container_width=True)

elif choice == "🛒 Sales POS":
    st.title("🛒 Sales Terminal")
    with st.container(border=True):
        with st.form("pos_sale", clear_on_submit=True):
            L, R = st.columns([2, 1])
            with L:
                cn, cp = st.text_input("Customer Name"), st.text_input("Phone Number")
                items = stock_df[stock_df['Stock'] > 0]['Product Name'].tolist()
                item = st.selectbox("Product Selection", items if items else ["NO STOCK"])
                q, p = st.number_input("Qty", 1), st.number_input("Sale Price", 0.0)
                sn, note = st.text_input("IMEI / Serial Number"), st.text_input("Additional Notes")
            with R:
                if item != "NO STOCK":
                    img_row = stock_df[stock_df['Product Name'] == item]
                    st.write(f"In Stock: {img_row['Stock'].values[0]}")
                    path = img_row['Image_Path'].values[0]
                    if pd.notnull(path) and os.path.exists(str(path)): st.image(str(path), use_column_width=True)

            if st.form_submit_button("PROCESS TRANSACTION", use_container_width=True):
                cost = float(stock_df[stock_df['Product Name'] == item]['Cost Price'].iloc[0])
                total = q * p
                new_row = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "PRODUCT", "Item": item,
                    "Qty": q, "Price": p, "Total": total, "Cost": cost*q, "Profit": total-(cost*q),
                    "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": sn,
                    "Device_Fault": "", "Parts_Needed": "", "Status": "Sold", "Notes": note
                }
                pd.concat([sales_df, pd.DataFrame([new_row])], ignore_index=True).to_csv(FILES["sales"], index=False)
                stock_df.loc[stock_df['Product Name'] == item, 'Stock'] -= q
                stock_df.to_csv(FILES["inventory"], index=False)
                st.balloons()
                st.rerun()

elif choice == "🛠️ Repairs":
    st.title("🛠️ Repair Intake")
    with st.container(border=True):
        with st.form("rep_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                cn, cp = st.text_input("Customer Name"), st.text_input("Customer Phone")
                dev, imei = st.text_input("Device Model"), st.text_input("IMEI/Serial")
            with c2:
                fault, parts = st.text_area("Fault Reported"), st.text_area("Parts Required")
                fee = st.number_input("Service Fee (GHS)", 0.0)
            if st.form_submit_button("LOG REPAIR JOB", use_container_width=True):
                new_job = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Type": "SERVICE", "Item": dev,
                    "Qty": 1, "Price": fee, "Total": fee, "Cost": 0.0, "Profit": fee,
                    "Staff": st.session_state.user, "Cust_Name": cn, "Cust_Phone": cp, "IMEI_Serial": imei,
                    "Device_Fault": fault, "Parts_Needed": parts, "Status": "Repairing", "Notes": ""
                }
                pd.concat([sales_df, pd.DataFrame([new_job])], ignore_index=True).to_csv(FILES["sales"], index=False)
                st.success("Job Registered Successfully")
                st.rerun()

elif choice == "📦 Inventory":
    st.title("📦 Stock Control")
    t1, t2 = st.tabs(["Warehouse View", "Register New Product"])
    with t1:
        st.dataframe(stock_df, use_container_width=True, column_config={"Image_Path": st.column_config.ImageColumn("Preview")})
    with t2:
        with st.form("inv_form"):
            n, b, cp, sp, s = st.text_input("Item Name"), st.text_input("Brand"), st.number_input("Cost"), st.number_input("Sell"), st.number_input("Stock")
            up = st.file_uploader("Upload Image", type=['jpg','png'])
            if st.form_submit_button("SAVE TO INVENTORY"):
                p = os.path.join(IMG_DIR, f"{n.replace(' ','_')}.png") if up else ""
                if up: Image.open(up).save(p)
                pd.concat([stock_df, pd.DataFrame([{"Product Name": n, "Brand": b, "Cost Price": cp, "Selling Price": sp, "Stock": s, "Min_Stock": 2, "Image_Path": p}])], ignore_index=True).to_csv(FILES["inventory"], index=False)
                st.rerun()

elif choice == "⚙️ Admin":
    st.title("⚙️ Control Panel")
    tab_ord, tab_usr, tab_sys = st.tabs(["📋 Orders", "👥 Staff", "🛡️ Database"])
    
    with tab_ord:
        q = st.text_input("Filter Orders (Name/IMEI)").lower()
        f_df = sales_df[sales_df.apply(lambda r: q in r.astype(str).str.lower().values, axis=1)] if q else sales_df.tail(10)
        if not f_df.empty:
            sel = st.selectbox("Select Transaction", f_df.index, format_func=lambda x: f"ID: {x} | {sales_df.at[x, 'Item']} | {sales_df.at[x, 'Cust_Name']}")
            r = sales_df.loc[sel]
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📄 RECEIPT"): st.markdown(get_receipt_html(r), unsafe_allow_html=True)
            with col2:
                msg = f"LOG MASTER: Hello {r['Cust_Name']}, your {r['Item']} is {r['Status']}."
                url = f"https://wa.me/{r['Cust_Phone']}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:10px; border-radius:8px; width:100%;">NOTIFY WHATSAPP</button></a>', unsafe_allow_html=True)
            with col3:
                if st.button("🗑️ DELETE"):
                    sales_df.drop(sel).to_csv(FILES["sales"], index=False)
                    st.rerun()
            
            with st.form("status_up"):
                ns = st.selectbox("Update Status", ["Repairing", "Ready", "Collected", "Sold", "Cancelled"])
                if st.form_submit_button("SAVE UPDATE"):
                    sales_df.at[sel, 'Status'] = ns
                    sales_df.to_csv(FILES["sales"], index=False)
                    st.rerun()

    with tab_usr:
        st.table(users_df[['username', 'role']])
        with st.form("new_u"):
            nu, np, nr = st.text_input("Username").upper(), st.text_input("Password"), st.selectbox("Role", ["STAFF", "OWNER"])
            if st.form_submit_button("ADD USER"):
                pd.concat([users_df, pd.DataFrame([{"username": nu, "password": np, "role": nr}])], ignore_index=True).to_csv(FILES["users"], index=False)
                st.rerun()

    with tab_sys:
        if st.button("🚀 EXECUTE FULL BACKUP"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            for k, p in FILES.items(): shutil.copy(p, os.path.join(BACKUP_DIR, f"BACKUP_{ts}_{p}"))
            st.success("System Snapshot Created")