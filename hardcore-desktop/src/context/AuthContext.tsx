import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
    id: string;
    email: string;
    name: string;
    picture?: string;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: () => Promise<void>;
    logout: () => Promise<void>;
    bypassAuth: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        try {
            const storedUser = localStorage.getItem('hc_user');
            if (storedUser) {
                setUser(JSON.parse(storedUser));
            }
        } catch (error) {
            console.error('Auth check failed:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const login = async () => {
        setIsLoading(true);
        try {
            const demoUser: User = {
                id: 'demo_' + Date.now(),
                email: 'demo@hardcore.ai',
                name: 'Demo User',
            };
            setUser(demoUser);
            localStorage.setItem('hc_user', JSON.stringify(demoUser));
        } catch (error) {
            console.error('Login failed:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const logout = async () => {
        setUser(null);
        localStorage.removeItem('hc_user');
    };

    const bypassAuth = () => {
        const bypassUser: User = {
            id: 'dev_bypass',
            email: 'dev@local',
            name: 'Developer',
        };
        setUser(bypassUser);
        localStorage.setItem('hc_user', JSON.stringify(bypassUser));
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isAuthenticated: !!user,
                isLoading,
                login,
                logout,
                bypassAuth,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}
