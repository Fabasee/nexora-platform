import AsyncStorage from "@react-native-async-storage/async-storage";
import { Platform } from "react-native";
import { getApp, getApps, initializeApp } from "firebase/app";
import * as FirebaseAuth from "firebase/auth";
import { getAuth, initializeAuth, type Auth } from "firebase/auth";

type ReactNativePersistenceFactory = (
  storage: typeof AsyncStorage,
) => NonNullable<Parameters<typeof initializeAuth>[1]>["persistence"];

// Firebase 12 exposes this on the React Native runtime entry but not shared type declarations.
const getReactNativePersistence = (
  FirebaseAuth as unknown as { getReactNativePersistence: ReactNativePersistenceFactory }
).getReactNativePersistence;

const firebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY ?? "",
  authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN ?? "",
  projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID ?? "",
  appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID ?? "",
};

let authInstance: Auth | null = null;

export function isFirebaseConfigured(): boolean {
  return Object.values(firebaseConfig).every((value) => value.length > 0);
}

function getFirebaseApp() {
  const requiredValues = Object.values(firebaseConfig);
  if (requiredValues.some((value) => value.length === 0)) {
    throw new Error("Firebase client configuration is incomplete.");
  }

  return getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
}

export function getFirebaseAuth(): Auth {
  if (authInstance) return authInstance;

  const app = getFirebaseApp();
  if (Platform.OS === "web") {
    authInstance = getAuth(app);
    return authInstance;
  }

  try {
    authInstance = initializeAuth(app, {
      persistence: getReactNativePersistence(AsyncStorage),
    });
  } catch (error) {
    const code = (error as { code?: string }).code;
    if (code !== "auth/already-initialized") throw error;
    authInstance = getAuth(app);
  }

  return authInstance;
}

export async function getFirebaseIdToken(forceRefresh = false): Promise<string> {
  const user = getFirebaseAuth().currentUser;
  if (!user) throw new Error("A signed-in Firebase user is required.");
  return user.getIdToken(forceRefresh);
}
