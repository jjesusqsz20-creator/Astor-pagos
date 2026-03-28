import toml
import gspread
from google.oauth2.service_account import Credentials

def debug_sheets():
    try:
        s = toml.load('.streamlit/secrets.toml')
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(s['gcp_service_account'], scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open('Astor_Pagos_DB')
        
        for w in spreadsheet.worksheets():
            print(f"--- Sheet: {w.title} ---")
            values = w.get_all_values()
            if not values:
                print("EMPTY")
                continue
            print(f"Headers: {values[0]}")
            if len(values) > 1:
                print(f"Row 1: {values[1]}")
            if len(values) > 2:
                print(f"Row 2: {values[2]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_sheets()
