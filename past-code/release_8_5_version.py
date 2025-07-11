import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

# 설정
# url = "https://docs.genesys.com/Documentation/RN/9.0.x/gvp-mcp90rn/gvp-mcp90rn"
# spreadsheet_name = "Genesys Engage Release Notes"  # 스프레드시트 제목
# worksheet_name = "gvp-mcp90rn"              # 워크시트 이름
credentials_path = "credentials.json"  # 구글 API 키 JSON 경로

def load_targets(json_path="targets.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_release_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")[1:]

    release_data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        a_tag = cells[0].find("a")
        if a_tag:
            version = a_tag.get_text(strip=True)
            link = a_tag.get("href")
        else:
            continue

        raw_date = cells[1].get_text(strip=True)
        try:
            v_mm, v_dd, v_yy = raw_date.strip().split('/')
            release_date = f"20{v_yy}-{v_mm}-{v_dd}"
            release_data.append((version, release_date, link))
        except ValueError:
            continue

    return release_data

def write_to_google_sheet(data, worksheet_name, client, spreadsheet_name="Genesys Engage Release Notes"):
    sheet = client.open(spreadsheet_name).worksheet(worksheet_name)
    existing = sheet.get_all_values()

    if not existing:
        existing_versions = set()
    else:
        existing_versions = set(row[0] for row in existing if row)

    new_rows = [list(row) for row in data if row[0] not in existing_versions]

    # 전체 데이터 = 새 항목 + 기존 항목 중복 제외
    combined = new_rows + [row for row in existing if row[0] not in set(r[0] for r in new_rows)]

    # 날짜 기준 내림차순 정렬
    def parse_date(date_str):
        return datetime.strptime(date_str, "%Y-%m-%d")

    try:
        sorted_combined = sorted(combined, key=lambda x: parse_date(x[1]), reverse=True)
    except Exception as e:
        print(f"⚠️ 날짜 파싱 중 오류 발생: {e}")
        sorted_combined = combined  # 실패 시 그대로 유지

    # 기존 데이터와 동일하면 → 변경 없음으로 판단
    if existing == sorted_combined:
        print(f"✅ {worksheet_name}: 추가할 새 항목 없음 + 정렬도 동일함.")
    else:
        sheet.clear()
        sheet.update(range_name="A1", values=sorted_combined)
        print(f"✅ {worksheet_name}: {len(new_rows)}개 항목 추가됨 또는 정렬 업데이트됨.")


def main():
    targets = load_targets()

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    for target in targets:
        print(f"🔍 {target['name']} 처리 중...")
        try:
            data = fetch_release_data(target["url"])
            write_to_google_sheet(data, target["worksheet"], client)
        except Exception as e:
            print(f"❌ {target['name']} 실패: {e}")


if __name__ == "__main__":
    main()
