# 명령줄 사용법

[한국어 README](../../README.ko.md) | [English](../cli.md)

`python -m pip install .`로 설치한 뒤 `radixscope` 또는 `python -m radixscope`를
실행합니다. 각 하위 명령에서 `--help`로 도움말을 보고 `--json`으로 JSON 결과를 받을 수 있습니다.

```sh
radixscope convert FF --from 16 --to 2 8 10 16
radixscope convert "0.(3)" --to 2 10 --precision 8 --rounding half-even
radixscope expression "0x10 + 2#11 / 10#2" --to 2 10 16
radixscope trace "1/3" --from 10 --to 2 --json
radixscope integer -128 --width 8 --signed --op shr --operand 1
radixscope integer 127 --width 8 --signed --op add --operand 1 --json
radixscope integer FF --base 16 --width 8 --signed --pattern
radixscope ieee decode 3F800000 --width 32
radixscope ieee encode "1/10" --width 32 --json
radixscope ieee encode nan --width 64 --payload 123 --signaling
radixscope ieee encode 0 --negative-zero --width 32
```

## 진법 변환과 수식

`convert`의 기본 입력 진법은 10이며, 기본 출력 진법은 2, 8, 10, 16입니다.
정확한 출력은 순환하는 숫자를 괄호로 묶습니다. `--precision`은 소수부 자릿수를
지정하고 `--rounding`은 다음 방식을 선택합니다.

| 옵션 | 처리 방식 |
| --- | --- |
| `truncate` | 남은 소수부를 버려 0 방향으로 자름 |
| `half-up` | 가장 가까운 값으로 반올림하며, 동률이면 0에서 먼 쪽 선택 |
| `half-even` | 가장 가까운 값으로 반올림하며, 동률이면 짝수 선택 |
| `floor` | 음의 무한대 방향으로 내림 |
| `ceiling` | 양의 무한대 방향으로 올림 |

`expression`은 서로 다른 진법을 섞은 수식을 계산합니다. 예를 들어 `0x10`은
16진수 10, `2#11`은 2진수 11입니다. 접두사가 없는 숫자는 10진수로 읽습니다.
`trace`는 나눗셈·곱셈 단계와 순환 구간의 시작 위치를 보여줍니다.

## 정수와 비트 연산

`integer`는 기본적으로 입력을 수학적 정수로 읽습니다. `--pattern`을 지정하면
원시 비트 패턴으로 해석합니다. 부호 있는 정수는 2의 보수를 사용합니다.
산술 결과는 정확한 값, 오버플로 여부, 선택한 비트 폭에 맞춰 감싼 값을 각각 보여줍니다.

비트 연산의 두 피연산자는 같은 진법·비트 폭·부호 설정을 사용합니다.
시프트 횟수는 10진수입니다. 엔디언 설정은 바이트 미리보기 순서에 적용됩니다.

## IEEE 754

`ieee encode`는 정확한 혼합 진법 수식과 선택적 부호가 붙은 `nan`, `inf`,
`infinity`를 받습니다. `ieee decode`는 기본적으로 16진수 원시 패턴을 읽습니다.
NaN 페이로드와 시그널링 옵션은 NaN 인코딩에만 적용합니다. 원시 디코딩은
Python `float`로 변환하지 않고 페이로드를 보존합니다.

## 종료 코드와 음수 입력

성공하면 종료 코드 0을 반환합니다. 잘못된 인자나 숫자는 종료 코드 2를 반환하고,
표준 오류에 짧은 메시지를 출력하며 표준 출력은 비워 둡니다.
`-FF`, `-inf`처럼 옵션으로 오인될 수 있는 음수는 `--` 뒤에 둡니다.
모든 명령 옵션은 이 구분자 앞에 적어야 합니다.

```sh
radixscope ieee encode --width 32 -- -inf
```
