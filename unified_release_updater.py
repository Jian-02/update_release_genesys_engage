import requests
from bs4 import BeautifulSoup
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from gspread_formatting import *

# 공통 설정
SPREADSHEET_NAME = "Genesys Engage Release Notes"
CREDENTIALS_PATH = "credentials.json"
TARGETS_81_PATH = "81_targets.json"
TARGETS_85_PATH = "85_targets.json"
SUMMARY_SHEET_NAME = "Summary"

def init_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
    return gspread.authorize(creds)

def load_targets(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 8.1.x 방식 파서
def fetch_81_versions(url, for_icon=False):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find("table", class_="os-table")
    if not table:
        print(f"❌ 테이블 없음: {url}")
        return []

    results = []
    for a_tag in table.find_all("a"):
        text = a_tag.get_text(strip=True)
        if "[" in text and "]" in text:
            try:
                version = text.split("[")[0].strip()
                raw_date = text.split("[")[1].split("]")[0].strip()
                mm, dd, yy = raw_date.split("/")
                formatted_date = f"{'20' if len(yy) == 2 else ''}{yy}-{mm}-{dd}" if not for_icon else f"{yy}-{mm}-{dd}"
                results.append((version, formatted_date))
            except Exception as e:
                print(f"⚠️ 파싱 실패: {text} → {e}")
    return results

# 8.5 이상 방식 파서
def fetch_85_versions(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    if not table:
        print(f"❌ 테이블 없음: {url}")
        return []

    rows = table.find_all("tr")[1:]
    release_data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        a_tag = cells[0].find("a")
        if not a_tag:
            continue
        version = a_tag.get_text(strip=True)
        raw_date = cells[1].get_text(strip=True)
        try:
            mm, dd, yy = raw_date.split("/")
            release_date = f"20{yy}-{mm}-{dd}"
            release_data.append((version, release_date, a_tag.get("href")))
        except ValueError:
            continue
    return release_data

# 공통 정렬 및 쓰기
def write_to_google_sheet(data, worksheet_name, client):
    sheet = client.open(SPREADSHEET_NAME).worksheet(worksheet_name)
    existing = sheet.get_all_values()
    existing_versions = set(row[0] for row in existing if row)

    new_rows = [list(row) for row in data if row[0] not in existing_versions]
    combined = new_rows + [row for row in existing if row[0] not in set(r[0] for r in new_rows)]

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return datetime.strptime(date_str, "%y-%m-%d")

    try:
        sorted_combined = sorted(combined, key=lambda x: parse_date(x[1]), reverse=True)
    except Exception as e:
        print(f"⚠️ 날짜 파싱 오류: {e}")
        sorted_combined = combined

    if existing != sorted_combined:
        sheet.clear()
        sheet.update("A1", sorted_combined)
        print(f"✅ {worksheet_name}: {len(new_rows)}개 항목 추가 또는 정렬됨.")
    else:
        print(f"✅ {worksheet_name}: 변경 없음.")

# 요약 탭 정리
def gather_summary_data(client):
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheets = spreadsheet.worksheets()

    today = datetime.today().strftime("%Y-%m-%d")
    summary = []

    for ws in worksheets:
        if ws.title == SUMMARY_SHEET_NAME:
            continue
        try:
            first_row = ws.row_values(1)
            if len(first_row) >= 2:
                version = first_row[0]
                date = first_row[1]
                updated_today = "✅" if date == today else ""
                summary.append([ws.title, version, date, updated_today])
        except Exception as e:
            print(f"⚠️ {ws.title} 읽기 실패: {e}")

    summary.sort(key=lambda x: x[2], reverse=True)
    return [["Component", "Version", "Date", "Updated Today?"]] + summary

def write_summary_sheet(client, summary_data):
    spreadsheet = client.open(SPREADSHEET_NAME)
    try:
        sheet = spreadsheet.worksheet(SUMMARY_SHEET_NAME)
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=SUMMARY_SHEET_NAME, rows="100", cols="10")
    sheet.append_rows(summary_data, value_input_option="RAW")

    # 강조
    today = datetime.today().strftime("%Y-%m-%d")
    fmt = cellFormat(backgroundColor=color(1, 1, 0.6))
    for i, row in enumerate(summary_data[1:], start=2):
        if row[2] == today:
            format_cell_range(sheet, f"A{i}:D{i}", fmt)

def main():
    client = init_client()

    # 8.1.x 처리
    for target in load_targets(TARGETS_81_PATH):
        print(f"🔍[8.1] {target['name']}")
        try:
            data = fetch_81_versions(target["url"], for_icon=(target["worksheet"] == "ICON"))
            write_to_google_sheet(data, target["worksheet"], client)
        except Exception as e:
            print(f"❌ {target['name']} 실패: {e}")

    # 8.5.x 이상 처리
    for target in load_targets(TARGETS_85_PATH):
        print(f"🔍[8.5+] {target['name']}")
        try:
            data = fetch_85_versions(target["url"])
            write_to_google_sheet(data, target["worksheet"], client)
        except Exception as e:
            print(f"❌ {target['name']} 실패: {e}")

    # 요약 시트 작성
    print("🧾 요약 탭 업데이트 중...")
    summary_data = gather_summary_data(client)
    write_summary_sheet(client, summary_data)
    print("✅ 요약 시트 업데이트 완료.")

if __name__ == "__main__":
    main()
