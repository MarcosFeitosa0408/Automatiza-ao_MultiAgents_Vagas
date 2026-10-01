type SidebarItem = {
  label: string;
  icon: string;
};

const sidebarItems: SidebarItem[] = [
  { label: "Dashboard", icon: "⌂" },
  { label: "Candidaturas", icon: "▣" },
  { label: "Nova candidatura", icon: "+" },
];

export default function Sidebar() {
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
        {sidebarItems.map((item, index) => (
          <button
            className={`sidebar-item${index === 0 ? " active" : ""}`}
            key={item.label}
            type="button"
          >
            <span className="sidebar-item-icon" aria-hidden="true">
              {item.icon}
            </span>

            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className="sidebar-status-dot" />
          <span>API conectada</span>
        </div>

        <small>Automação + Inteligência</small>
      </div>
    </aside>
  );
}