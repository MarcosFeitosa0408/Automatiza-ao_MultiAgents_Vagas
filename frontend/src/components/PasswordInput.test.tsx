import { afterEach, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PasswordInput from "./PasswordInput";

afterEach(cleanup);

it("mostra, oculta e apaga somente a senha sem enviar o formulário", async () => {
  const user = userEvent.setup();
  let submitted = false;
  render(<form onSubmit={(event) => { event.preventDefault(); submitted = true; }}>
    <label htmlFor="test-password">Senha</label>
    <PasswordInput id="test-password" name="password" fieldLabel="senha" minLength={8} required />
  </form>);
  const input = screen.getByLabelText("Senha") as HTMLInputElement;
  await user.type(input, "Teste123");
  expect(input.type).toBe("password");
  await user.click(screen.getByRole("button", {name:"Mostrar senha"}));
  expect(input.type).toBe("text");
  expect(input.value).toBe("Teste123");
  await user.click(screen.getByRole("button", {name:"Ocultar senha"}));
  expect(input.type).toBe("password");
  await user.click(screen.getByRole("button", {name:"Apagar senha"}));
  expect(input.value).toBe("");
  expect(input.type).toBe("password");
  expect(submitted).toBe(false);
  expect(new FormData(input.form!).get("password")).toBe("");
});
