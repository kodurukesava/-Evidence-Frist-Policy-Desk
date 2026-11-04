
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../services/api";

function WorkspaceDetails() {
    const { workspaceId } = useParams();

    const [workspace, setWorkspace] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchWorkspace = async () => {
            try {
                const response = await api.get(
                    `/workspaces/${workspaceId}`
                );
                setWorkspace(response.data);
            } catch (err) {
                console.error("Workspace details error:", err);
                setError(
                    err.response?.data?.detail ||
                    "Unable to load workspace details."
                );
            } finally {
                setLoading(false);
            }
        };

        fetchWorkspace();
    }, [workspaceId]);

    if (loading) {
        return <div className="page-card">Loading workspace details...</div>;
    }

    if (error) {
        return (
            <div className="page-card">
                <h2>Error</h2>
                <p>{error}</p>
                <Link to="/workspaces">Back to Workspaces</Link>
            </div>
        );
    }

    if (!workspace) {
        return <div className="page-card">Workspace not found.</div>;
    }

    return (
        <div className="page-card">
            <Link to="/workspaces">← Back to Workspaces</Link>

            <h1>{workspace.name}</h1>
            <p>{workspace.description || "No description provided."}</p>

            <div className="stats">
                <div className="stat-card">
                    <h3>Workspace ID</h3>
                    <h2>{workspace.id}</h2>
                </div>

                <div className="stat-card">
                    <h3>Owner ID</h3>
                    <h2>{workspace.owner_id}</h2>
                </div>

                <div className="stat-card">
                    <h3>Documents</h3>
                    <h2>0</h2>
                </div>
            </div>

            <section>
                <h2>Workspace Information</h2>
                <p><strong>Name:</strong> {workspace.name}</p>
                <p>
                    <strong>Description:</strong>{" "}
                    {workspace.description || "Not provided"}
                </p>
                <p><strong>Workspace ID:</strong> {workspace.id}</p>
                <p><strong>Owner ID:</strong> {workspace.owner_id}</p>
                <p>
                    <strong>Created At:</strong>{" "}
                    {workspace.created_at
                        ? new Date(workspace.created_at).toLocaleString()
                        : "Not available"}
                </p>
            </section>

            <section>
                <h2>Documents</h2>
                <p>No documents have been added to this workspace yet.</p>
            </section>
        </div>
    );
}

export default WorkspaceDetails;
