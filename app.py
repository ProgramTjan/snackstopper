import json
from datetime import date, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template, request

from config import Config
from models import CheckIn, PushSubscription, Settings, db
from push import send_push_to_all

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

scheduler = BackgroundScheduler(daemon=True)


def send_daily_reminder():
    """Scheduled job: send push reminder."""
    with app.app_context():
        today = date.today()
        already = CheckIn.query.filter_by(date=today).first()
        if not already:
            send_push_to_all(
                "Op weg naar huis? Rij door! \U0001f697\U0001f4a8",
                app.config["VAPID_PRIVATE_KEY"],
                app.config["VAPID_CLAIMS_EMAIL"],
            )


def schedule_reminder():
    """Set up or reschedule the daily reminder."""
    with app.app_context():
        time_str = Settings.get("reminder_time", app.config["DEFAULT_REMINDER_TIME"])
    hour, minute = map(int, time_str.split(":"))

    scheduler.remove_all_jobs()
    scheduler.add_job(
        send_daily_reminder,
        "cron",
        hour=hour,
        minute=minute,
        id="daily_reminder",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()


# --- Routes ---


@app.route("/")
def index():
    return render_template("index.html", vapid_public_key=app.config["VAPID_PUBLIC_KEY"])


@app.route("/api/checkin", methods=["POST"])
def checkin():
    data = request.get_json()
    passed = data.get("passed", True)
    note = data.get("note", "")

    avg = float(Settings.get("average_amount", app.config["DEFAULT_AVERAGE_AMOUNT"]))
    amount_saved = avg if passed else 0.0

    today = date.today()
    existing = CheckIn.query.filter_by(date=today).first()
    if existing:
        existing.passed = passed
        existing.amount_saved = amount_saved
        existing.note = note
    else:
        existing = CheckIn(date=today, passed=passed, amount_saved=amount_saved, note=note)
        db.session.add(existing)

    db.session.commit()
    return jsonify(existing.to_dict())


@app.route("/api/stats")
def stats():
    checkins = CheckIn.query.order_by(CheckIn.date.desc()).all()

    # Calculate streak
    streak = 0
    for ci in checkins:
        if ci.passed:
            streak += 1
        else:
            break

    total_saved = sum(ci.amount_saved for ci in checkins)
    total_days = len(checkins)
    days_passed = sum(1 for ci in checkins if ci.passed)

    today_checkin = CheckIn.query.filter_by(date=date.today()).first()

    return jsonify({
        "streak": streak,
        "total_saved": round(total_saved, 2),
        "total_days": total_days,
        "days_passed": days_passed,
        "checked_in_today": today_checkin is not None,
        "today_passed": today_checkin.passed if today_checkin else None,
    })


@app.route("/api/history")
def history():
    checkins = CheckIn.query.order_by(CheckIn.date.desc()).limit(30).all()
    return jsonify([ci.to_dict() for ci in checkins])


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json()
    sub_json = json.dumps(data)

    # Avoid duplicates
    existing = PushSubscription.query.filter_by(subscription_json=sub_json).first()
    if not existing:
        sub = PushSubscription(subscription_json=sub_json)
        db.session.add(sub)
        db.session.commit()

    return jsonify({"ok": True})


@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        data = request.get_json()
        if "reminder_time" in data:
            Settings.set("reminder_time", data["reminder_time"])
            schedule_reminder()
        if "average_amount" in data:
            Settings.set("average_amount", data["average_amount"])
        return jsonify({"ok": True})

    return jsonify({
        "reminder_time": Settings.get("reminder_time", app.config["DEFAULT_REMINDER_TIME"]),
        "average_amount": float(Settings.get("average_amount", app.config["DEFAULT_AVERAGE_AMOUNT"])),
    })


# --- Init ---

with app.app_context():
    db.create_all()

schedule_reminder()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
