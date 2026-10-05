import { afterEach, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PlatformGuide from "./PlatformGuide";

afterEach(cleanup);

it("abre e fecha as instruções com o mesmo botão", async () => {
  const user = userEvent.setup();
  render(<PlatformGuide />);
  const button = screen.getByRole("button", { name: "Como usar a plataforma" });
  expect(button.getAttribute("aria-expanded")).toBe("false");
  expect(screen.queryByRole("heading", { name: "Seu passo a passo" })).toBeNull();
  await user.click(button);
  expect(button.getAttribute("aria-expanded")).toBe("true");
  expect(screen.getByRole("heading", { name: "Seu passo a passo" })).toBeTruthy();
  expect(screen.getAllByRole("listitem")).toHaveLength(7);
  expect(screen.getByText(/não envia uma candidatura à empresa/)).toBeTruthy();
  await user.click(button);
  expect(button.getAttribute("aria-expanded")).toBe("false");
  expect(screen.queryByRole("heading", { name: "Seu passo a passo" })).toBeNull();
});
