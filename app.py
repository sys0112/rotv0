import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import os
from flask import Flask, render_template, jsonify, request, redirect, session
import db
import license as lic
import crawler
import analyzer
import pension_crawler
import pension_analyzer

_tmpl = os.environ.get("ROTTO_TEMPLATE_PATH")
app = Flask(__name__, template_folder=_tmpl) if _tmpl else Flask(__name__)

db.init_license_db()
app.secret_key = db.get_or_create_flask_secret()

_LICENSE_EXEMPT = {
    "/license",
    "/api/license/activate",
    "/admin",
    "/admin/login",
    "/admin/logout",
    "/api/admin/generate",
}

@app.before_request
def check_license():
    if request.path in _LICENSE_EXEMPT:
        return
    if not lic.is_licensed():
        return redirect("/license")


@app.route("/license")
def license_page():
    if lic.is_licensed():
        return redirect("/")
    return render_template("license.html")


@app.route("/api/license/activate", methods=["POST"])
def api_license_activate():
    data = request.get_json(silent=True) or {}
    key = str(data.get("key", "")).strip().upper()
    if not key:
        return jsonify({"success": False, "error": "키를 입력해주세요"}), 400
    if not lic.validate_key(key):
        return jsonify({"success": False, "error": "유효하지 않은 키"}), 401
    lic.write_license_file(key)
    return jsonify({"success": True})


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


@app.route("/pension")
def pension():
    db.init_pension_db()
    draws = db.get_all_pension_draws()
    return render_template(
        "pension.html",
        total=len(draws),
        first_round=draws[0]["round"] if draws else 0,
        latest_round=draws[-1]["round"] if draws else 0,
    )


@app.route("/api/pension/update", methods=["POST"])
def api_pension_update():
    db.init_pension_db()
    latest_local = db.get_latest_pension_round()
    try:
        all_draws = pension_crawler.fetch_all_pension_draws()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    latest_remote = max((d["round"] for d in all_draws), default=0)
    if latest_local >= latest_remote:
        draws = db.get_all_pension_draws()
        first = draws[0]["round"] if draws else 0
        return jsonify({"saved": 0, "latest": latest_local, "total": len(draws), "first_round": first})

    saved = 0
    for draw in all_draws:
        if draw["round"] > latest_local:
            try:
                db.save_pension_draw(draw["round"], draw["date"], draw["jo"], draw["number"])
                saved += 1
            except Exception:
                pass

    draws = db.get_all_pension_draws()
    first = draws[0]["round"] if draws else 0
    return jsonify({"saved": saved, "failed": 0, "latest": latest_remote, "total": len(draws), "first_round": first})


@app.route("/api/pension/stats")
def api_pension_stats():
    db.init_pension_db()
    draws = db.get_all_pension_draws()
    if not draws:
        return jsonify({"total": 0, "latest": 0, "first": 0, "positions": [], "jo": []})
    stats = pension_analyzer.pension_frequency_analysis(draws)
    stats["total"] = len(draws)
    stats["latest"] = draws[-1]["round"]
    stats["first"] = draws[0]["round"]
    return jsonify(stats)


@app.route("/api/pension/pick")
def api_pension_pick():
    strategy = request.args.get("strategy", "mixed")
    count = int(request.args.get("count", 5))
    db.init_pension_db()
    draws = db.get_all_pension_draws()
    if not draws:
        return jsonify({"error": "데이터가 없습니다"}), 400
    sets = pension_analyzer.pick_pension_numbers(draws, strategy=strategy, count=count)
    return jsonify({"sets": sets})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
