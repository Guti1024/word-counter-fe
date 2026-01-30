import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional


def _json_print(d: Dict):
    # 2개 이상 키면 개행(indent) 처리
    if len(d.keys()) >= 2:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(d, ensure_ascii=False))


def load_text(text: Optional[str] = None, file_path: Optional[str] = None) -> str:
    if text is not None:
        return text
    if file_path is not None:
        p = Path(file_path)
        return p.read_text(encoding="utf-8")
    return ""


def count_terms_in_text(text: str, terms: List[str]) -> Dict[str, int]:
    lower_text = text.lower()
    out: Dict[str, int] = {}

    # ✅ 특수문자/숫자가 "사이에" 들어간 형태를 하나의 토큰으로 취급
    # 예: hello-world, hello.world, hello/word, hello+world, hello1world => 전부 "hello"로 매칭되지 않음
    token_pattern = r"[0-9A-Za-z가-힣]+(?:[^\s0-9A-Za-z가-힣]+[0-9A-Za-z가-힣]+)*"
    tokens = re.findall(token_pattern, lower_text)
    counter = Counter(tokens)

    for original in terms:
        term = (original or "").strip().lower()
        if not term:
            continue

        # ✅ 공백 포함(구문) 검색은 "정확히 동일한 구문"만 매칭
        if " " in term:
            phrase_pattern = rf"(?<!\S){re.escape(term)}(?!\S)"
            out[original] = len(re.findall(phrase_pattern, lower_text))
        else:
            out[original] = counter.get(term, 0)

    return out


def count_top_words(text: str) -> Dict[str, int]:
    tokens = re.findall(r"[0-9A-Za-z가-힣]+", text.lower())
    if not tokens:
        return {}
    c = Counter(tokens)
    max_cnt = max(c.values())
    return {w: cnt for w, cnt in c.items() if cnt == max_cnt}


def build_result(text: str, terms: Optional[List[str]]) -> Dict:
    if text.strip() == "":
        return {"error": "문자가 없습니다"}

    # ✅ 검색어가 있으면: 검색어 중 "최대 등장 횟수"만 (동률이면 가나다/abc 순)
    if terms and any(t.strip() for t in terms):
        counts = count_terms_in_text(text, terms)
        if not counts:
            return {"error": "문자가 없습니다"}  # terms가 전부 공백 등인 경우

        max_cnt = max(counts.values())
        tied_keys = sorted([k for k, v in counts.items() if v == max_cnt])  # ✅ 가나다/abc
        return {k: counts[k] for k in tied_keys}

    # ✅ 검색어 없으면: 전체 토큰 중 최다 등장 단어(동률 포함) (가나다/abc 순)
    top = count_top_words(text)
    if not top:
        return {"error": "문자가 없습니다"}

    ordered = sorted(top.keys())  # ✅ 가나다/abc
    return {k: top[k] for k in ordered}


def main():
    parser = argparse.ArgumentParser()
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--text", type=str, help="기준 텍스트")
    src.add_argument("--file", type=str, help="텍스트 파일 경로(utf-8)")

    parser.add_argument(
        "--terms",
        type=str,
        help="검색 단어들(쉼표로 구분). 미지정 시 전체 단어 중 최다 등장 단어(동률 포함) 반환",
    )
    args = parser.parse_args()

    # 입력이 없으면 인터랙티브로 받기
    text = args.text
    file_path = args.file
    if text is None and file_path is None:
        mode = input("입력 방식 선택 (text/file): ").strip().lower()
        if mode == "file":
            file_path = input("파일 경로: ").strip()
        else:
            text = input("기준 텍스트: ")

    raw_terms = args.terms
    if raw_terms is None:
        raw_terms = input("검색 단어(쉼표구분, 없으면 엔터): ").strip()
    terms = [t.strip() for t in raw_terms.split(",")] if raw_terms else []

    base_text = load_text(text=text, file_path=file_path)
    result = build_result(base_text, terms)
    _json_print(result)


if __name__ == "__main__":
    main()
