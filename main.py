import argparse
import db
import crawler
import analyzer


def cmd_update(args):
    db.init_db()
    latest_local = db.get_latest_round()
    latest_remote = crawler.fetch_latest_round()

    if latest_local >= latest_remote:
        print(f"이미 최신 상태입니다. (회차: {latest_local})")
        return

    total = latest_remote - latest_local
    print(f"크롤링 시작: {latest_local + 1}회차 ~ {latest_remote}회차 (총 {total}개)")

    session = crawler.build_session()
    saved = 0
    failed = 0
    for round_no in range(latest_local + 1, latest_remote + 1):
        draw = crawler.fetch_draw(round_no, _session=session)
        if draw:
            db.save_draw(draw["round"], draw["date"], draw["numbers"], draw["bonus"])
            saved += 1
        else:
            failed += 1
        print(f"  진행 중: {round_no}/{latest_remote}회차", end="\r", flush=True)

    print(f"\n완료! {saved}개 회차 저장됨" + (f" ({failed}개 실패)" if failed else ""))


def cmd_stats(args):
    db.init_db()
    draws = db.get_all_draws()
    if not draws:
        print("데이터가 없습니다. 먼저 'python main.py update'를 실행하세요.")
        return

    stats = analyzer.frequency_analysis(draws)
    total = len(draws)

    print(f"\n[번호별 출현 빈도 - 전체 {total}회차 기준]")
    print(f"{'순위':>4}  {'번호':>4}  {'출현횟수':>8}  {'출현률':>7}  {'미출현(회차)':>12}")
    print("-" * 55)
    for i, s in enumerate(stats, 1):
        print(f"{i:>4}  {s['number']:>4}  {s['count']:>8}  {s['pct']:>6.1f}%  {s['last_seen_ago']:>12}회차")


def cmd_pick(args):
    db.init_db()
    draws = db.get_all_draws()
    if not draws:
        print("데이터가 없습니다. 먼저 'python main.py update'를 실행하세요.")
        return

    strategy_names = {"hot": "핫넘버", "cold": "콜드넘버", "mixed": "혼합"}
    print(f"\n[추천 번호 - {strategy_names[args.strategy]} 전략]")
    sets = analyzer.pick_numbers(draws, strategy=args.strategy, count=args.count)
    for i, nums in enumerate(sets, 1):
        formatted = "  ".join(f"{n:02d}" for n in nums)
        print(f"세트 {i}: {formatted}")


def main():
    parser = argparse.ArgumentParser(description="로또 번호 통계 분석 및 추천")
    subs = parser.add_subparsers(dest="command")

    subs.add_parser("update", help="최신 당첨 번호 크롤링")
    subs.add_parser("stats", help="번호별 출현 빈도 통계")

    pick_parser = subs.add_parser("pick", help="번호 추천")
    pick_parser.add_argument("--count", type=int, default=5, help="추천 세트 수 (기본: 5)")
    pick_parser.add_argument(
        "--strategy",
        choices=["hot", "cold", "mixed"],
        default="mixed",
        help="추천 전략 (기본: mixed)",
    )

    args = parser.parse_args()

    if args.command == "update":
        cmd_update(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "pick":
        cmd_pick(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
