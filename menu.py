import argparse
import sys
from persona import run_game
from main import cmd_update, cmd_stats, cmd_pick


def _lotto_menu():
    while True:
        print("\n--- 로또 번호 분석기 ---")
        print(" 1. 최신 데이터 업데이트")
        print(" 2. 번호별 출현 빈도 보기")
        print(" 3. 번호 추천받기 (혼합 전략, 5세트)")
        print(" 0. 메인으로 돌아가기")
        choice = input("선택: ").strip()

        if choice == "1":
            cmd_update(argparse.Namespace())
        elif choice == "2":
            cmd_stats(argparse.Namespace())
        elif choice == "3":
            cmd_pick(argparse.Namespace(strategy="mixed", count=5))
        elif choice == "0":
            break
        else:
            print("잘못된 입력입니다.")
            continue

        input("\n엔터를 누르면 메뉴로 돌아갑니다...")


def main():
    while True:
        print("\n" + "=" * 27)
        print("     심심풀이 도구 모음")
        print("=" * 27)
        print(" 1. 로또 번호 분석기")
        print(" 2. 페르소나 추리 게임")
        print(" 0. 종료")
        print("=" * 27)
        choice = input("선택: ").strip()

        if choice == "1":
            _lotto_menu()
        elif choice == "2":
            run_game()
        elif choice == "0":
            print("종료합니다.")
            sys.exit(0)
        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n종료합니다.")
        sys.exit(0)
