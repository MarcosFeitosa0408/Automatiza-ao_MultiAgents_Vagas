import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./Platform";

vi.mock("./components/dashboard/Dashboard", () => ({
  default: () => <p>Conteúdo do dashboard</p>,
}));

vi.mock("./pages/Applications/Applications", () => ({
  default: () => <p>Conteúdo das candidaturas</p>,
}));

describe("Navegação da plataforma", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/");
  });

  afterEach(() => {
    cleanup();
    window.history.replaceState(null, "", "/");
  });

  it("abre o dashboard como página inicial", () => {
    render(<App />);

    expect(screen.getByText("Conteúdo do dashboard")).toBeTruthy();

    expect(
      screen
        .getByRole("button", { name: "Dashboard" })
        .getAttribute("aria-current"),
    ).toBe("page");
  });

  it("navega para candidaturas e retorna ao dashboard", async () => {
    const user = userEvent.setup();

    render(<App />);

    await user.click(
      screen.getByRole("button", { name: "Candidaturas" }),
    );

    expect(
      await screen.findByText("Conteúdo das candidaturas"),
    ).toBeTruthy();

    expect(window.location.hash).toBe("#/candidaturas");

    expect(
      screen
        .getByRole("button", { name: "Candidaturas" })
        .getAttribute("aria-current"),
    ).toBe("page");

    await user.click(
      screen.getByRole("button", { name: "Dashboard" }),
    );

    await waitFor(() => {
      expect(screen.getByText("Conteúdo do dashboard")).toBeTruthy();
    });

    expect(window.location.hash).toBe("#/dashboard");
  });

  it("abre candidaturas diretamente pelo endereço", () => {
    window.history.replaceState(null, "", "/#/candidaturas");

    render(<App />);

    expect(screen.getByText("Conteúdo das candidaturas")).toBeTruthy();
  });

  it("abre o formulário pelo menu Nova candidatura", async () => {
  const user = userEvent.setup();

  render(<App />);

  await user.click(
    screen.getByRole("button", { name: "Nova candidatura" }),
  );

  expect(
    await screen.findByRole("heading", {
      name: "Cadastrar oportunidade",
    }),
  ).toBeTruthy();

  expect(window.location.hash).toBe("#/nova-candidatura");

  expect(
    screen
      .getByRole("button", { name: "Nova candidatura" })
      .getAttribute("aria-current"),
  ).toBe("page");
});
});