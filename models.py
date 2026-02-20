from datetime import date, datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, default=date.today)
    passed = db.Column(db.Boolean, nullable=False)  # True = doorgereden
    amount_saved = db.Column(db.Float, default=0.0)
    note = db.Column(db.String(200), default="")

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "passed": self.passed,
            "amount_saved": self.amount_saved,
            "note": self.note,
        }


class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subscription_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)

    @staticmethod
    def get(key, default=None):
        s = Settings.query.filter_by(key=key).first()
        return s.value if s else default

    @staticmethod
    def set(key, value):
        s = Settings.query.filter_by(key=key).first()
        if s:
            s.value = str(value)
        else:
            s = Settings(key=key, value=str(value))
            db.session.add(s)
        db.session.commit()
