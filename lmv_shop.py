import streamlit as st
import pandas as pd
import os

# --- 1. BRAND IDENTITY ---
COMPANY_NAME = "LOG MASTER VENTURES"
WHATSAPP_BUS = "233545531632"

# --- 2. DATA LOAD (Synced with ERP) ---
def get_inventory():
    path = "lmv_stock.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=["Product Name", "Selling Price", "Stock", "Image_URL", "Description"])

inventory = get_inventory()

# --- 3. WEBSITE LAYOUT ---
st.set_page_config(page_title=f"{COMPANY_NAME} | Gadgets & Repairs", layout="wide")

# Custom CSS for a "Premium" look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; }
    .product-card { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. NAVIGATION ---
st.title(f"🏬 Welcome to {COMPANY_NAME}")
st.subheader("High-Quality Gadgets & Expert Repairs in Ghana")

tab1, tab2, tab3 = st.tabs(["🛒 Shop Gadgets", "🔧 Book a Repair", "📞 Contact Us"])

# --- 5. SHOPPING TAB ---
with tab1:
    st.write("### Featured Products")
    if inventory.empty:
        st.info("We are currently restocking. Check back soon!")
    else:
        # Create a grid of 3 columns
        cols = st.columns(3)
        for index, row in inventory.iterrows():
            with cols[index % 3]:
                st.markdown(f"""
                <div class="product-card">
                    <h4>{row['Product Name']}</h4>
                    <p style="color: green; font-weight: bold; font-size: 20px;">GHS {row['Selling Price']:,.2f}</p>
                    <p style="font-size: 12px; color: grey;">Status: {'In Stock' if row['Stock'] > 0 else 'Out of Stock'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # WhatsApp Buy Link
                msg = f"Hello {COMPANY_NAME}, I'm interested in buying the {row['Product Name']}."
                wa_link = f"https://wa.me/{WHATSAPP_BUS}?text={urllib.parse.quote(msg)}"
                st.link_button(f"Order on WhatsApp", wa_link)

# --- 6. REPAIR BOOKING ---
with tab2:
    st.write("### 🔧 Professional Repair Service")
    st.write("Screen broken? Battery failing? We can fix it!")
    
    with st.form("repair_request"):
        name = st.text_input("Your Name")
        phone = st.text_input("Phone Number")
        device = st.text_input("Device Model (e.g. iPhone 12 Pro)")
        issue = st.selectbox("What's the problem?", ["Broken Screen", "Charging Port", "Battery Issues", "Software/Unlocking", "Other"])
        
        if st.form_submit_button("Request Repair Quote"):
            # This sends a message to your WhatsApp immediately
            msg = f"REPAIR REQUEST\nName: {name}\nDevice: {device}\nIssue: {issue}\nPhone: {phone}"
            wa_link = f"https://wa.me/{WHATSAPP_BUS}?text={urllib.parse.quote(msg)}"
            st.success("Redirecting you to our technician on WhatsApp...")
            st.markdown(f'<meta http-equiv="refresh" content="0;url={wa_link}">', unsafe_allow_html=True)

# --- 7. CONTACT TAB ---
with tab3:
    st.write("### 📍 Location & Hours")
    st.write("**Visit our shop:** Accra, Ghana")
    st.write("**Hours:** Monday - Saturday (8:00 AM - 6:00 PM)")
    st.write(f"**Email:** logmastergh@gmail.com")