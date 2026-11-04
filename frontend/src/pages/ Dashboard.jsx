
import { useEffect, useState } from "react";
import ApiStatus from "../components/common/ApiStatus";
import api from "../services/api";

function Dashboard() {
    const [workspaces, setWorkspaces] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const response = await api.get("/workspaces/");
                setWorkspaces(response.data);
            } catch (err) {
                console.error(err);
                setError("Unable to load workspaces.");
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    return (
        <div className="dashboard">
            <header>
                <h1>Evidence-First Policy Desk</h1>
                <p>
                    Evidence-grounded multi-document
                    AI question answering platform.
                </p>
            </header>

            <section className="stats">
                <div className="stat-card">
                    <h3>Documents</h3>
                    <h2>0</h2>
                    <p>Uploaded documents</p>
                </div>

                <div className="stat-card">
                    <h3>Questions</h3>
                    <h2>0</h2>
                    <p>Questions answered</p>
                </div>

                <div className="stat-card">
                    <h3>Workspaces</h3>
                    <h2>{loading ? "..." : workspaces.length}</h2>
                    <p>Active workspaces</p>
                </div>
            </section>

            <ApiStatus />

            <section className="welcome-card">
                <h2>Welcome to your workspace</h2>
                <p>
                    Upload documents, search for evidence
                    and receive answers supported by
                    verified document passages.
                </p>
            </section>

            <section className="recent-workspaces">
                <h2>Recent Workspaces</h2>

                {loading ? (
                    <p>Loading workspaces...</p>
                ) : error ? (
                    <p>{error}</p>
                ) : workspaces.length === 0 ? (
                    <p>No workspaces found.</p>
                ) : (
                    workspaces.map((workspace) => (
                        <div className="stat-card" key={workspace.id}>
                            <h3>{workspace.name}</h3>
                            <p>{workspace.description}</p>
                            <small>Workspace ID: {workspace.id}</small>
                        </div>
                    ))
                )}
            </section>
        </div>
    );
}

export default Dashboard;
