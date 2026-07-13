import React from "react";
import { createRoot } from "react-dom/client";
import { Activity, Database, MessageCircle, Settings } from "lucide-react";
import { getHealth } from "./api";
import ChatPage from "./pages/ChatPage";
import CasesPage from "./pages/CasesPage";
import "./styles.css";

const routes = [
  { path: "/", label: "AI 问诊", icon: MessageCircle },
  { path: "/cases", label: "病例库", icon: Database },
];

function useRoute() {
  const [path, setPath] = React.useState(window.location.pathname);

  React.useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = (nextPath) => {
    window.history.pushState({}, "", nextPath);
    setPath(nextPath);
  };

  return { path, navigate };
}

function App() {
  const { path, navigate } = useRoute();
  const [health, setHealth] = React.useState(null);

  React.useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  const currentRoute = routes.find((item) => item.path === path) || routes[0];
  const Page = currentRoute.path === "/cases" ? CasesPage : ChatPage;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI Hospital</p>
          <h1>{currentRoute.label}</h1>
        </div>
        <div className="status-strip" aria-label="运行状态">
          <span className={health?.has_api_key ? "dot ok" : "dot warn"} />
          <span>{health?.model || "模型未连接"}</span>
          <span className="divider" />
          <Activity size={16} />
          <span>{health?.case_count ?? "--"} 病例</span>
        </div>
      </header>

      <main className="page-frame">
        <Page health={health} />
      </main>

      <nav className="bottom-nav" aria-label="主导航">
        {routes.map((route) => {
          const Icon = route.icon;
          const active = currentRoute.path === route.path;
          return (
            <button
              key={route.path}
              className={active ? "nav-item active" : "nav-item"}
              onClick={() => navigate(route.path)}
              title={route.label}
              type="button"
            >
              <Icon size={20} />
              <span>{route.label}</span>
            </button>
          );
        })}
        <button className="nav-item muted" type="button" title="配置从后端环境变量读取">
          <Settings size={20} />
          <span>配置</span>
        </button>
      </nav>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
