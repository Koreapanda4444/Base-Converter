Base Converter

다양한 진법 변환을 지원하는 Python 기반 애플리케이션입니다.
GUI와 CLI 모두 제공하며, 실수·표현식·혼합 진법까지 변환할 수 있습니다.

⭐ 특징
🔹 공통 기능

2진수 ~ 36진수 변환

정수, 실수, 분수(Fraction) 모두 처리

0b, 0x, (FF)_16 같은 혼합 진법 자동 인식

기본 사칙연산·괄호·변수(assign) 지원 (x = 10, x + 5)

다양한 반올림 모드 (HALF_UP, CEILING, …)

정밀도 지정 (precision)

변환 과정 출력

🖥 GUI (CustomTkinter)

입력 → 변환 과정 실시간 표시

변환 기록 자동 저장
(검색/정렬: 최신순, A→Z 등)

사용자 설정 자동 저장 (config.json)

시스템 테마 기반 다크/라이트 모드 지원

기록 더블클릭 → 자동 재입력

💻 CLI
python -m cli.main --from 10 --to 2 "3.14"


지원 옵션:

--from, --to : 변환 진법 설정

--precision : 정밀도

--round : 반올림 모드

--lower : 소문자 출력

--group4 : 4자리 그룹핑

--underscore : group separator _

--prefix : 0b/0o/0x 접두사

--sci : 과학적 표기법

--sig N : 유효숫자 제한

--batch : CSV 일괄 변환

예시:

python -m cli.main --batch --input input.csv --output result.csv

🔌 Portable 모드 지원

프로그램 폴더 안에 portable.flag 파일을 만들면
모든 데이터가 로컬 폴더의 data/ 아래에 저장됩니다.

Base-Converter/
 ├─ portable.flag
 └─ data/
      ├─ config.json
      ├─ history.json
      └─ vars.json


USB에서 들고 다니며 사용할 때 유용합니다.

📁 프로젝트 구조
Base-Converter/
├─ cli/
│   └─ main.py              # CLI 실행 진입점
│
├─ converter/
│   ├─ logic.py             # 진법 변환 및 수식 처리
│   ├─ utils.py             # 토큰화·숫자 판별·반올림 처리
│   └─ vars.py              # 변수 저장 시스템
│
├─ gui/
│   ├─ main.py              # GUI 실행 진입점
│   ├─ ui.py                # GUI 화면 구성
│   └─ config_manager.py    # GUI 설정 저장/불러오기
│
├─ history/
│   └─ store.py             # 변환 기록 저장/검색 기능
│
└─ data/                    # portable 모드에서 생성됨

🚀 설치 및 실행
1) 의존성
pip install customtkinter

2) GUI 실행
python -m gui.main

3) CLI 도움말
python -m cli.main --guide

🔍 예시
간단 변환
python -m cli.main --from 16 --to 10 "FF"

표현식 계산
python -m cli.main --from 10 --to 2 "3.5 + 1.25"

혼합 진법
0xA + (1011)_2 * 3
