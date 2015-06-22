import pytest
from datetime import datetime, timedelta
from registry.models import Passport, DeactivatedException
from registry.extensions import db


def test_visits_are_ordered(app):
    """Visits are ordered by check_in"""
    with app.test_request_context():
        passport = Passport.create('John', 'Doe', 111)
        when = datetime.now()
        passport.check_in(when - timedelta(minutes=10))
        passport.check_out(when - timedelta(minutes=9))
        passport.check_out(when - timedelta(minutes=6))  # Corrupt one
        passport.check_in(when - timedelta(minutes=5))
        passport.check_out(when - timedelta(minutes=4))
        passport.check_in(when - timedelta(minutes=3))
        passport.check_in(when - timedelta(minutes=2))
        passport.check_out(when - timedelta(minutes=0))

        db.session.expire_all()

        passport = Passport.get(111)

        for i in range(0, len(passport.visits) - 1):
            v1 = passport.visits[i]
            v2 = passport.visits[i + 1]
            assert v1.timestamp > v2.timestamp


def test_new_passport_is_inactive(app):
    """Passes with no transaction are not activated"""
    with app.test_request_context():
        passport = Passport.create('John', 'Doe', 111)
        assert passport.is_active is False


def test_visit_activates_passport(app):
    """Visit activates Passport"""
    with app.test_request_context():
        passport = Passport.create('John', 'Doe', 111)
        passport.check_in()
        assert passport.is_active is True


def test_deactivated_pass_cannot_check_in(app):
    """Deactivated pass cannot be checked in"""
    with app.test_request_context():
        passport = Passport.create('Bad John', 'Doe', 111)
        passport.deactivate()
        with pytest.raises(DeactivatedException):
            passport.check_in()


def test_check_in_creates_visit(app):
    """Checkin create visit"""
    with app.test_request_context():
        passport = Passport.create('John', 'Doe', 111)
        passport.check_in()

        db.session.expire_all()

        assert Passport.get(111).visits[0].check_in


def test_check_out_closes_visit(app):
    """Checkin create visit"""
    with app.test_request_context():
        passport = Passport.create('John', 'Doe', 111)
        passport.check_in()
        passport.check_out()

        db.session.expire_all()

        assert Passport.get(111).visits[0].check_out
