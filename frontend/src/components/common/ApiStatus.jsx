
import { useEffect, useState } from "react";
import api from "../../services/api";

function ApiStatus() {
    const [status, setStatus] = useState("Checking...");

    useEffect(() => {
        api.get("/health")
            .then((response) => {
                setStatus(response.data.status);
            })
            .catch(() => {
                setStatus("Disconnected");
            });
    }, []);

    return (
        <div className="status-card">
            <h3>Backend Connection</h3>
            <p>
                Status: <strong>{status}</strong>
            </p>
        </div>
    );
}

export default ApiStatus;
