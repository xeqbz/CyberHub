"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getCurrentUser, type CurrentUser } from "@/src/shared/api/users";
import { clearTokens, getAccessToken } from "@/src/shared/lib/auth";

type CurrentUserContextValue = {
  user: CurrentUser | null;
  isLoading: boolean;
  error: string;
  isAuthenticated: boolean;
  refreshUser: () => Promise<void>;
  clearUser: () => void;
};

const CurrentUserContext = createContext<CurrentUserContextValue | undefined>(
  undefined,
);

type CurrentUserProviderProps = {
  children: React.ReactNode;
};

export default function CurrentUserProvider({
  children,
}: CurrentUserProviderProps) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadUser = useCallback(async () => {
    const token = getAccessToken();

    if (!token) {
      setUser(null);
      setError("");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError("");

      const data = await getCurrentUser(token);
      setUser(data);
    } catch (err) {
      setUser(null);
      clearTokens();
      setError(err instanceof Error ? err.message : "Failed to load current user");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadUser();
  }, [loadUser]);

  const refreshUser = useCallback(async () => {
    await loadUser();
  }, [loadUser]);

  const clearUser = useCallback(() => {
    setUser(null);
    setError("");
  }, []);

  const value = useMemo<CurrentUserContextValue>(
    () => ({
      user,
      isLoading,
      error,
      isAuthenticated: Boolean(user),
      refreshUser,
      clearUser,
    }),
    [user, isLoading, error, refreshUser, clearUser],
  );

  return (
    <CurrentUserContext.Provider value={value}>
      {children}
    </CurrentUserContext.Provider>
  );
}

export function useCurrentUserContext(): CurrentUserContextValue {
  const context = useContext(CurrentUserContext);

  if (!context) {
    throw new Error(
      "useCurrentUserContext must be used within CurrentUserProvider",
    );
  }

  return context;
}