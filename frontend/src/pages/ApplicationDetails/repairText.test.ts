import { expect, it } from "vitest";
import { repairText } from "./repairText";

it("propõe recuperação reversível de acentos sem alterar texto correto ou caracteres perdidos", () => {
  expect(repairText("agÃªncia estÃ¡ contratando um analista jÃºnior")).toBe("agência está contratando um analista júnior");
  expect(repairText("AnÃ¡lise e organizaÃ§Ã£o de dados")).toBe("Análise e organização de dados");
  expect(repairText("Júnior — São Paulo 🤖")).toBe("Júnior — São Paulo 🤖");
  expect(repairText("Texto com � perdido")).toBe("Texto com � perdido");
  expect(repairText("Ã isolado")).toBe("Ã isolado");
});

it("corrige acentos corrompidos preservando emoji e texto correto", () => {
  expect(repairText("🤖 AgÃªncia — São Paulo"))
    .toBe("🤖 Agência — São Paulo");
});

it("corrige um trecho sem modificar os acentos corretos ao lado", () => {
  expect(repairText("Análise de dados na agÃªncia"))
    .toBe("Análise de dados na agência");
});

it("corrige sequências recuperáveis sem apagar caracteres perdidos", () => {
  expect(repairText("AgÃªncia com � perdido"))
    .toBe("Agência com � perdido");
});
