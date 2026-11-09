
import { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

const SESSION_KEY = "auth_session";

function getSavedSession() {
    try {
        const saved = sessionStorage.getItem(SESSION_KEY);

        if (!saved) return null;

        const session = JSON.parse(saved);

        if (Date.now() >= session.expiresAt) {
            sessionStorage.removeItem(SESSION_KEY);
            return null;
        }

        return session;
    } catch {
        sessionStorage.removeItem(SESSION_KEY);
        return null;
    }
}

export function AuthProvider({ children }) {
    const [session, setSession] = useState(getSavedSession);

    const user = session?.user || null;
    const isAuthenticated = Boolean(session?.accessToken && user);

    useEffect(() => {
        if (!session) return;

        const remainingTime = session.expiresAt - Date.now();

        if (remainingTime <= 0) {
            logout();
            return;
        }

        const timer = setTimeout(logout, remainingTime);

        return () => clearTimeout(timer);
    }, [session]);

    async function register(fullName, email, password) {
        const response = await api.post("/auth/register", {
            full_name: fullName,
            email,
            password,
        });

        return response.data;
    }

    async function login(email, password) {
        const response = await api.post("/auth/login", {
            email,
            password,
        });

        const data = response.data;

        const newSession = {
            accessToken: data.access_token,
            user: data.user,
            expiresAt: Date.now() + data.expires_in * 1000,
        };

        sessionStorage.setItem(
            SESSION_KEY,
            JSON.stringify(newSession)
        );

        setSession(newSession);

        return data.user;
    }

    function logout() {
        sessionStorage.removeItem(SESSION_KEY);
        setSession(null);
    }

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated,
                register,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error("useAuth must be used inside AuthProvider");
    }

    return context;
}
