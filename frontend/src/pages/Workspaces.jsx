
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Workspaces() {
    const [workspaces, setWorkspaces] = useState([]);
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");

    // Edit workspace state
    const [editingWorkspaceId, setEditingWorkspaceId] = useState(null);
    const [editName, setEditName] = useState("");
    const [editDescription, setEditDescription] = useState("");

    // Fetch all workspaces
    const fetchWorkspaces = async () => {
        try {
            setLoading(true);
            const response = await api.get("/workspaces/");
            setWorkspaces(response.data);
            setError("");
        } catch (err) {
            setError(
                "Unable to load workspaces. Check whether the backend is running."
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWorkspaces();
    }, []);

    // Create workspace
    const createWorkspace = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");

        if (name.trim().length < 3) {
            setError("Workspace name must contain at least 3 characters.");
            return;
        }

        try {
            await api.post("/workspaces/", {
                name: name.trim(),
                description: description.trim() || null,
            });

            setName("");
            setDescription("");
            setMessage("Workspace created successfully!");

            await fetchWorkspaces();
        } catch (err) {
            setError(
                err.response?.data?.detail || "Failed to create workspace."
            );
        }
    };

    // Start editing
    const startEditing = (workspace) => {
        setEditingWorkspaceId(workspace.id);
        setEditName(workspace.name);
        setEditDescription(workspace.description || "");
        setError("");
        setMessage("");
    };

    // Cancel editing
    const cancelEditing = () => {
        setEditingWorkspaceId(null);
        setEditName("");
        setEditDescription("");
    };

    // Update workspace
    const updateWorkspace = async (e, id) => {
        e.preventDefault();
        setError("");
        setMessage("");

        if (editName.trim().length < 3) {
            setError("Workspace name must contain at least 3 characters.");
            return;
        }

        try {
            await api.put(`/workspaces/${id}`, {
                name: editName.trim(),
                description: editDescription.trim() || null,
            });

            setMessage("Workspace updated successfully!");
            cancelEditing();
            await fetchWorkspaces();
        } catch (err) {
            setError(
                err.response?.data?.detail || "Failed to update workspace."
            );
        }
    };

    // Delete workspace
    const deleteWorkspace = async (id) => {
        if (!window.confirm("Are you sure you want to delete this workspace?")) {
            return;
        }

        setError("");
        setMessage("");

        try {
            await api.delete(`/workspaces/${id}`);
            setMessage("Workspace deleted successfully!");
            await fetchWorkspaces();
        } catch (err) {
            setError(
                err.response?.data?.detail || "Failed to delete workspace."
            );
        }
    };

    return (
        <div className="page-card">
            <h1>Workspaces</h1>
            <p>Organize documents into separate workspaces.</p>

            {/* Create Workspace Form */}
            <form onSubmit={createWorkspace}>
                <div>
                    <label>Workspace Name</label>
                    <input
                        type="text"
                        placeholder="Enter workspace name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>

                <div>
                    <label>Description</label>
                    <textarea
                        placeholder="Enter workspace description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>

                <button type="submit">Create Workspace</button>
            </form>

            {message && (
                <p style={{ color: "green" }}>{message}</p>
            )}

            {error && (
                <p style={{ color: "red" }}>{error}</p>
            )}

            <h2>Your Workspaces</h2>

            {loading ? (
                <p>Loading workspaces...</p>
            ) : workspaces.length === 0 ? (
                <p>No workspaces found. Create your first workspace.</p>
            ) : (
                <div>
                    {workspaces.map((workspace) => (
                        <div
                            key={workspace.id}
                            style={{
                                border: "1px solid #ddd",
                                padding: "16px",
                                marginBottom: "12px",
                                borderRadius: "8px",
                            }}
                        >
                            {editingWorkspaceId === workspace.id ? (
                                <form
                                    onSubmit={(e) =>
                                        updateWorkspace(e, workspace.id)
                                    }
                                >
                                    <h3>Edit Workspace</h3>

                                    <div>
                                        <label>Workspace Name</label>
                                        <input
                                            type="text"
                                            value={editName}
                                            onChange={(e) =>
                                                setEditName(e.target.value)
                                            }
                                            required
                                        />
                                    </div>

                                    <div>
                                        <label>Description</label>
                                        <textarea
                                            value={editDescription}
                                            onChange={(e) =>
                                                setEditDescription(e.target.value)
                                            }
                                        />
                                    </div>

                                    <button type="submit">
                                        Save Changes
                                    </button>

                                    <button
                                        type="button"
                                        onClick={cancelEditing}
                                    >
                                        Cancel
                                    </button>
                                </form>
                            ) : (
                                <>
                                    <h3>
                                        <Link
                                            to={`/workspaces/${workspace.id}`}
                                            style={{
                                                color: "#2563eb",
                                                textDecoration: "none",
                                            }}
                                        >
                                            {workspace.name}
                                        </Link>
                                    </h3>

                                    <p>
                                        {workspace.description ||
                                            "No description provided."}
                                    </p>

                                    <small>
                                        Workspace ID: {workspace.id}
                                    </small>

                                    <br />

                                    <button
                                        type="button"
                                        onClick={() =>
                                            startEditing(workspace)
                                        }
                                    >
                                        Edit
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            deleteWorkspace(workspace.id)
                                        }
                                    >
                                        Delete
                                    </button>
                                </>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default Workspaces;
