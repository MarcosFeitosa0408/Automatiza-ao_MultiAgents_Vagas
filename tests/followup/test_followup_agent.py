from datetime import datetime, timedelta, timezone

from agents.agent_06_followup.followup_agent import FollowUpAgent
from core.schemas.job import JobStatus
from core.schemas.tracking import ApplicationTracking


def test_first_followup_is_allowed_after_five_days():
    agent = FollowUpAgent()

    now = datetime.now(timezone.utc)
    last_contact = now - timedelta(days=5)

    tracking = ApplicationTracking(
        job_id="followup-001",
        current_status=JobStatus.APPLIED,
    )

    result = agent.should_follow_up(
        tracking=tracking,
        followup_count=0,
        last_contact_at=last_contact,
        now=now,
    )

    assert result is True


def test_first_followup_is_blocked_before_five_days():
    agent = FollowUpAgent()

    now = datetime.now(timezone.utc)
    last_contact = now - timedelta(days=4)

    tracking = ApplicationTracking(
        job_id="followup-002",
        current_status=JobStatus.APPLIED,
    )

    result = agent.should_follow_up(
        tracking=tracking,
        followup_count=0,
        last_contact_at=last_contact,
        now=now,
    )

    assert result is False


def test_followup_is_blocked_after_two_contacts():
    agent = FollowUpAgent()

    now = datetime.now(timezone.utc)
    last_contact = now - timedelta(days=10)

    tracking = ApplicationTracking(
        job_id="followup-003",
        current_status=JobStatus.APPLIED,
    )

    result = agent.should_follow_up(
        tracking=tracking,
        followup_count=2,
        last_contact_at=last_contact,
        now=now,
    )

    assert result is False


def test_followup_is_blocked_for_terminal_status():
    agent = FollowUpAgent()

    now = datetime.now(timezone.utc)
    last_contact = now - timedelta(days=10)

    tracking = ApplicationTracking(
        job_id="followup-004",
        current_status=JobStatus.REJECTED,
    )

    result = agent.should_follow_up(
        tracking=tracking,
        followup_count=0,
        last_contact_at=last_contact,
        now=now,
    )

    assert result is False


def test_second_followup_is_allowed_after_seven_days():
    agent = FollowUpAgent()

    now = datetime.now(timezone.utc)
    last_contact = now - timedelta(days=7)

    tracking = ApplicationTracking(
        job_id="followup-005",
        current_status=JobStatus.SCREENING,
    )

    result = agent.should_follow_up(
        tracking=tracking,
        followup_count=1,
        last_contact_at=last_contact,
        now=now,
    )

    assert result is True


def test_second_followup_is_blocked_before_seven_days():
    agent = FollowUpAgent()

    now = datetime.now(timezone.utc)
    last_contact = now - timedelta(days=6)

    tracking = ApplicationTracking(
        job_id="followup-006",
        current_status=JobStatus.SCREENING,
    )

    result = agent.should_follow_up(
        tracking=tracking,
        followup_count=1,
        last_contact_at=last_contact,
        now=now,
    )

    assert result is False
