import {
  createUserWithEmailAndPassword,
  getMultiFactorResolver,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  TotpMultiFactorGenerator,
  updateProfile,
  type MultiFactorError,
  type MultiFactorResolver,
  type User,
} from "firebase/auth";

import { getFirebaseAuth, isFirebaseConfigured } from "./firebase";
import { MfaChallengeRequiredError } from "./auth-types";
import type { AuthAdapter, AuthMfaFactor, AuthUser } from "./auth-types";

let pendingSignInResolver: MultiFactorResolver | null = null;

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
  throw new Error("TOTP enrollment and factor management are currently available in the native Android/iOS app only.");
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
    const auth = getFirebaseAuth();
    pendingSignInResolver = null;
    try {
      const credential = await signInWithEmailAndPassword(
        auth,
        email.trim(),
        password,
      );
      return toAuthUser(credential.user);
    } catch (error) {
      if ((error as { code?: string })?.code !== "auth/multi-factor-auth-required") {
        throw error;
      }

      const resolver = getMultiFactorResolver(auth, error as MultiFactorError);
      pendingSignInResolver = resolver;
      const factors: AuthMfaFactor[] = resolver.hints.map((hint) => ({
        uid: hint.uid,
        factorId: hint.factorId,
        displayName: hint.displayName ?? null,
        enrollmentTime: hint.enrollmentTime ?? null,
      }));
      throw new MfaChallengeRequiredError(factors);
    }
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

  async completeTotpSignIn(factorUid, verificationCode) {
    const resolver = pendingSignInResolver;
    if (!resolver) throw new Error("MFA_SIGN_IN_CHALLENGE_EXPIRED");

    const factor = resolver.hints.find(
      (hint) => hint.uid === factorUid && hint.factorId === "totp",
    );
    if (!factor) throw new Error("MFA_FACTOR_NOT_FOUND");

    const normalizedCode = verificationCode.replace(/\\s+/g, "");
    if (!/^\\d{6}$/.test(normalizedCode)) throw new Error("INVALID_TOTP_CODE");

    const assertion = TotpMultiFactorGenerator.assertionForSignIn(
      factor.uid,
      normalizedCode,
    );
    const credential = await resolver.resolveSignIn(assertion);
    pendingSignInResolver = null;
    await credential.user.getIdToken(true);
  },

  cancelMfaSignInChallenge() {
    pendingSignInResolver = null;
  },

  async removeMfaFactor() { return nativeMfaRequired(); },

  async signOut() {
    pendingSignInResolver = null;
    await signOut(getFirebaseAuth());
  },
};
