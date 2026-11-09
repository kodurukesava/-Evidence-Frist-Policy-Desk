
import { BrowserRouter, Routes, Route } from "react-router-dom";

import MainLayout from "./components/layout/MainLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute";

import Login from "./pages/Login";
import Register from "./pages/Register";

import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import DocumentSearch from "./pages/DocumentSearch";
import Chat from "./pages/Chat";
import Workspaces from "./pages/Workspaces";
import WorkspaceDetails from "./pages/WorkspaceDetails";
import Evaluations from "./pages/Evaluations";
import Settings from "./pages/Settings";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Public routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected application routes */}
                <Route element={<ProtectedRoute />}>
                    <Route element={<MainLayout />}>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/documents" element={<Documents />} />
                        <Route
                            path="/document-search"
                            element={<DocumentSearch />}
                        />
                        <Route path="/chat" element={<Chat />} />
                        <Route path="/workspaces" element={<Workspaces />} />
                        <Route
                            path="/workspaces/:workspaceId"
                            element={<WorkspaceDetails />}
                        />
                        <Route path="/evaluations" element={<Evaluations />} />
                        <Route path="/settings" element={<Settings />} />
                    </Route>
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
