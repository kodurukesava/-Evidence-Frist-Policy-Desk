
import { NavLink } from "react-router-dom";
import {
    LayoutDashboard,
    FileText,
    MessageSquare,
    FolderKanban,
    ChartBar,
    Settings,
    ShieldCheck
} from "lucide-react";

function Sidebar() {
    const menuItems = [
        { name: "Dashboard", path: "/", icon: LayoutDashboard },
        { name: "Documents", path: "/documents", icon: FileText },
        { name: "AI Chat", path: "/chat", icon: MessageSquare },
        { name: "Workspaces", path: "/workspaces", icon: FolderKanban },
        { name: "Evaluations", path: "/evaluations", icon: ChartBar },
        { name: "Settings", path: "/settings", icon: Settings }
    ];

    return (
        <aside className="sidebar">
            <div className="brand">
                <ShieldCheck size={27} />
                <span>Evidence Desk</span>
            </div>

            <p className="menu-heading">WORKSPACE</p>

            <nav>
                {menuItems.map((item) => {
                    const Icon = item.icon;

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            end={item.path === "/"}
                            className={({ isActive }) =>
                                isActive ? "nav-item active" : "nav-item"
                            }
                        >
                            <Icon size={19} />
                            <span>{item.name}</span>
                        </NavLink>
                    );
                })}
            </nav>

            <div className="sidebar-footer">
                Evidence-First Policy Desk
                <p>Version 1.0.0</p>
            </div>
        </aside>
    );
}

export default Sidebar;
