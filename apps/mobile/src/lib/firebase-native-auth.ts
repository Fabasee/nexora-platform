import { getApps } from "@react-native-firebase/app";
import {
  createUserWithEmailAndPassword,
  getAuth,
  getMultiFactorResolver,
  multiFactor,
  onAuthStateChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  TotpMultiFactorGenerator,
  updateProfile,
  type MultiFactorError,
  type MultiFactorInfo,
  type MultiFactorResolver,
  type TotpSecret,
  type User,
} from "@react-native-firebase/auth";

import { MfaChallengeRequiredError } from "./auth-types";

import type {
  AuthAdapter,
  AuthMfaFactor,
  AuthUser,
  TotpEnrollmentDraft,
} from "./auth-types";

type PendingTotpEnrollment = {
  userUid: string;
  secret: TotpSecret;
};

let pendingTotpEnrollment: PendingTotpEnrollment | null = null;
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

function requireAuth() {
  if (getApps().length === 0) {
    throw new Error(
      "Native Firebase is not configured. Add the Firebase Android/iOS app configuration files and rebuild the development client.",
    );
  }
  return getAuth();
}

function requireCurrentUser() {
  const user = requireAuth().currentUser;
  if (!user) throw new Error("A signed-in Firebase user is required.");
  return user;
}

function toMfaFactor(factor: MultiFactorInfo): AuthMfaFactor {
  return {
    uid: factor.uid,
    factorId: factor.factorId,
    displayName: factor.displayName ?? null,
    enrollmentTime: factor.enrollmentTime ?? null,
  };
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
    const auth = requireAuth();
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
      const factors = resolver.hints.map((hint) => ({
        uid: hint.uid,
        factorId: hint.factorId,
        displayName: hint.displayName ?? null,
        enrollmentTime: hint.enrollmentTime ?? null,
      }));
      throw new MfaChallengeRequiredError(factors);
    }
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
    const user = requireCurrentUser();
    await sendEmailVerification(user);
  },

  async getMfaFactors() {
    const user = requireCurrentUser();
    return multiFactor(user).enrolledFactors.map(toMfaFactor);
  },

  async beginTotpEnrollment(): Promise<TotpEnrollmentDraft> {
    const auth = requireAuth();
    const user = requireCurrentUser();
    await user.reload();
    if (!user.emailVerified) {
      throw new Error("VERIFIED_EMAIL_REQUIRED");
    }

    const session = await multiFactor(user).getSession();
    const secret = await TotpMultiFactorGenerator.generateSecret(session, auth);
    pendingTotpEnrollment = { userUid: user.uid, secret };

    return {
      secretKey: secret.secretKey,
      otpauthUrl: secret.generateQrCodeUrl(user.email ?? user.uid, "Nexora"),
    };
  },

  async completeTotpEnrollment(verificationCode, displayName = "Nexora authenticator") {
    const user = requireCurrentUser();
    const pending = pendingTotpEnrollment;
    if (!pending || pending.userUid !== user.uid) {
      throw new Error("TOTP_ENROLLMENT_EXPIRED");
    }

    const normalizedCode = verificationCode.replace(/\s+/g, "");
    if (!/^\d{6}$/.test(normalizedCode)) {
      throw new Error("INVALID_TOTP_CODE");
    }

    const assertion = TotpMultiFactorGenerator.assertionForEnrollment(
      pending.secret,
      normalizedCode,
    );
    await multiFactor(user).enroll(assertion, displayName.trim() || "Nexora authenticator");
    pendingTotpEnrollment = null;
    await user.getIdToken(true);
  },

  async completeTotpSignIn(factorUid, verificationCode) {
    const auth = requireAuth();
    const resolver = pendingSignInResolver;
    if (!resolver) throw new Error("MFA_SIGN_IN_CHALLENGE_EXPIRED");

    const factor = resolver.hints.find((hint) => hint.uid === factorUid && hint.factorId === "totp");
    if (!factor) throw new Error("MFA_FACTOR_NOT_FOUND");

    const normalizedCode = verificationCode.replace(/\\s+/g, "");
    if (!/^\\d{6}$/.test(normalizedCode)) throw new Error("INVALID_TOTP_CODE");

    const assertion = TotpMultiFactorGenerator.assertionForSignIn(factor.uid, normalizedCode);
    const credential = await resolver.resolveSignIn(assertion);
    pendingSignInResolver = null;
    await credential.user.getIdToken(true);
  },

  async removeMfaFactor(factorUid) {
    const user = requireCurrentUser();
    const factor = multiFactor(user).enrolledFactors.find((item) => item.uid === factorUid);
    if (!factor) throw new Error("MFA_FACTOR_NOT_FOUND");
    await multiFactor(user).unenroll(factor);
    if (pendingTotpEnrollment?.userUid === user.uid) pendingTotpEnrollment = null;
  },

  async signOut() {
    pendingTotpEnrollment = null;
    await signOut(requireAuth());
  },
};
