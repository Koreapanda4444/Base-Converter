# Base Converter

다양한 진법 변환을 지원하는 Python 기반 애플리케이션입니다.
GUI와 CLI 모두 제공하며, 실수·분수·표현식·혼합 진법까지 변환할 수 있습니다.

## ✨ 특징

### 🔹 공통 기능
- 2진법 ~ 36진법 변환
- 정수, 실수, Fraction 기반 정밀 계산
- 사칙연산, 괄호, 변수(assign) 지원  
  예: `x = 10`, `x + 5`
- 혼합 진법 자동 인식  
  - `0b1010`, `0xFF`, `0o77`  
  - `(FF)_16`, `A2.3B_12` 등
- 반올림 모드 지원 (HALF_UP, HALF_EVEN, HALF_DOWN, CEILING, FLOOR)
- 정밀도(precision) 설정 가능

## 🖥 GUI (CustomTkinter)
- 변환 과정 실시간 표시
- 변환 기록 자동 저장 (검색/정렬 지원)
- OS 테마에 따라 다크/라이트 모드 자동 적용
- 사용자 설정(config.json) 자동 저장
- 히스토리 더블클릭 → 입력값 자동 로드

## 💻 CLI

### 단일 변환 예시
```bash
python -m cli.main --from 16 --to 10 "FF"
python -m cli.main --from 10 --to 2 --precision 16 "3.14"
```

### 주요 옵션
- `--from`, `--to` : 진법 설정  
- `--precision` : 소수 정밀도  
- `--round` : 반올림 모드  
- `--lower` : 소문자 출력  
- `--group4` : 4자리 묶기  
- `--underscore` : `_` 구분자  
- `--prefix` : 0b, 0o, 0x 접두사  
- `--sci` : 과학적 표기법  
- `--sig N` : 유효숫자 제한  
- `--batch` : CSV 일괄 변환  
- `--guide` : CLI 가이드 출력  

### CSV 일괄 변환
```bash
python -m cli.main --batch --input input.csv --output result.csv
```

## 🔌 Portable 모드

프로그램 폴더에 `portable.flag` 파일을 생성하면  
설정·히스토리·변수 저장 파일이 프로그램 내부 `data/` 폴더로 저장됩니다.

```
Base-Converter/
 ├─ portable.flag
 └─ data/
      ├─ config.json
      ├─ history.json
      └─ vars.json
```

## 📁 프로젝트 구조

```
Base-Converter/
├─ cli/
│   └─ main.py
│
├─ converter/
│   ├─ logic.py
│   ├─ utils.py
│   └─ vars.py
│
├─ gui/
│   ├─ main.py
│   ├─ ui.py
│   └─ config_manager.py
│
├─ history/
│   └─ store.py
│
└─ data/              # portable 모드에서 생성됨
```

## 🚀 설치 및 실행

### 1) 의존성 설치
```bash
pip install customtkinter
```

### 2) GUI 실행
```bash
python -m gui.main
```

### 3) CLI 도움말
```bash
python -m cli.main --guide
```

## 🔍 변환 예시

### 표현식 계산
```
0xA + (1011)_2 * 3 - 1.5
```

### 변수 사용
```
x = 15
x * 2
```
