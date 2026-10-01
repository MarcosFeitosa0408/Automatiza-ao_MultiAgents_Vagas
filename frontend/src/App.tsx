import MainLayout from "./components/layout/MainLayout";
import Dashboard from "./components/dashboard/Dashboard";

function App() {
  return (
    <MainLayout
      title="Dashboard"
      subtitle="Acompanhe sua operação de candidaturas com inteligência e controle."
    >
      <Dashboard />
    </MainLayout>
  );
}

export default App;