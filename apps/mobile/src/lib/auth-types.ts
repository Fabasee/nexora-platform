export type AuthUser = {
  uid: string;
  email: string | null;
  emailVerified: boolean;
  displayName: string | null;
  getIdToken: (forceRefresh?: boolean) => Promise<string>;
  reload: () => Promise<void>;
};

export type AuthUnsubscribe = () => void;

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
  signOut: () => Promise<void>;
};
