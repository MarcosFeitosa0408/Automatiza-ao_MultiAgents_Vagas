/** Imprime somente a prévia revisada, sem enviar dados a outro serviço. */
export function printResume(article: HTMLElement, name: string, language = "pt-BR"): void {
  const page = window.open("", "_blank", "width=900,height=750");
  if (!page) {
    throw new Error("O navegador bloqueou a janela do currículo. Permita pop-ups para esta plataforma e tente novamente.");
  }
  try {
    page.opener = null;
    const doc = page.document;
    doc.title = `Currículo - ${name}`;
    doc.documentElement.lang = language;
    const style = doc.createElement("style");
    style.textContent = `
      @page { size: A4; margin: 16mm; }
      * { box-sizing: border-box; }
      body { margin: 0; background: white; color: #111; font: 11pt Arial, sans-serif; line-height: 1.45; }
      article { max-width: 180mm; margin: 24px auto; overflow-wrap: anywhere; }
      header { border-bottom: 1px solid #555; padding-bottom: 10px; }
      h2 { margin: 0 0 5px; font-size: 20pt; }
      h3 { margin: 18px 0 7px; font-size: 12pt; border-bottom: 1px solid #ccc; padding-bottom: 3px; break-after: avoid; }
      p { margin: 4px 0; }
      ul { margin: 6px 0 10px; padding-left: 20px; }
      li { margin-bottom: 3px; }
      a { color: #111; text-decoration: none; }
      header, li { break-inside: avoid; }
      @media print { article { margin: 0; max-width: none; } }
    `;
    doc.head.append(style);
    const copy = article.cloneNode(true) as HTMLElement;
    // O documento contém somente elementos renderizados pelo React; nenhum HTML
    // do perfil é interpretado como marcação.
    copy.querySelectorAll("a").forEach((link) => {
      link.removeAttribute("target");
    });
    doc.body.replaceChildren(copy);
    page.focus();
    page.print();
  } catch {
    page.close();
    throw new Error("Não foi possível abrir o currículo para salvar em PDF. Tente novamente.");
  }
}
