import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
  type User,
} from "firebase/auth";

import { getFirebaseAuth, isFirebaseConfigured } from "./firebase";
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

function nativeMfaRequired(): never {
  throw new Error("TOTP management is currently available in the native Android/iOS app only.");
}

export const firebaseJsAuthAdapter: AuthAdapter = {
  isConfigured: isFirebaseConfigured,
  subscribe(onUser, onError) {
    return onAuthStateChanged(
      getFirebaseAuth(),
      (user) => onUser(user ? toAuthUser(user) : null),
      (error) => onError(error),
    );
  },

  async signIn(email, password) {
    const credential = await signInWithEmailAndPassword(
      getFirebaseAuth(),
      email.trim(),
      password,
    );
    return toAuthUser(credential.user);
  },

  async register(name, email, password) {
    const auth = getFirebaseAuth();
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
    await sendPasswordResetEmail(getFirebaseAuth(), email.trim());
  },

  async sendVerificationEmail() {
    const user = getFirebaseAuth().currentUser;
    if (!user) throw new Error("No authenticated user is available.");
    await sendEmailVerification(user);
  },

  async getMfaFactors() { return nativeMfaRequired(); },
  async beginTotpEnrollment() { return nativeMfaRequired(); },
  async completeTotpEnrollment() { return nativeMfaRequired(); },
  cancelTotpEnrollment() {},
  async completeTotpSignIn() { return nativeMfaRequired(); },
  cancelMfaSignInChallenge() {},
  async removeMfaFactor() { return nativeMfaRequired(); },

  async signOut() {
    await signOut(getFirebaseAuth());
  },
};
