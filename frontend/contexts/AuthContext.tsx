'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '@/lib/api-client';

interface AuthContextType {
  user: string | null;
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for token in localStorage on mount
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        setToken(storedToken);
        // Verify token by fetching user info
        authApi
          .getMe()
          .then((username) => {
            setUser(username);
          })
          .catch(() => {
            // Token invalid, remove it
            localStorage.removeItem('token');
            setToken(null);
          })
          .finally(() => {
            setLoading(false);
          });
      } else {
        setLoading(false);
      }
    }
  }, []);

  const login = async (username: string, password: string) => {
    const response = await authApi.login({ username, password });
    const accessToken = response.access_token;
    localStorage.setItem('token', accessToken);
    setToken(accessToken);
    setUser(username);
  };

  const register = async (username: string, password: string) => {
    await authApi.register({ username, password });
    // Auto-login after registration
    await login(username, password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        logout,
        isAuthenticated: !!token,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

