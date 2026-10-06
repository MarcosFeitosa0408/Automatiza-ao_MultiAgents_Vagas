import { afterEach, expect, it, vi } from "vitest";
import { printResume } from "./printResume";

afterEach(() => vi.restoreAllMocks());

it("exporta apenas o currículo, preserva texto e links e não interpreta dados como HTML", () => {
  const doc = document.implementation.createHTMLDocument();
  const print = vi.fn();
  const page = { document: doc, opener: window, focus: vi.fn(), print, close: vi.fn() };
  vi.spyOn(window, "open").mockReturnValue(page as unknown as Window);
  const article = document.createElement("article");
  const text = document.createElement("p");
  text.textContent = 'Análise <script>alert("teste")</script> & SQL';
  const link = document.createElement("a");
  link.href = "https://example.com/portfolio";
  link.textContent = link.href;
  link.target = "_blank";
  article.append(text, link);
  const review = document.createElement("p");
  review.textContent = "Requisitos sem correspondência: segredo de teste";
  document.body.append(article, review);
  try {
    printResume(article, "Pessoa de Teste");
    expect(doc.title).toBe("Currículo - Pessoa de Teste");
    expect(doc.documentElement.lang).toBe("pt-BR");
    expect(doc.body.textContent).toContain(text.textContent);
    expect(doc.querySelector("script")).toBeNull();
    expect(doc.body.textContent).not.toContain("segredo de teste");
    expect(doc.querySelector("a")?.href).toBe(link.href);
    expect(page.opener).toBeNull();
    expect(print).toHaveBeenCalledOnce();
  } finally {
    article.remove();
    review.remove();
  }
});

it("informa quando o navegador bloqueia a janela sem apagar a prévia", () => {
  vi.spyOn(window, "open").mockReturnValue(null);
  const article = document.createElement("article");
  article.textContent = "Currículo preservado";
  expect(() => printResume(article, "Pessoa")).toThrow("Permita pop-ups");
  expect(article.textContent).toBe("Currículo preservado");
});
