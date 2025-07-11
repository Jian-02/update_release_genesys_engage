import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from gspread_formatting import *

# 설정
credentials_path = "credentials.json"
spreadsheet_name = "Genesys Engage Release Notes"
summary_sheet_name = "Summary"

def init_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    return gspread.authorize(creds)

def gather_latest_versions(client):
    spreadsheet = client.open(spreadsheet_name)
    worksheets = spreadsheet.worksheets()

    today = datetime.today().strftime("%Y-%m-%d")
    summary_data = []

    for ws in worksheets:
        if ws.title == summary_sheet_name:
            continue

        try:
            first_row = ws.row_values(1)
            if len(first_row) >= 2:
                version = first_row[0]
                date = first_row[1]
                updated_today = "✅" if date == today else ""
                summary_data.append({
                    "Component": ws.title,
                    "Version": version,
                    "Date": date,
                    "Today": updated_today
                })
        except Exception as e:
            print(f"⚠️ {ws.title} 읽기 실패: {e}")

    # 날짜 내림차순 정렬
    summary_data.sort(key=lambda x: x["Date"], reverse=True)
    return [["Component", "Version", "Date", "Updated Today?"]] + [
        [entry["Component"], entry["Version"], entry["Date"], entry["Today"]] for entry in summary_data
    ]

def write_summary_sheet(client, summary_data):
    spreadsheet = client.open(spreadsheet_name)

    try:
        summary_ws = spreadsheet.worksheet(summary_sheet_name)
        summary_ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        summary_ws = spreadsheet.add_worksheet(title=summary_sheet_name, rows="100", cols="10")

    summary_ws.append_rows(summary_data, value_input_option="RAW")

    # 강조 색상 적용
    today = datetime.today().strftime("%Y-%m-%d")
    fmt = cellFormat(backgroundColor=color(1, 1, 0.6))  # 연노랑
    for i, row in enumerate(summary_data[1:], start=2):
        if row[2] == today:
            format_cell_range(summary_ws, f"A{i}:D{i}", fmt)

def main():
    client = init_client()
    summary_data = gather_latest_versions(client)
    write_to_google_sheet = write_summary_sheet(client, summary_data)

if __name__ == "__main__":
    main()
