
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar.jsx";

function MainLayout() {
    return (
        <div className="app-layout">
            <Sidebar />
            <div className="main-section">
                <Navbar />
                <main className="page-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

export default MainLayout;
