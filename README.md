# Genesys Engage Release Note 자동화 스크립트

Genesys Engage 제품 릴리즈 노트를 크롤링하여 Google Sheet에 자동으로 정리하고, 최신 버전을 요약하는 Python 스크립트입니다.

---

## 📦 설치 방법

### 1. Python 환경 준비

```bash
python -m venv venv
source venv/bin/activate  # 윈도우는 venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Google Cloud API 설정

Google Sheets API와 Google Drive API를 사용합니다.

▶ 서비스 계정 키 발급하기
Google Cloud Console 접속

프로젝트 생성 또는 선택 (예: genesys-engage-release-notes)

"API 및 서비스" → "사용자 인증 정보" → "사용자 인증 정보 만들기" → "서비스 계정"

서비스 계정 생성 후 키 추가 → JSON 형식으로 다운로드

해당 파일을 credentials.json으로 프로젝트 루트에 저장 (절대 Git에 올리지 마세요)

▶ 스프레드시트 접근 권한 부여
생성한 서비스 계정 이메일 주소 (예: your-service-account@your-project.iam.gserviceaccount.com)를

Google 스프레드시트의 공유 대상에 추가 (편집 권한)

### ⚙️ 실행 방법

```bash
python unified_release_updater.py
```

```bash
.
├── credentials.sample.json     # 서비스 계정 키 샘플
├── unified_release_updater.py  # 메인 실행 파일
├── 81_targets.json             # 8.1.x 대상 URL 목록
├── targets.json                # 8.5.x 이상 대상 URL 목록
├── requirements.txt            # 필요한 Python 라이브러리
└── README.md                   # 사용 설명서
```

❗ 주의사항
credentials.json은 .gitignore로 Git에 절대 올리지 마세요.

실제 민감 정보는 .sample 파일을 복사해서 각자 설정해야 합니다.
