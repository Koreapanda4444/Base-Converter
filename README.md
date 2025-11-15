# Base Converter

다양한 진법 변환을 지원하는 파이썬 애플리케이션입니다. 직관적인 그래픽 인터페이스(GUI)와 강력한 명령줄 인터페이스(CLI)를 모두 제공합니다.

![image](https://user-images.githubusercontent.com/42678534/188339192-13949311-04e3-4b92-8080-872f00608560.png)

## ✨ 주요 기능

### 공통
- **2진법 ~ 36진법** 변환 지원
- 정수, 실수 및 간단한 사칙연산(`+`, `-`, `*`, `/`) 표현식 변환
- 다양한 반올림 모드 및 정밀도 설정

### GUI (Graphical User Interface)
- 실시간 변환 및 변환 과정 표시
- 모든 변환 기록을 자동으로 저장하는 **히스토리** 기능
- 히스토리 검색 및 정렬 (시간순, 입력값순)
- 사용자가 설정한 정밀도, 반올림 모드 자동 저장
- 다크/라이트 모드 자동 지원

### CLI (Command-Line Interface)
- 단일 표현식 변환
- CSV 파일을 이용한 **배치(일괄) 변환**
- 결과 포맷팅 옵션 (소문자, 4자리 그룹핑, `0b`/`0x` 접두사 등)

## ⚙️ 설치 및 요구사항

1.  **Python 3.7 이상**이 설치되어 있어야 합니다.
2.  필요한 라이브러리를 설치합니다.

    ```shell
    pip install customtkinter
    ```

## 🚀 실행 방법

### GUI 실행
터미널에서 다음 명령어를 실행하세요.
```shell
python -m gui.main
```

### CLI 실행
터미널에서 다음 명령어를 실행하여 상세한 도움말을 볼 수 있습니다.
```shell
python -m cli.main --guide
```

**CLI 사용 예시:**
```shell
# 16진수 'FF'를 10진수로 변환
python -m cli.main --from 16 --to 10 "FF"

# 10진수 '3.14'를 2진수로 변환 (정밀도 16자리)
python -m cli.main --from 10 --to 2 --precision 16 "3.14"

# CSV 파일 일괄 변환
python -m cli.main --batch --input "input.csv" --output "result.csv"
```

## 📁 프로젝트 구조

```
Base-Converter/
├── cli/              # CLI 관련 코드
│   └── main.py
├── converter/        # 핵심 변환 로직
│   └── logic.py
├── gui/              # GUI 관련 코드
│   ├── main.py
│   ├── ui.py
│   └── config_manager.py
└── history/          # 히스토리 저장 및 관리
    └── store.py
```