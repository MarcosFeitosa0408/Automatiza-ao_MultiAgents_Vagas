import { useRef, useState } from "react";
import type { ComponentProps } from "react";

type Props = Omit<ComponentProps<"input">, "type"> & { fieldLabel: string };

export default function PasswordInput({ fieldLabel, ...props }: Props) {
  const [visible, setVisible] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  return <div className="password-control">
    <input {...props} ref={input} type={visible ? "text" : "password"} />
    <button type="button" className="password-action" aria-label={`${visible ? "Ocultar" : "Mostrar"} ${fieldLabel}`} aria-pressed={visible} onClick={() => setVisible(!visible)}>
      <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
        <circle cx="12" cy="12" r="3" />
        {visible && <path d="M3 3 21 21" />}
      </svg>
    </button>
    <button type="button" className="password-action" aria-label={`Apagar ${fieldLabel}`} onClick={() => {
      if (input.current) {
        input.current.value = "";
        input.current.dispatchEvent(new Event("input", { bubbles: true }));
        input.current.focus();
      }
      setVisible(false);
    }}>Limpar</button>
  </div>;
}
