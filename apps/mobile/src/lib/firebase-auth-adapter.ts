import { Platform } from "react-native";

import { firebaseJsAuthAdapter } from "./firebase-js-auth";
import { firebaseNativeAuthAdapter } from "./firebase-native-auth";

export const firebaseAuthAdapter =
  Platform.OS === "web" ? firebaseJsAuthAdapter : firebaseNativeAuthAdapter;
