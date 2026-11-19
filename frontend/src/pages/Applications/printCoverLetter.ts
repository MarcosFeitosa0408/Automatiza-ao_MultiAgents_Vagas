/** Abre a carta revisada para impressão local, sem transmitir o documento. */
export function printCoverLetter(article: HTMLElement, name: string): void {
  const page = window.open("", "_blank", "width=900,height=750");
  if (!page) {
    throw new Error("O navegador bloqueou a janela da carta. Permita pop-ups para esta plataforma e tente novamente.");
  }
  try {
    page.opener = null;
    const doc = page.document;
    doc.title = `Carta de Apresentação - ${name || "Candidato"}`;
    doc.documentElement.lang = "pt-BR";
    const style = doc.createElement("style");
    style.textContent = `
      @page { size: A4; margin: 20mm; }
      * { box-sizing: border-box; }
      body { margin: 0; background: white; color: #111; font: 11pt Arial, sans-serif; line-height: 1.6; }
      article { max-width: 170mm; margin: 24px auto; overflow-wrap: anywhere; }
      header { border-bottom: 1px solid #aaa; padding-bottom: 12px; margin-bottom: 20px; }
      h2 { margin: 0 0 6px; font-size: 18pt; }
      h3 { margin: 0 0 18px; font-size: 13pt; }
      p { margin: 0 0 14px; white-space: pre-wrap; }
      header p { margin: 2px 0; }
      header { break-inside: avoid; }
      h3 { break-after: avoid; }
      @media print { article { margin: 0; max-width: none; } }
    `;
    doc.head.append(style);
    // O React renderiza os dados como texto. Nenhum HTML do perfil é interpretado.
    doc.body.replaceChildren(article.cloneNode(true));
    page.focus();
    page.print();
  } catch {
    page.close();
    throw new Error("Não foi possível abrir a carta para salvar em PDF. Tente novamente.");
  }
}
