import {
  createContext,
  useContext,
  useEffect,
  useState,
  type PropsWithChildren,
} from "react";

import { isFirebaseConfigured } from "../lib/firebase";
import { firebaseJsAuthAdapter } from "../lib/firebase-js-auth";
import type { AuthUser } from "../lib/auth-types";

type AuthStatus = "loading" | "signed-in" | "signed-out" | "unconfigured" | "error";

type AuthContextValue = {
  user: AuthUser | null;
  status: AuthStatus;
  signIn: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  sendVerificationEmail: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    if (!isFirebaseConfigured()) {
      setStatus("unconfigured");
      return;
    }

    try {
      return firebaseJsAuthAdapter.subscribe(
        (nextUser) => {
          setUser(nextUser);
          setStatus(nextUser ? "signed-in" : "signed-out");
        },
        () => {
          setUser(null);
          setStatus("error");
        },
      );
    } catch {
      setUser(null);
      setStatus("error");
    }
  }, []);

  const signIn = async (email: string, password: string) => {
    await firebaseJsAuthAdapter.signIn(email, password);
  };

  const register = async (name: string, email: string, password: string) => {
    await firebaseJsAuthAdapter.register(name, email, password);
  };

  const resetPassword = async (email: string) => {
    await firebaseJsAuthAdapter.resetPassword(email);
  };

  const sendVerificationEmail = async () => {
    await firebaseJsAuthAdapter.sendVerificationEmail();
  };

  const signOut = async () => {
    await firebaseJsAuthAdapter.signOut();
  };

  return (
    <AuthContext.Provider value={{
      user,
      status,
      signIn,
      register,
      resetPassword,
      sendVerificationEmail,
      signOut,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
