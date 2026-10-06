type Props = { message: string; working?: boolean; mood?: "ready" | "retry" };

/** Só acompanha estados reais da interface; não representa uma integração extra. */
export default function RobotStatus({ message, working = false, mood = "ready" }: Props) {
  return <p role="status" className={`robot-status ${working ? "robot-working" : ""}`}>
    <span className="robot-mascot" aria-hidden="true">🤖</span>
    <span>{message}</span>
    {!working && <span aria-hidden="true">{mood === "retry" ? "💙" : "✨"}</span>}
  </p>;
}
