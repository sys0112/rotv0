import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import os
from flask import Flask, render_template, jsonify, request
import db
import crawler
import analyzer

_tmpl = os.environ.get("ROTTO_TEMPLATE_PATH")
app = Flask(__name__, template_folder=_tmpl) if _tmpl else Flask(__name__)


@app.route("/")
def index():
    db.init_db()
    draws = db.get_all_draws()
    return render_template(
        "index.html",
        total=len(draws),
        first_round=draws[0]["round"] if draws else 0,
        latest_round=draws[-1]["round"] if draws else 0,
    )


@app.route("/api/stats")
def api_stats():
    db.init_db()
    draws = db.get_all_draws()
    stats = analyzer.frequency_analysis(draws)
    return jsonify(stats)


@app.route("/api/update", methods=["POST"])
def api_update():
    db.init_db()
    latest_local = db.get_latest_round()
    try:
        latest_remote = crawler.fetch_latest_round()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if latest_local >= latest_remote:
        draws = db.get_all_draws()
        first = draws[0]["round"] if draws else 0
        return jsonify({"saved": 0, "latest": latest_local, "total": len(draws), "first_round": first})

    session = crawler.build_session()
    saved = 0
    failed = 0
    for round_no in range(latest_local + 1, latest_remote + 1):
        try:
            draw = crawler.fetch_draw(round_no, _session=session)
            if draw:
                db.save_draw(draw["round"], draw["date"], draw["numbers"], draw["bonus"])
                saved += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    draws = db.get_all_draws()
    first = draws[0]["round"] if draws else 0
    return jsonify({"saved": saved, "failed": failed, "latest": latest_remote, "total": len(draws), "first_round": first})


@app.route("/api/pick")
def api_pick():
    strategy = request.args.get("strategy", "mixed")
    count = int(request.args.get("count", 5))
    db.init_db()
    draws = db.get_all_draws()
    if not draws:
        return jsonify({"error": "데이터가 없습니다"}), 400
    sets = analyzer.pick_numbers(draws, strategy=strategy, count=count)
    return jsonify({"sets": sets})



if __name__ == "__main__":
    app.run(debug=True, port=5000)
