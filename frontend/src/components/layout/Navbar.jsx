
import { Bell, Search } from "lucide-react";

function Navbar() {
    return (
        <header className="navbar">
            <div>
                <h3>Document Intelligence Platform</h3>
                <p>Evidence-grounded AI workspace</p>
            </div>

            <div className="navbar-actions">
                <button aria-label="Search">
                    <Search size={19} />
                </button>

                <button aria-label="Notifications">
                    <Bell size={19} />
                </button>

                <div className="profile">
                    KK
                </div>
            </div>
        </header>
    );
}

export default Navbar;
