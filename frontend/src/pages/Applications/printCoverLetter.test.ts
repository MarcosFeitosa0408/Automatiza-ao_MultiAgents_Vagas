import { afterEach, expect, it, vi } from "vitest";
import { printCoverLetter } from "./printCoverLetter";
afterEach(() => vi.restoreAllMocks());

it("informa o bloqueio de pop-up e preserva a carta", () => {
  vi.spyOn(window, "open").mockReturnValue(null);
  const article = document.createElement("article");
  article.textContent = "Carta preservada";
  expect(() => printCoverLetter(article, "Pessoa")).toThrow("Permita pop-ups");
  expect(article.textContent).toBe("Carta preservada");
});
