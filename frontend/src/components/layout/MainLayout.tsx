import type { ReactNode } from "react";
import Sidebar from "./Sidebar";
import type { NavigationPage } from "./Sidebar";
import Header from "./Header";

type MainLayoutProps = {
  children: ReactNode;
  title: string;
  subtitle: string;
  activePage: NavigationPage;
  onNavigate: (page: NavigationPage) => void;
};

export default function MainLayout({
  children,
  title,
  subtitle,
  activePage,
  onNavigate,
}: MainLayoutProps) {
  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />
      <div className="app-content">
        <Header title={title} subtitle={subtitle} />
        <main className="app-main">{children}</main>
      </div>
    </div>
  );
}