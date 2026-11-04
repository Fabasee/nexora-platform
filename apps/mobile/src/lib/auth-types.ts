export type AuthUser = {
  uid: string;
  email: string | null;
  emailVerified: boolean;
  displayName: string | null;
  getIdToken: (forceRefresh?: boolean) => Promise<string>;
  reload: () => Promise<void>;
};

export type AuthUnsubscribe = () => void;

export type AuthMfaFactor = {
  uid: string;
  factorId: "totp" | "phone" | string;
  displayName: string | null;
  enrollmentTime: string | null;
};

export type TotpEnrollmentDraft = {
  secretKey: string;
  otpauthUrl: string;
};

export type AuthAdapter = {
  isConfigured: () => boolean;
  subscribe: (
    onUser: (user: AuthUser | null) => void,
    onError: (error: Error) => void,
  ) => AuthUnsubscribe;
  signIn: (email: string, password: string) => Promise<AuthUser>;
  register: (name: string, email: string, password: string) => Promise<AuthUser>;
  resetPassword: (email: string) => Promise<void>;
  sendVerificationEmail: () => Promise<void>;
  getMfaFactors: () => Promise<AuthMfaFactor[]>;
  beginTotpEnrollment: () => Promise<TotpEnrollmentDraft>;
  completeTotpEnrollment: (verificationCode: string, displayName?: string) => Promise<void>;
  removeMfaFactor: (factorUid: string) => Promise<void>;
  signOut: () => Promise<void>;
};
