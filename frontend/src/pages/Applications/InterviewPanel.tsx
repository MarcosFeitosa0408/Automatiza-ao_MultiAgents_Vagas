import RobotStatus from "../../components/RobotStatus";
import { useRef, useState } from "react";
import { ApiError } from "../../api/client";
import { generateInterviewPlan, evaluateInterviewAnswer } from "../../api/interview";
import type { InterviewPlan, InterviewFeedback } from "../../api/interview";

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
  const [feedback, setFeedback] = useState<Record<string, InterviewFeedback>>({});
  const [evaluating, setEvaluating] = useState<string | null>(null);
  const [evaluationErrors, setEvaluationErrors] = useState<Record<string, string>>({});

  async function evaluate(questionId: string) {
    if (submitting.current) return;
    const answer = answers[questionId] ?? "";
    if (!answer.trim()) return;
    submitting.current = true;
    setEvaluating(questionId);
    setEvaluationErrors({});
    try {
      const result = await evaluateInterviewAnswer(applicationId, questionId, answer);
      setFeedback((current) => ({ ...current, [questionId]: result }));
    } catch (cause) {
      setEvaluationErrors({ [questionId]: describeError(cause) });
    } finally {
      submitting.current = false;
      setEvaluating(null);
    }
  }

  async function generate() {
    if (submitting.current) return;

    submitting.current = true;
    setLoading(true);
    setError(null);

    try {
      const result = await generateInterviewPlan(applicationId);
      setPlan(result);
      setFeedback({});
      setEvaluationErrors({});
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
        disabled={loading || evaluating !== null}
      >
        {loading ? "Preparando..." : "Preparar entrevista"}
      </button>

      {loading && <RobotStatus working message="Preparando seu roteiro…" />}
      {error && <p role="alert">{error}</p>}

      {plan && !loading && !error && <RobotStatus message="Roteiro pronto. Vamos praticar!" />}
      {plan && (
        <details open>
          <summary>Treino para {plan.job_title}</summary>

          <div className="interview-content">
            <h3>Preparação para entrevista</h3>
            <p>{plan.job_title} · {plan.company}</p>
            <p>
              Pratique com suas próprias palavras. As respostas digitadas
              ficam apenas nesta tela e serão perdidas ao sair ou atualizar
              a página. Ao clicar em Avaliar resposta, o texto será enviado
              ao servidor para avaliar sua estrutura, sem salvar a resposta.
              A nota não mede correção técnica nem prevê aprovação.
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
                    maxLength={6000}
                    disabled={loading || evaluating !== null}
                    placeholder="Escreva sua resposta para praticar..."
                    value={answers[question.question_id] ?? ""}
                    onChange={(event) => {
                      setAnswers((current) => ({
                        ...current,
                        [question.question_id]: event.target.value,
                      }));
                      setFeedback((current) => {
                        const next = { ...current };
                        delete next[question.question_id];
                        return next;
                      });
                      setEvaluationErrors({});
                    }}
                  />
                  <button className="secondary-button" type="button"
                    disabled={loading || evaluating !== null || !(answers[question.question_id] ?? "").trim()}
                    onClick={() => evaluate(question.question_id)}>
                    {evaluating === question.question_id ? "Avaliando..." : "Avaliar resposta"}
                  </button>
                  {evaluating === question.question_id && <RobotStatus working message="Analisando a estrutura da resposta…" />}
                  {evaluationErrors[question.question_id] && <p role="alert">{evaluationErrors[question.question_id]}</p>}
                  {feedback[question.question_id] && <div role="status">
                    <RobotStatus message="Análise concluída!" />
                    <h4>Nota de estrutura: {feedback[question.question_id].score}/100</h4>
                    <p>{feedback[question.question_id].score >= 75
                      ? <><span aria-hidden="true">🎉👏</span> Muito bem! Sua resposta apresenta vários indícios de estrutura. Confira as orientações.</>
                      : feedback[question.question_id].score >= 40
                        ? <><span aria-hidden="true">🙂💪</span> Você está avançando! Confira as sugestões e tente novamente.</>
                        : <><span aria-hidden="true">😕💙</span> Ainda podemos desenvolver essa resposta. Vamos praticar juntos?</>}</p>
                    <ul>{feedback[question.question_id].criteria.map((criterion) => (
                      <li key={criterion.name}><strong>{criterion.name}: {criterion.score}/{criterion.maximum}</strong> — {criterion.guidance}</li>
                    ))}</ul>
                    <p>{feedback[question.question_id].limitation}</p>
                    <p>Edite sua resposta e avalie novamente para praticar. Use somente experiências e resultados reais.</p>
                  </div>}
                </section>
              );
            })}
          </div>
        </details>
      )}
    </div>
  );
}
