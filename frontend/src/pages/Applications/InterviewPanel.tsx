import { useRef, useState } from "react";
import { ApiError } from "../../api/client";
import { generateInterviewPlan } from "../../api/interview";
import type { InterviewPlan } from "../../api/interview";

type InterviewPanelProps = {
  applicationId: string;
};

function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.detail && typeof error.detail === "object") {
      const body = error.detail as Record<string, unknown>;

      if (typeof body.message === "string") return body.message;
      if (typeof body.detail === "string") return body.detail;
    }

    return "Não foi possível preparar a entrevista. Confira o perfil e a vaga.";
  }

  return "Não foi possível conectar ao servidor.";
}

export default function InterviewPanel({
  applicationId,
}: InterviewPanelProps) {
  const [plan, setPlan] = useState<InterviewPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const submitting = useRef(false);

  async function generate() {
    if (submitting.current) return;

    submitting.current = true;
    setLoading(true);
    setError(null);

    try {
      const result = await generateInterviewPlan(applicationId);
      setPlan(result);
    } catch (cause) {
      setError(describeError(cause));
    } finally {
      submitting.current = false;
      setLoading(false);
    }
  }

  return (
    <div className="interview-panel">
      <button
        className="secondary-button"
        type="button"
        onClick={generate}
        disabled={loading}
      >
        {loading ? "Preparando..." : "Preparar entrevista"}
      </button>

      {loading && <p role="status">Preparando seu roteiro...</p>}
      {error && <p role="alert">{error}</p>}

      {plan && (
        <details open>
          <summary>Treino para {plan.job_title}</summary>

          <div className="interview-content">
            <h3>Preparação para entrevista</h3>
            <p>{plan.job_title} · {plan.company}</p>
            <p>
              Pratique com suas próprias palavras. As respostas digitadas
              ficam apenas nesta tela e serão perdidas ao sair ou atualizar
              a página. Ainda não há avaliação automática.
            </p>

            <ul>
              {plan.preparation_notes.map((note, index) => (
                <li key={index}>{note}</li>
              ))}
            </ul>

            {plan.questions.map((question, index) => {
              const id =
                `answer-${applicationId}-${question.question_id}`;

              return (
                <section
                  className="interview-question"
                  key={question.question_id}
                >
                  <p><strong>{question.category}</strong></p>
                  <label htmlFor={id}>
                    {index + 1}. {question.question}
                  </label>

                  <ul>
                    {question.guidance.map((guidance, position) => (
                      <li key={position}>{guidance}</li>
                    ))}
                  </ul>

                  <textarea
                    id={id}
                    rows={6}
                    placeholder="Escreva sua resposta para praticar..."
                    value={answers[question.question_id] ?? ""}
                    onChange={(event) =>
                      setAnswers((current) => ({
                        ...current,
                        [question.question_id]: event.target.value,
                      }))
                    }
                  />
                </section>
              );
            })}
          </div>
        </details>
      )}
    </div>
  );
}