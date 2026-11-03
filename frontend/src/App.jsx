import { BrowserRouter, Routes, Route } from "react-router-dom";
import MainLayout from "./components/layout/MainLayout";

import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Chat from "./pages/Chat";
import Workspaces from "./pages/Workspaces";
import Evaluations from "./pages/Evaluations";
import Settings from "./pages/Settings";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route element={<MainLayout />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/documents" element={<Documents />} />
                    <Route path="/chat" element={<Chat />} />
                    <Route path="/workspaces" element={<Workspaces />} />
                    <Route path="/evaluations" element={<Evaluations />} />
                    <Route path="/settings" element={<Settings />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;