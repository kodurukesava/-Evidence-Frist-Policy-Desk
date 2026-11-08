
import {
    LayoutDashboard,
    FileText,
    Search,
    MessageSquare,
    FolderKanban,
    ClipboardCheck,
    Settings,
} from "lucide-react";

import { NavLink } from "react-router-dom";

function Sidebar() {
    const menuItems = [
        {
            name: "Dashboard",
            path: "/",
            icon: LayoutDashboard,
        },
        {
            name: "Documents",
            path: "/documents",
            icon: FileText,
        },
        {
            name: "Document Search",
            path: "/document-search",
            icon: Search,
        },
        {
            name: "Chat",
            path: "/chat",
            icon: MessageSquare,
        },
        {
            name: "Workspaces",
            path: "/workspaces",
            icon: FolderKanban,
        },
        {
            name: "Evaluations",
            path: "/evaluations",
            icon: ClipboardCheck,
        },
        {
            name: "Settings",
            path: "/settings",
            icon: Settings,
        },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <h2>Evidence Desk</h2>
                <p>Policy Intelligence</p>
            </div>

            <nav className="sidebar-nav">
                {menuItems.map((item) => {
                    const Icon = item.icon;

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            end={item.path === "/"}
                            className={({ isActive }) =>
                                `nav-link ${isActive ? "active" : ""}`
                            }
                        >
                            <Icon size={20} />
                            <span>{item.name}</span>
                        </NavLink>
                    );
                })}
            </nav>

            <div className="sidebar-footer">
                <p>Evidence-First Policy Desk</p>
                <span>Version 1.0</span>
            </div>
        </aside>
    );
}

export default Sidebar;
