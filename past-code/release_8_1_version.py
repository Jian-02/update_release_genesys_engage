import requests
from bs4 import BeautifulSoup
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

spreadsheet_name = "Genesys Engage Release Notes"
credentials_path = "credentials.json"
json_targets_path = "81_targets.json"

def load_targets(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_versions_from_os_table(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table", class_="os-table")
    if not table:
        print("❌ .os-table 테이블을 찾을 수 없습니다.")
        return []

    results = []
    for a_tag in table.find_all("a"):
        text = a_tag.get_text(strip=True)
        if "[" in text and "]" in text:
            try:
                version = text.split("[")[0].strip()
                raw_date = text.split("[")[1].split("]")[0].strip()
                mm, dd, yy = raw_date.split("/")
                formatted_date = f"20{yy}-{mm}-{dd}"
                results.append((version, formatted_date))
            except Exception as e:
                print(f"⚠️ 파싱 실패: {text} → {e}")
    return results

def fetch_versions_from_os_table_for_icon(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table", class_="os-table")
    if not table:
        print("❌ .os-table 테이블을 찾을 수 없습니다.")
        return []

    results = []
    for a_tag in table.find_all("a"):
        text = a_tag.get_text(strip=True)
        if "[" in text and "]" in text:
            try:
                version = text.split("[")[0].strip()
                raw_date = text.split("[")[1].split("]")[0].strip()
                mm, dd, yy = raw_date.split("/")
                formatted_date = f"{yy}-{mm}-{dd}"
                results.append((version, formatted_date))
            except Exception as e:
                print(f"⚠️ 파싱 실패: {text} → {e}")
    return results

def write_to_google_sheet(data, worksheet_name, client):
    sheet = client.open(spreadsheet_name).worksheet(worksheet_name)
    existing = sheet.get_all_values()
    existing_versions = set(row[0] for row in existing if row)

    # 신규 항목만 추출
    new_rows = [list(row) for row in data if row[0] not in existing_versions]

    # 전체 데이터 = 신규 항목 + 기존 항목 중 중복 제거
    combined = new_rows + [row for row in existing if row[0] not in set(r[0] for r in new_rows)]

    # 날짜 형식에 따라 유연하게 파싱
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

    # 기존과 다를 경우에만 업데이트
    if existing != sorted_combined:
        sheet.clear()
        sheet.update(range_name="A1", values=sorted_combined)
        print(f"✅ {worksheet_name}: {len(new_rows)}개 항목 추가 또는 정렬됨.")
    else:
        print(f"✅ {worksheet_name}: 추가할 항목도 없고 정렬도 동일.")


def main():
    targets = load_targets(json_targets_path)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    print("test")
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)

    for target in targets:
        print(f"🔍 {target['name']} 처리 중...")
        try:
            if target["worksheet"] == "ICON":
                data = fetch_versions_from_os_table_for_icon(target["url"])
            else:
                data = fetch_versions_from_os_table(target["url"])
            write_to_google_sheet(data, target["worksheet"], client)
        except Exception as e:
            print(f"❌ {target['name']} 실패: {e}")

if __name__ == "__main__":
    main()
