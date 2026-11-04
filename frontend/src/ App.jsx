
import { BrowserRouter, Routes, Route } from "react-router-dom";

import MainLayout from "./components/layout/MainLayout";

import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Chat from "./pages/Chat";
import Workspaces from "./pages/Workspaces";
import WorkspaceDetails from "./pages/WorkspaceDetails";
import Evaluations from "./pages/Evaluations";
import Settings from "./pages/Settings";

import "./index.css";

function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Main Application Layout */}
                <Route element={<MainLayout />}>

                    {/* Dashboard */}
                    <Route
                        path="/"
                        element={<Dashboard />}
                    />

                    {/* Documents */}
                    <Route
                        path="/documents"
                        element={<Documents />}
                    />

                    {/* Chat */}
                    <Route
                        path="/chat"
                        element={<Chat />}
                    />

                    {/* Workspaces */}
                    <Route
                        path="/workspaces"
                        element={<Workspaces />}
                    />

                    {/* Individual Workspace Details */}
                    <Route
                        path="/workspaces/:workspaceId"
                        element={<WorkspaceDetails />}
                    />

                    {/* Evaluations */}
                    <Route
                        path="/evaluations"
                        element={<Evaluations />}
                    />

                    {/* Settings */}
                    <Route
                        path="/settings"
                        element={<Settings />}
                    />

                </Route>

                {/* 404 - Route Not Found */}
                <Route
                    path="*"
                    element={
                        <h1 style={{ textAlign: "center", marginTop: "100px" }}>
                            Route Not Found
                        </h1>
                    }
                />

            </Routes>
        </BrowserRouter>
    );
}

export default App;
