
import ApiStatus from "../components/common/ApiStatus";

function Dashboard() {
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
                    <h2>0</h2>
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
        </div>
    );
}

export default Dashboard;
