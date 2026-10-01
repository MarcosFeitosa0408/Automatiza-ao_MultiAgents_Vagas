export type NavigationPage =
  | "dashboard"
  | "applications"
  | "new-application";

type SidebarProps = {
  activePage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
};

const sidebarItems: {
  page: NavigationPage;
  label: string;
  icon: string;
}[] = [
  { page: "dashboard", label: "Dashboard", icon: "D" },
  { page: "applications", label: "Candidaturas", icon: "C" },
  { page: "new-application", label: "Nova candidatura", icon: "+" },
];

export default function Sidebar({
  activePage,
  onNavigate,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">M</div>
        <div>
          <strong>MultiAgents</strong>
          <span>Vagas</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Navegação principal">
        {sidebarItems.map((item) => (
          <button
            className={`sidebar-item${
              activePage === item.page ? " active" : ""
            }`}
            key={item.page}
            type="button"
            aria-current={activePage === item.page ? "page" : undefined}
            onClick={() => onNavigate(item.page)}
          >
            <span className="sidebar-item-icon" aria-hidden="true">
              {item.icon}
            </span>
            <span>{item.label}</span>
          </button>
        ))}

        <button
          className="sidebar-item"
          type="button"
          disabled
          title="Formulário disponível na próxima etapa"
        >
          <span className="sidebar-item-icon" aria-hidden="true">+</span>
          <span>Nova candidatura · em breve</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span>Revisão humana obrigatória</span>
        </div>
        <small>Automação + Inteligência</small>
      </div>
    </aside>
  );
}