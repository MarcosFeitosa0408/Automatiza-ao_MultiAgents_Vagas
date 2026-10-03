import { useRef, useState } from "react";
import { deleteJobApplication } from "../../api/applications";

type Props = {
  applicationId: string;
  title: string;
  company: string;
  onDeleted: (applicationId: string) => void;
};

export default function DeleteApplication({ applicationId, title, company, onDeleted }: Props) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pending = useRef(false);

  async function remove() {
    if (pending.current) return;
    pending.current = true;
    setDeleting(true);
    setError(null);
    try {
      const result = await deleteJobApplication(applicationId);
      if (!result.deleted || result.application_id !== applicationId) {
        throw new Error("Exclusão não confirmada");
      }
      onDeleted(applicationId);
    } catch {
      setError("Não foi possível confirmar a exclusão. Atualize a lista antes de tentar novamente.");
    } finally {
      pending.current = false;
      setDeleting(false);
    }
  }

  return (
    <div className="application-delete">
      {!confirming ? (
        <button className="secondary-button" type="button" onClick={() => setConfirming(true)}>
          Excluir oportunidade
        </button>
      ) : (
        <div role="group" aria-label="Confirmar exclusão da oportunidade">
          <p>Excluir {title} · {company} da sua conta?</p>
          <p>Isso remove o registro e seu histórico nesta plataforma. Não cancela uma candidatura enviada em outro site.</p>
          <button className="secondary-button" type="button" disabled={deleting} onClick={() => { setConfirming(false); setError(null); }}>
            Manter oportunidade
          </button>
          <button className="secondary-button" type="button" disabled={deleting} onClick={() => void remove()}>
            {deleting ? "Excluindo..." : "Confirmar exclusão"}
          </button>
        </div>
      )}
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
