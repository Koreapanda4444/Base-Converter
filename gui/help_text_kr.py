# gui/help_text_kr.py
HELP_TEXT = """📘 Base-Converter 사용 가이드 (GUI)

[개요]
- 진법 변환 및 연산기 (CLI + GUI)
- 혼합 진법 입력, 변수/상수, 정밀도/반올림, 유효자리수/과학표기, 히스토리, CSV/JSON, 테마, 포터블 모드 지원

[입력 형식]
- 단일 값: 1011, A.F, 123.45
- 혼합 진법: 0b1010, 0o77, 0xFF, (A.F)_16, 1011_2
- 연산: +, -, *, /, %, ^, 괄호 ()
- 변수 할당: A=0xFF, PI=3.14159  (할당 후 식에서 사용 가능)

[진법 선택]
- ‘입력진법’, ‘출력진법’ 콤보박스로 2~36 선택
- 혼합 표기 사용 시 기본 입력진법은 혼합 숫자에 우선하지 않음

[정밀도/반올림]
- 정밀도: 소숫점 이하 계산·표시에 적용
- 반올림: HALF_UP, HALF_DOWN, HALF_EVEN, CEILING, FLOOR

[유효자리수/과학표기]
- 유효자리수(sig): 전체 유효자릿수 제한
- 과학표기(sci): 10진 출력 시 지수표기(e±n) 사용

[결과]
- ‘결과’에 변환 결과 표시
- ‘복사’ 버튼으로 클립보드 복사

[히스토리]
- 변환/연산 실행 시 자동 저장
- 열 헤더: 입력 | 진법 | 결과 | ★ | 태그
- 더블클릭: 해당 기록 재적용
- ★ 토글: 즐겨찾기
- #태그 추가: 쉼표로 다중 태그 가능
- CSV 내보내기/가져오기
- JSON 백업/복원

[실시간 입력 검증]
- 입력창 아래 오류 메시지로 즉시 피드백(자리수/토큰화 등)

[테마]
- 글자색/배경색/버튼색/호버색 변경
- theme.json 저장

[포터블 모드]
- 실행 폴더에 portable.flag가 있으면 설정/테마/변수/히스토리를 실행 폴더 하위 data/에 저장

[단축키]
- Enter: 변환
- Esc: 초기화
- Ctrl+C: 결과 복사
- Ctrl+F: 히스토리 포커스
- F1: 이 도움말

[예시]
- 0b1011 + (A.F)_16
- A=0xFF, A + 1
- (1011_2 ^ 2) % 0xF
"""

CLI_TEXT = """💻 CLI 사용 가이드

[기본]
python cli/main.py --from 10 --to 2 "255"
python cli/main.py --from 2 --to 16 "1011 + 1101"

[옵션]
--from, --to           입력/출력 진법(2~36)
--precision            정밀도(기본 12)
--round                반올림(HALF_UP|HALF_DOWN|HALF_EVEN|CEILING|FLOOR)
--lower                출력 소문자
--group4               정수부 4자리 그룹
--underscore           그룹 구분자로 '_' 사용
--prefix               접두사(0b/0o/0x) 출력
--sci                  10진 과학표기 사용
--sig N                유효자리수 N 적용
--batch                배치 변환 모드
--input PATH           배치 입력 CSV
--output PATH          배치 출력 CSV
--guide                이 확장 도움말 출력 후 종료

[혼합 진법 입력]
- 0b/0o/0x, (..)_base, .._base 표기 혼용 가능
예) "0b1010 + (FF)_16 - 123_10"

[배치 CSV 예]
expr,base_from,base_to
0b1010+1,2,10
(FF)_16,10,2

[예시]
python cli/main.py --from 16 --to 2 "FF + 1"
python cli/main.py --precision 20 --round HALF_EVEN --from 10 --to 16 "3.14159"
python cli/main.py --batch --input in.csv --output out.csv
"""
