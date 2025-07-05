from constants import Base_name_to_num


def to_int(value: str, base_name: str) -> int:

    base = Base_name_to_num[base_name]
    return int(value.strip(), base)


def calculate(val1: str, val2: str, base1: str, base2: str, operator: str) -> int:

    try:
        num1 = to_int(val1, base1)
        num2 = to_int(val2, base2)
    except Exception:
        raise ValueError("입력값이나 진법이 올바르지 않습니다.")

    if operator == "+":
        return num1 + num2
    elif operator == "-":
        return num1 - num2
    elif operator == "×":
        return num1 * num2
    elif operator == "÷":
        if num2 == 0:
            raise ZeroDivisionError("0으로 나눌 수 없습니다.")
        return num1 // num2
    else:
        raise ValueError("지원되지 않는 연산자입니다.")


def convert_result_to_bases(value: int) -> dict:

    return {
        "2진법": bin(value),
        "8진법": oct(value),
        "10진법": str(value),
        "16진법": hex(value).upper()
    }
