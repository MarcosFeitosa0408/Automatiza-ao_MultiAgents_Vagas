from pydantic import Field

from core.schemas.candidate import MasterProfile
from core.schemas.job import JobOpportunity, StrictModel


class InterviewQuestion(StrictModel):
    question_id: str
    category: str
    question: str
    guidance: list[str] = Field(default_factory=list)


class InterviewPlan(StrictModel):
    job_id: str
    job_title: str
    company: str
    questions: list[InterviewQuestion]
    preparation_notes: list[str]


class InterviewAgent:
    """Prepara um roteiro de estudo baseado na vaga e no perfil."""

    def prepare(
        self,
        job: JobOpportunity,
        profile: MasterProfile,
    ) -> InterviewPlan:
        requirements = list(
            dict.fromkeys(
                item.strip()
                for item in job.requirements
                if item.strip()
            )
        )

        if not requirements:
            raise ValueError(
                "Informe os requisitos da vaga antes de preparar a entrevista."
            )

        questions: list[InterviewQuestion] = [
            InterviewQuestion(
                question_id="presentation",
                category="Apresentação",
                question=(
                    f"Como você apresentaria sua trajetória e seu interesse "
                    f"na vaga de {job.title}?"
                ),
                guidance=[
                    "Organize uma apresentação de 60 a 90 segundos.",
                    "Relacione sua formação e sua prática aos requisitos.",
                    "Use apenas informações verdadeiras do seu perfil.",
                ],
            ),
        ]

        for index, requirement in enumerate(requirements[:8], start=1):
            questions.append(
                InterviewQuestion(
                    question_id=f"technical-{index}",
                    category="Técnica",
                    question=(
                        f"A vaga pede: {requirement}. Como você explica "
                        "esse requisito e demonstra sua prática relacionada?"
                    ),
                    guidance=[
                        "Explique o conceito com suas próprias palavras.",
                        "Apresente um exemplo real, se tiver.",
                        "Diferencie experiência profissional, projeto e estudo.",
                        "Se ainda não tiver prática, explique o que precisa aprender.",
                    ],
                )
            )

        questions.extend(
            [
                InterviewQuestion(
                    question_id="problem-solving",
                    category="Comportamental",
                    question=(
                        "Conte sobre um problema que você resolveu. "
                        "Qual era o contexto, o que você fez e qual foi o resultado?"
                    ),
                    guidance=[
                        "Organize contexto, responsabilidade, ação e resultado.",
                        "Explique sua contribuição pessoal.",
                        "Use métricas somente quando tiver evidências.",
                    ],
                ),
                InterviewQuestion(
                    question_id="practical-case",
                    category="Exercício prático",
                    question=(
                        f"Escolha um requisito de {job.title} e proponha "
                        "um pequeno exercício para demonstrar sua competência."
                    ),
                    guidance=[
                        "Defina o problema e os dados ou recursos necessários.",
                        "Explique como executaria e validaria a solução.",
                        "Trate exemplos simulados como exercícios, não como experiência.",
                    ],
                ),
                InterviewQuestion(
                    question_id="ask-recruiter",
                    category="Perguntas ao recrutador",
                    question="O que você perguntaria para entender melhor a vaga?",
                    guidance=[
                        "Pergunte sobre responsabilidades e desafios da equipe.",
                        "Confirme modalidade, localização e etapas da seleção.",
                        "Pergunte como o desempenho será acompanhado.",
                    ],
                ),
            ]
        )

        notes = [
            "Este roteiro é para preparação e não prevê as perguntas reais.",
            "Treinar não garante aprovação no processo seletivo.",
            "Revise o anúncio completo antes da entrevista.",
        ]

        if profile.experience:
            notes.append(
                "Revise estas experiências do perfil: "
                + "; ".join(
                    f"{item.role} — {item.company}"
                    for item in profile.experience
                )
            )

        if profile.projects:
            notes.append(
                "Revise seus projetos e sua participação em cada um: "
                + "; ".join(item.name for item in profile.projects)
            )

        return InterviewPlan(
            job_id=job.job_id,
            job_title=job.title,
            company=job.company,
            questions=questions,
            preparation_notes=notes,
        )