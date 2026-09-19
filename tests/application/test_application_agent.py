from agents.agent_04_application.application_agent import ApplicationAgent
from core.schemas.application import ApplicationDecision


def test_application_starts_pending_human_approval():
    agent = ApplicationAgent()

    preparation = agent.prepare(
        job_id="application-001",
        approved_for_human_review=True,
        blocking_issues=[],
        warnings=[],
    )

    assert preparation.decision == (
        ApplicationDecision.PENDING_HUMAN_APPROVAL
    )
    assert preparation.ready_to_apply is False


def test_human_can_approve_valid_application():
    agent = ApplicationAgent()

    preparation = agent.prepare(
        job_id="application-002",
        approved_for_human_review=True,
        blocking_issues=[],
        warnings=["REQUISITOS_NAO_COMPROVADOS"],
    )

    approved = agent.approve(preparation)

    assert approved.decision == ApplicationDecision.APPROVED_BY_HUMAN
    assert approved.ready_to_apply is True


def test_blocked_application_cannot_become_ready():
    agent = ApplicationAgent()

    preparation = agent.prepare(
        job_id="application-003",
        approved_for_human_review=False,
        blocking_issues=["FIT_ABAIXO_DO_LIMITE"],
        warnings=[],
    )

    approved = agent.approve(preparation)

    assert approved.decision == (
        ApplicationDecision.PENDING_HUMAN_APPROVAL
    )
    assert approved.ready_to_apply is False


def test_human_can_reject_application():
    agent = ApplicationAgent()

    preparation = agent.prepare(
        job_id="application-004",
        approved_for_human_review=True,
        blocking_issues=[],
        warnings=[],
    )

    rejected = agent.reject(preparation)

    assert rejected.decision == ApplicationDecision.REJECTED_BY_HUMAN
    assert rejected.ready_to_apply is False
