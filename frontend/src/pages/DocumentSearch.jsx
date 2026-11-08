
import { useState } from "react";
import api from "../services/api";

function DocumentSearch() {
    const [workspaceId, setWorkspaceId] = useState("1");
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [searched, setSearched] = useState(false);

    const handleSearch = async (e) => {
        e.preventDefault();

        if (!query.trim()) {
            setError("Please enter a search query.");
            return;
        }

        setLoading(true);
        setError("");
        setSearched(false);
        setResults([]);

        try {
            const response = await api.get(
                `/documents/search/${workspaceId}`,
                {
                    params: {
                        query: query.trim(),
                        limit: 10,
                    },
                }
            );

            setResults(response.data.results);
            setSearched(true);
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                "Unable to search documents. Please try again."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <h1>Document Search</h1>
            <p>Search for evidence across your workspace documents.</p>

            <form onSubmit={handleSearch}>
                <div>
                    <label>Workspace ID</label>
                    <input
                        type="number"
                        min="1"
                        value={workspaceId}
                        onChange={(e) => setWorkspaceId(e.target.value)}
                    />
                </div>

                <div>
                    <label>Search Query</label>
                    <input
                        type="text"
                        placeholder="e.g. Attendance Policy"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                </div>

                <button type="submit" disabled={loading}>
                    {loading ? "Searching..." : "Search Documents"}
                </button>
            </form>

            {error && <p className="error-message">{error}</p>}

            {searched && (
                <div className="search-results">
                    <h2>Search Results ({results.length})</h2>

                    {results.length === 0 ? (
                        <p>No matching documents found.</p>
                    ) : (
                        results.map((result) => (
                            <div
                                key={result.segment_id}
                                className="document-result-card"
                            >
                                <h3>{result.document_name}</h3>

                                <p>
                                    Document ID: {result.document_id}
                                </p>

                                <p>
                                    Segment ID: {result.segment_id}
                                </p>

                                <p>
                                    Version ID: {result.version_id}
                                </p>

                                <p>
                                    Relevance: {result.relevance_score.toFixed(8)}
                                </p>

                                <div className="result-content">
                                    {result.content}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}

export default DocumentSearch;
