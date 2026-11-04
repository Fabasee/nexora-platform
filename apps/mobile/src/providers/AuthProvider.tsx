import {
  createContext,
  useContext,
  useEffect,
  useState,
  type PropsWithChildren,
} from "react";
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  updateProfile,
  type User,
} from "firebase/auth";

import { getFirebaseAuth, isFirebaseConfigured } from "../lib/firebase";

type AuthStatus = "loading" | "signed-in" | "signed-out" | "unconfigured" | "error";

type AuthContextValue = {
  user: User | null;
  status: AuthStatus;
  signIn: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  sendVerificationEmail: () => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    if (!isFirebaseConfigured()) {
      setStatus("unconfigured");
      return;
    }

    try {
      return onAuthStateChanged(
        getFirebaseAuth(),
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
    await signInWithEmailAndPassword(getFirebaseAuth(), email.trim(), password);
  };

  const register = async (name: string, email: string, password: string) => {
    const credential = await createUserWithEmailAndPassword(
      getFirebaseAuth(),
      email.trim(),
      password,
    );
    try {
      await updateProfile(credential.user, { displayName: name.trim() });
    } catch (error) {
      await firebaseSignOut(getFirebaseAuth());
      throw error;
    }

    // Account creation must not be rolled back just because the mail provider is
    // temporarily unavailable; the signed-in account can request another link.
    try {
      await sendEmailVerification(credential.user);
    } catch {
      // The account screen exposes a retry action for unverified addresses.
    }
  };

  const resetPassword = async (email: string) => {
    await sendPasswordResetEmail(getFirebaseAuth(), email.trim());
  };

  const sendVerificationEmail = async () => {
    const currentUser = getFirebaseAuth().currentUser;
    if (!currentUser) throw new Error("No authenticated user is available.");
    await sendEmailVerification(currentUser);
  };

  const signOut = async () => {
    await firebaseSignOut(getFirebaseAuth());
  };

  return (
    <AuthContext.Provider value={{ user, status, signIn, register, resetPassword, sendVerificationEmail, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
