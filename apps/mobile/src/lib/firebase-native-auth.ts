import { getApps } from "@react-native-firebase/app";
import {
  createUserWithEmailAndPassword,
  getAuth,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
  type User,
} from "@react-native-firebase/auth";

import type { AuthAdapter, AuthUser } from "./auth-types";

function toAuthUser(user: User): AuthUser {
  return {
    get uid() { return user.uid; },
    get email() { return user.email; },
    get emailVerified() { return user.emailVerified; },
    get displayName() { return user.displayName; },
    getIdToken: (forceRefresh = false) => user.getIdToken(forceRefresh),
    reload: () => user.reload(),
  };
}

function requireAuth() {
  if (getApps().length === 0) {
    throw new Error(
      "Native Firebase is not configured. Add the Firebase Android/iOS app configuration files and rebuild the development client.",
    );
  }
  return getAuth();
}

export const firebaseNativeAuthAdapter: AuthAdapter = {
  isConfigured() {
    return getApps().length > 0;
  },

  subscribe(onUser, onError) {
    return onAuthStateChanged(
      requireAuth(),
      (user) => onUser(user ? toAuthUser(user) : null),
      (error) => onError(error),
    );
  },

  async signIn(email, password) {
    const credential = await signInWithEmailAndPassword(
      requireAuth(),
      email.trim(),
      password,
    );
    return toAuthUser(credential.user);
  },

  async register(name, email, password) {
    const auth = requireAuth();
    const credential = await createUserWithEmailAndPassword(
      auth,
      email.trim(),
      password,
    );

    try {
      await updateProfile(credential.user, { displayName: name.trim() });
    } catch (error) {
      await signOut(auth);
      throw error;
    }

    try {
      await sendEmailVerification(credential.user);
    } catch {
      // Registration remains successful; the account screen can retry verification.
    }

    return toAuthUser(credential.user);
  },

  async resetPassword(email) {
    await sendPasswordResetEmail(requireAuth(), email.trim());
  },

  async sendVerificationEmail() {
    const user = requireAuth().currentUser;
    if (!user) throw new Error("No authenticated user is available.");
    await sendEmailVerification(user);
  },

  async signOut() {
    await signOut(requireAuth());
  },
};
