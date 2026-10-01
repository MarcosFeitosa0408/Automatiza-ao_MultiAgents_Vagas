import type { ReactNode } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

type MainLayoutProps = {
  children: ReactNode;
  title: string;
  subtitle: string;
};

export default function MainLayout({
  children,
  title,
  subtitle,
}: MainLayoutProps) {
  return (
    <div className="app-shell">
      <Sidebar />

      <div className="app-content">
        <Header title={title} subtitle={subtitle} />

        <main className="app-main">{children}</main>
      </div>
    </div>
  );
}