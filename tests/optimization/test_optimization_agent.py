from core.schemas.job import JobStatus
from core.schemas.tracking import ApplicationTracking, TrackingEvent
from agents.agent_07_optimization.optimization_agent import OptimizationAgent


def test_optimization_counts_reached_interview_after_rejection():
    agent = OptimizationAgent()

    tracking = ApplicationTracking(
        job_id="optimization-001",
        current_status=JobStatus.REJECTED,
        history=[
            TrackingEvent(
                status=JobStatus.APPLIED,
                note="Candidatura enviada.",
            ),
            TrackingEvent(
                status=JobStatus.SCREENING,
                note="Triagem iniciada.",
            ),
            TrackingEvent(
                status=JobStatus.INTERVIEW,
                note="Entrevista realizada.",
            ),
            TrackingEvent(
                status=JobStatus.REJECTED,
                note="Processo encerrado.",
            ),
        ],
    )

    metrics = agent.calculate_metrics([tracking])

    assert metrics["total_applications"] == 1
    assert metrics["screening_or_beyond"] == 1
    assert metrics["interviews"] == 1
    assert metrics["finals"] == 0
    assert metrics["offers"] == 0
    assert metrics["hires"] == 0
    assert metrics["rejections"] == 1
    assert metrics["response_rate"] == 100.0
    assert metrics["interview_rate"] == 100.0
    assert metrics["offer_rate"] == 0.0
    assert metrics["hire_rate"] == 0.0


def test_optimization_returns_zero_metrics_without_applications():
    agent = OptimizationAgent()

    metrics = agent.calculate_metrics([])

    assert metrics["total_applications"] == 0
    assert metrics["screening_or_beyond"] == 0
    assert metrics["interviews"] == 0
    assert metrics["finals"] == 0
    assert metrics["offers"] == 0
    assert metrics["hires"] == 0
    assert metrics["rejections"] == 0
    assert metrics["response_rate"] == 0.0
    assert metrics["interview_rate"] == 0.0
    assert metrics["offer_rate"] == 0.0
    assert metrics["hire_rate"] == 0.0
