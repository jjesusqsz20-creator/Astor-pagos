import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Setup connection
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
client = gspread.authorize(creds)
spreadsheet = client.open("Astor_Pagos_DB")

# Get worksheets
for ws in spreadsheet.worksheets():
    print(f"Sheet: {ws.title}")
    data = ws.get_all_values()
    if data:
        print(f"  Headers: {data[0]}")
        for i, row in enumerate(data[1:10]):
            print(f"  Row {i+1}: {row}")
