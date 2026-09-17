from agents.agent_05_tracking.tracking_agent import TrackingAgent
from core.schemas.job import JobStatus


def test_tracking_starts_with_initial_status():
    agent = TrackingAgent()

    tracking = agent.start_tracking(
        job_id="tracking-001",
    )

    assert tracking.job_id == "tracking-001"
    assert tracking.current_status == JobStatus.READY_TO_APPLY
    assert len(tracking.history) == 1
    assert tracking.history[0].status == JobStatus.READY_TO_APPLY


def test_tracking_updates_status_and_preserves_history():
    agent = TrackingAgent()

    tracking = agent.start_tracking(
        job_id="tracking-002",
    )

    updated = agent.update_status(
        tracking,
        JobStatus.APPLIED,
        note="Candidatura enviada.",
    )

    assert updated.current_status == JobStatus.APPLIED
    assert len(updated.history) == 2

    assert updated.history[0].status == JobStatus.READY_TO_APPLY
    assert updated.history[1].status == JobStatus.APPLIED
    assert updated.history[1].note == "Candidatura enviada."


def test_tracking_blocks_invalid_status_transition():
    agent = TrackingAgent()

    tracking = agent.start_tracking(
        job_id="tracking-003",
    )

    try:
        agent.update_status(
            tracking,
            JobStatus.HIRED,
            note="Transição inválida para teste.",
        )

        assert False, "A transição inválida deveria gerar ValueError."

    except ValueError as error:
        assert (
            str(error)
            == "Transição inválida: READY_TO_APPLY -> HIRED"
        )





