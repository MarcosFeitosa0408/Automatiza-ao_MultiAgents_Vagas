from core.resume_preview import ResumePreview, build_resume_preview
from datetime import datetime
import os

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.database import initialize_database
from core.orchestrator.orchestrator import JobOrchestrator
from core.schemas.api import (
    ApplicationDecisionRequest,
    JobAnalysisRequest,
    JobApplicationCreateRequest,
    StoredTrackingStatusUpdateRequest,
    TrackingStatusUpdateRequest,
)
from core.schemas.job import JobOpportunity
from core.opportunity_search_api import router as opportunity_search_router
from core.schemas.candidate import MasterProfile
from agents.agent_08_interview.interview_agent import (
    InterviewAgent,
    InterviewPlan,
)

from copy import copy
from fastapi.exceptions import RequestValidationError
from core.accounts import get_store, AccountMemoryAgent, AccountJobRepository
from core.auth_api import router as auth_router, require_user


def get_user_orchestrator(user=Depends(require_user)):
    scoped = copy(orchestrator)
    store = get_store()
    scoped.memory_agent = AccountMemoryAgent(store, user['id'])
    scoped.job_application_repository = AccountJobRepository(store, user['id'])
    return scoped


app = FastAPI(
    title="Plataforma Especialização Multiagente Vaga",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(opportunity_search_router, dependencies=[Depends(require_user)])

def initialize_configured_database() -> None:
    """Inicializa o banco somente quando o backend configurado é PostgreSQL."""

    if os.getenv("REPOSITORY_BACKEND", "memory").lower() == "postgres":
        initialize_database()


initialize_configured_database()

orchestrator = JobOrchestrator()


@app.exception_handler(ValueError)
async def value_error_handler(
    request: Request,
    exc: ValueError,
):
    return JSONResponse(
        status_code=400,
        content={
            "error": "business_rule_violation",
            "message": str(exc),
        },
    )


@app.get("/health")
def health_check():


    return {
        "status": "ok",
        "service": "multiagent-job-platform",
        "version": "0.2.0",
    }


@app.post("/analyze-job")
def analyze_job(request: JobAnalysisRequest, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    job = JobOpportunity(
        job_id=request.job_id,
        title=request.title,
        company=request.company,
        source=request.source,
        location=request.location,
        work_model=request.work_model,
        employment_type=request.employment_type,
        description=request.description,
        requirements=request.requirements,
        desirable_requirements=request.desirable_requirements,
    )

    result = orchestrator.run([job])[0]

    return result


@app.post("/personalize-job")
def personalize_job(request: JobAnalysisRequest, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    job = JobOpportunity(
        job_id=request.job_id,
        title=request.title,
        company=request.company,
        source=request.source,
        location=request.location,
        work_model=request.work_model,
        employment_type=request.employment_type,
        description=request.description,
        requirements=request.requirements,
        desirable_requirements=request.desirable_requirements,
    )

    qualification = orchestrator.run([job])[0]

    personalization = orchestrator.personalize_job(
        job,
        qualification,
    )

    return {
        "qualification": qualification,
        "personalization": personalization,
    }


@app.post("/prepare-application")
def prepare_application(request: JobAnalysisRequest, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    job = JobOpportunity(
        job_id=request.job_id,
        title=request.title,
        company=request.company,
        source=request.source,
        location=request.location,
        work_model=request.work_model,
        employment_type=request.employment_type,
        description=request.description,
        requirements=request.requirements,
        desirable_requirements=request.desirable_requirements,
    )

    qualification = orchestrator.run([job])[0]

    preparation = orchestrator.prepare_application(
        job,
        qualification,
    )

    return {
        "qualification": qualification,
        "application": preparation,
    }
@app.post("/approve-application")
def approve_application(request: ApplicationDecisionRequest, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    approved = orchestrator.approve_application(
        request.application
    )

    return approved


@app.post("/reject-application")
def reject_application(request: ApplicationDecisionRequest, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    rejected = orchestrator.reject_application(
        request.application
    )

    return rejected


@app.post("/update-tracking-status")
def update_tracking_status(request: TrackingStatusUpdateRequest, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    updated = orchestrator.update_tracking_status(
        request.tracking,
        request.new_status,
        request.note,
    )

    return updated


@app.post("/job-applications")
def create_job_application(
    request: JobApplicationCreateRequest,
    orchestrator: JobOrchestrator = Depends(get_user_orchestrator),
):
    application = orchestrator.create_job_application(
        job=request.job,
        application_id=request.application_id,
    )

    saved_application = orchestrator.save_job_application(
        application
    )

    return saved_application


@app.get("/job-applications")
def list_job_applications(orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    return orchestrator.list_job_applications()


@app.get("/job-applications/metrics")
def get_job_application_metrics(orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    applications = orchestrator.list_job_applications()

    metrics = orchestrator.calculate_job_application_metrics(
        applications
    )

    return metrics


@app.get("/job-applications/{application_id}")
def get_job_application(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    return application

@app.delete("/job-applications/{application_id}")
def delete_job_application(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    deleted = orchestrator.delete_job_application(
        application_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    return {
        "application_id": application_id,
        "deleted": True,
    }


@app.post("/job-applications/{application_id}/qualify")
def qualify_job_application(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    qualified_application = (
        orchestrator.qualify_job_application(
            application
        )
    )

    saved_application = orchestrator.save_job_application(
        qualified_application
    )

    return saved_application


@app.post("/job-applications/{application_id}/personalize")
def personalize_job_application(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    personalized_application = (
        orchestrator.personalize_job_application(
            application
        )
    )

    saved_application = orchestrator.save_job_application(
        personalized_application
    )

    return saved_application


@app.post("/job-applications/{application_id}/prepare")
def prepare_job_application(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    prepared_application = (
        orchestrator.prepare_job_application(
            application
        )
    )

    saved_application = orchestrator.save_job_application(
        prepared_application
    )

    return saved_application


@app.post("/job-applications/{application_id}/approve")
def approve_stored_job_application(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    approved_application = (
        orchestrator.approve_job_application(
            application
        )
    )

    saved_application = orchestrator.save_job_application(
        approved_application
    )

    return saved_application


@app.post("/job-applications/{application_id}/reject")
def reject_stored_job_application(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    rejected_application = (
        orchestrator.reject_job_application(
            application
        )
    )

    saved_application = orchestrator.save_job_application(
        rejected_application
    )

    return saved_application


@app.post("/job-applications/{application_id}/tracking/start")
def start_stored_job_application_tracking(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    tracked_application = (
        orchestrator.start_job_application_tracking(
            application
        )
    )

    saved_application = orchestrator.save_job_application(
        tracked_application
    )

    return saved_application


@app.post("/job-applications/{application_id}/tracking/status")
def update_stored_job_application_status(
    application_id: str,
    request: StoredTrackingStatusUpdateRequest,
    orchestrator: JobOrchestrator = Depends(get_user_orchestrator),
):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    updated_application = (
        orchestrator.update_job_application_status(
            application,
            request.new_status,
            request.note,
        )
    )

    saved_application = orchestrator.save_job_application(
        updated_application
    )

    return saved_application


@app.post("/job-applications/{application_id}/follow-up/check")
def check_stored_job_application_follow_up(
    application_id: str,
    orchestrator: JobOrchestrator = Depends(get_user_orchestrator),
):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    should_follow_up = (
        orchestrator.should_follow_up_job_application(
            application=application,
        )
    )

    return {
        "application_id": application_id,
        "should_follow_up": should_follow_up,
        "followup_count": application.tracking.followup_count,
        "last_followup_at": application.tracking.last_followup_at,
    }


@app.post("/job-applications/{application_id}/follow-up/register")
def register_stored_job_application_follow_up(
    application_id: str,
    orchestrator: JobOrchestrator = Depends(get_user_orchestrator),
):
    application = orchestrator.get_job_application(
        application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Candidatura não encontrada.",
                "application_id": application_id,
            },
        )

    updated_application = (
        orchestrator.register_job_application_follow_up(
            application
        )
    )

    saved_application = orchestrator.save_job_application(
        updated_application
    )

    return saved_application


@app.get("/profile", response_model=MasterProfile)
def get_candidate_profile(orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    """Consulta o perfil usado pelos agentes."""

    try:
        return orchestrator.memory_agent.get_profile()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="O perfil ainda não foi cadastrado.",
        ) from None
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="O perfil salvo possui dados inválidos.",
        ) from None
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Não foi possível ler o perfil.",
        ) from None


@app.put("/profile", response_model=MasterProfile)
def update_candidate_profile(profile: MasterProfile, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    """Valida e salva o perfil usado pelos agentes."""

    try:
        return orchestrator.memory_agent.save_profile(profile)
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Não foi possível salvar o perfil. Tente novamente.",
        ) from None


@app.post(
    "/job-applications/{application_id}/resume-preview",
    response_model=ResumePreview,
)
def generate_resume_preview(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Candidatura não encontrada.",
        )

    try:
        profile = orchestrator.memory_agent.get_profile()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Cadastre seu perfil antes de gerar o currículo.",
        ) from None

    # Usa uma mesma leitura do perfil para análise e personalização.
    qualification = orchestrator.qualification_agent.calculate_fit(
        application.job,
        profile,
    )

    personalization = orchestrator.personalization_agent.personalize(
        application.job,
        profile,
        qualification,
    )

    return build_resume_preview(
        application_id=application.application_id,
        job_title=application.job.title,
        company=application.job.company,
        profile=profile,
        personalization=personalization,
    )

@app.post(
    "/job-applications/{application_id}/interview-plan",
    response_model=InterviewPlan,
)
def generate_interview_plan(application_id: str, orchestrator: JobOrchestrator = Depends(get_user_orchestrator)):
    application = orchestrator.get_job_application(application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Candidatura não encontrada.",
        )

    try:
        profile = orchestrator.memory_agent.get_profile()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Cadastre seu perfil antes de preparar a entrevista.",
        ) from None

    return InterviewAgent().prepare(application.job, profile)


from core.schemas.api import JobDetailsUpdateRequest
from core.schemas.job_application import JobApplicationObject
from core.schemas.job import JobStatus


@app.patch(
    "/job-applications/{application_id}/job-details",
    response_model=JobApplicationObject,
)
def update_saved_job_details(
    application_id: str,
    request: JobDetailsUpdateRequest,
    orchestrator: JobOrchestrator = Depends(get_user_orchestrator),
):
    application = orchestrator.get_job_application(application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Candidatura não encontrada.",
        )

    if application.tracking is not None or application.preparation is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Esta candidatura já possui preparação ou acompanhamento. "
                "Cadastre uma nova oportunidade para alterar o anúncio."
            ),
        )

    requirements = [
        value.strip()
        for value in request.requirements
        if value.strip()
    ]

    if not requirements:
        raise HTTPException(
            status_code=422,
            detail="Informe pelo menos um requisito real do anúncio.",
        )

    desirable = [
        value.strip()
        for value in request.desirable_requirements
        if value.strip()
    ]

    updated_job = application.job.model_copy(
        update={
            "description": request.description.strip(),
            "requirements": list(dict.fromkeys(requirements)),
            "desirable_requirements": list(dict.fromkeys(desirable)),
            "status": JobStatus.DISCOVERED,
        }
    )

    # Resultados anteriores precisam ser recalculados para o novo anúncio.
    updated_application = orchestrator._update_job_application(
        application,
        job=updated_job,
        qualification=None,
        personalization=None,
        preparation=None,
    )

    return orchestrator.save_job_application(updated_application)

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]})
