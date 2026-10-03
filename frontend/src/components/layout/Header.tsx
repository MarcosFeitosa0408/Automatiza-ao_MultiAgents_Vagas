type HeaderProps = {
  title: string;
  subtitle: string;
};

export default function Header({
  title,
  subtitle,
}: HeaderProps) {
  return (
    <header className="app-header">
      <div>
        <p className="app-header-eyebrow">PLATAFORMA MULTIAGENTE</p>
        <h1>{title}</h1>
        <p className="app-header-subtitle">{subtitle}</p>
      </div>

      <div className="app-header-user">
        <div className="app-header-avatar">U</div>

        <div>
          <strong>Área do candidato</strong>
          <span>Controle humano ativo</span>
        </div>
      </div>
    </header>
  );
}