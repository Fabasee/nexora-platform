import {
  createContext,
  useContext,
  useEffect,
  useState,
  type PropsWithChildren,
} from "react";

import { firebaseAuthAdapter } from "../lib/firebase-auth-adapter";
import type {
  AuthMfaFactor,
  AuthUser,
  TotpEnrollmentDraft,
} from "../lib/auth-types";

type AuthStatus = "loading" | "signed-in" | "signed-out" | "unconfigured" | "error";

type AuthContextValue = {
  user: AuthUser | null;
  status: AuthStatus;
  signIn: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  sendVerificationEmail: () => Promise<void>;
  getMfaFactors: () => Promise<AuthMfaFactor[]>;
  beginTotpEnrollment: () => Promise<TotpEnrollmentDraft>;
  completeTotpEnrollment: (verificationCode: string, displayName?: string) => Promise<void>;
  completeTotpSignIn: (factorUid: string, verificationCode: string) => Promise<void>;
  removeMfaFactor: (factorUid: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    if (!firebaseAuthAdapter.isConfigured()) {
      setStatus("unconfigured");
      return;
    }

    try {
      return firebaseAuthAdapter.subscribe(
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
    await firebaseAuthAdapter.signIn(email, password);
  };

  const register = async (name: string, email: string, password: string) => {
    await firebaseAuthAdapter.register(name, email, password);
  };

  const resetPassword = async (email: string) => {
    await firebaseAuthAdapter.resetPassword(email);
  };

  const sendVerificationEmail = async () => {
    await firebaseAuthAdapter.sendVerificationEmail();
  };

  const getMfaFactors = async () => firebaseAuthAdapter.getMfaFactors();

  const beginTotpEnrollment = async () => firebaseAuthAdapter.beginTotpEnrollment();

  const completeTotpEnrollment = async (verificationCode: string, displayName?: string) => {
    await firebaseAuthAdapter.completeTotpEnrollment(verificationCode, displayName);
  };

  const completeTotpSignIn = async (factorUid: string, verificationCode: string) => {
    await firebaseAuthAdapter.completeTotpSignIn(factorUid, verificationCode);
  };

  const removeMfaFactor = async (factorUid: string) => {
    await firebaseAuthAdapter.removeMfaFactor(factorUid);
  };

  const signOut = async () => {
    await firebaseAuthAdapter.signOut();
  };

  return (
    <AuthContext.Provider value={{
      user,
      status,
      signIn,
      register,
      resetPassword,
      sendVerificationEmail,
      getMfaFactors,
      beginTotpEnrollment,
      completeTotpEnrollment,
      removeMfaFactor,
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
