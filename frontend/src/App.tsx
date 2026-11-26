
import Sidebar from "./components/layout/Sidebar";
import Header from "./components/layout/Header";
import PolicyAnalysisPage from "./features/policy-analysis/pages/PolicyAnalysisPage";

function App() {
  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content">
        <Header />
        <PolicyAnalysisPage />
      </main>
    </div>
  );
}

export default App;
