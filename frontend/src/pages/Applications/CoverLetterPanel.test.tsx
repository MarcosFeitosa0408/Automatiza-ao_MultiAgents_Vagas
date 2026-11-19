import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CoverLetterPanel from "./CoverLetterPanel";
import { generateResumePreview } from "../../api/resume";
import { ApiError } from "../../api/client";
import { coverLetterFixture } from "../../test/coverLetterFixture";

vi.mock("../../api/resume", () => ({ generateResumePreview: vi.fn() }));
beforeEach(() => vi.mocked(generateResumePreview).mockResolvedValue(coverLetterFixture()));
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.resetAllMocks(); });

it("gera somente ao clicar, para a candidatura escolhida, e conserva a edição ao fechar e reabrir", async () => {
  const user = userEvent.setup();
  render(<CoverLetterPanel applicationId="application-b" />);
  expect(generateResumePreview).not.toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: "Carta de Apresentação" }));
  const field = await screen.findByLabelText("Texto da carta — você pode editar");
  expect(generateResumePreview).toHaveBeenCalledExactlyOnceWith("application-b");
  expect((field as HTMLTextAreaElement).value).toContain("Empresa Exemplo");
  await user.clear(field);
  await user.type(field, "Carta ajustada pela pessoa.");
  await user.click(screen.getByRole("button", { name: "Fechar carta" }));
  expect(screen.queryByLabelText("Texto da carta — você pode editar")).toBeNull();
  await user.click(screen.getByRole("button", { name: "Carta de Apresentação" }));
  expect((screen.getByLabelText("Texto da carta — você pode editar") as HTMLTextAreaElement).value).toBe("Carta ajustada pela pessoa.");
  expect(generateResumePreview).toHaveBeenCalledTimes(1);
});

it("copia e exporta o texto revisado, reiniciando a revisão após edição", async () => {
  const user = userEvent.setup();
  const writeText = vi.spyOn(navigator.clipboard, "writeText");
  const doc = document.implementation.createHTMLDocument();
  const print = vi.fn();
  vi.spyOn(window, "open").mockReturnValue({document: doc, focus: vi.fn(), print, close: vi.fn()} as unknown as Window);
  render(<CoverLetterPanel applicationId="letter-test" />);
  await user.click(screen.getByRole("button", { name: "Carta de Apresentação" }));
  const field = await screen.findByLabelText("Texto da carta — você pode editar");
  const pdf = screen.getByRole("button", {name:"Salvar carta em PDF"}) as HTMLButtonElement;
  expect(pdf.disabled).toBe(true);
  await user.click(screen.getByRole("checkbox", {name: /Revisei a carta/}));
  expect(pdf.disabled).toBe(false);
  await user.clear(field);
  await user.type(field, 'Minha carta revisada. <script>alert("teste")</script>');
  expect(pdf.disabled).toBe(true);
  await user.click(screen.getByRole("checkbox", {name: /Revisei a carta/}));
  await user.click(screen.getByRole("button", {name:"Copiar carta"}));
  expect(writeText).toHaveBeenCalledWith(expect.stringContaining("Minha carta revisada."));
  await user.click(pdf);
  expect(print).toHaveBeenCalledOnce();
  expect(doc.title).toBe("Carta de Apresentação - Pessoa de Teste");
  expect(doc.body.textContent).toContain('Minha carta revisada. <script>alert("teste")</script>');
  expect(doc.querySelector("script")).toBeNull();
  expect(doc.body.textContent).not.toContain("Kubernetes");
  expect(doc.body.textContent).not.toContain("Revisei a carta");
});

it("informa erro de perfil ou requisitos e permite tentar novamente", async () => {
  const user = userEvent.setup();
  vi.mocked(generateResumePreview).mockRejectedValueOnce(new ApiError(400, {message:"Informe os requisitos da vaga."}));
  render(<CoverLetterPanel applicationId="letter-test" />);
  await user.click(screen.getByRole("button", {name:"Carta de Apresentação"}));
  expect((await screen.findByRole("alert")).textContent).toContain("Informe os requisitos");
  await user.click(screen.getByRole("button", {name:"Carta de Apresentação"}));
  expect(await screen.findByLabelText("Texto da carta — você pode editar")).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
});

it("busca o perfil atualizado ao gerar novamente e não compartilha a carta entre candidaturas", async () => {
  const user = userEvent.setup();
  render(<><CoverLetterPanel applicationId="a" /><CoverLetterPanel applicationId="b" /></>);
  await user.click(screen.getAllByRole("button", {name:"Carta de Apresentação"})[0]);
  await screen.findByLabelText("Texto da carta — você pode editar");
  const second = {...coverLetterFixture(), company:"Segunda Empresa", name:"Outro perfil de teste"};
  vi.mocked(generateResumePreview).mockResolvedValueOnce(second);
  await user.click(screen.getAllByRole("button", {name:"Carta de Apresentação"})[1]);
  await waitFor(() => expect(screen.getAllByLabelText("Texto da carta — você pode editar")).toHaveLength(2));
  const panels = screen.getAllByRole("region", {name:"Carta de Apresentação da candidatura"});
  expect((within(panels[0]).getByRole("textbox") as HTMLTextAreaElement).value).toContain("Empresa Exemplo");
  expect((within(panels[1]).getByRole("textbox") as HTMLTextAreaElement).value).toContain("Segunda Empresa");
  vi.mocked(generateResumePreview).mockResolvedValueOnce({...coverLetterFixture(), professional_summary:"Resumo profissional atualizado."});
  await user.click(within(panels[0]).getByRole("button", {name:"Gerar nova carta"}));
  await waitFor(() => expect((within(panels[0]).getByRole("textbox") as HTMLTextAreaElement).value).toContain("Resumo profissional atualizado."));
  expect(generateResumePreview).toHaveBeenNthCalledWith(1, "a");
  expect(generateResumePreview).toHaveBeenNthCalledWith(2, "b");
  expect(generateResumePreview).toHaveBeenNthCalledWith(3, "a");
});
