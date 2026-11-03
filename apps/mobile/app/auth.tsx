import { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "../src/providers/AuthProvider";

type Mode = "signin" | "register" | "reset";

function friendlyAuthError(error: unknown): string {
  const code = (error as { code?: string })?.code;
  if (code === "auth/invalid-credential" || code === "auth/wrong-password" || code === "auth/user-not-found") {
    return "Email atau kata sandi tidak cocok.";
  }
  if (code === "auth/email-already-in-use") return "Email sudah terdaftar. Silakan masuk.";
  if (code === "auth/weak-password") return "Kata sandi terlalu lemah. Gunakan minimal 8 karakter.";
  if (code === "auth/invalid-email") return "Format email belum benar.";
  if (code === "auth/too-many-requests") return "Terlalu banyak percobaan. Coba lagi beberapa saat.";
  if (code === "auth/network-request-failed") return "Koneksi internet bermasalah. Periksa jaringan Anda.";
  return "Permintaan belum berhasil. Periksa koneksi dan coba kembali.";
}

export default function AuthScreen() {
  const { signIn, register, resetPassword, status } = useAuth();
  const [mode, setMode] = useState<Mode>("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const title = mode === "register" ? "Create your account" : mode === "reset" ? "Reset password" : "Welcome back";
  const subtitle = mode === "register"
    ? "One Nexora account for connected experiences."
    : mode === "reset"
      ? "We’ll send a secure password reset link to your email."
      : "Sign in to continue to your Nexora account.";

  async function submit() {
    setError("");
    setNotice("");
    if (!email.trim()) {
      setError("Masukkan alamat email.");
      return;
    }
    if (mode !== "reset" && !password) {
      setError("Masukkan kata sandi.");
      return;
    }
    if (mode === "register" && !name.trim()) {
      setError("Masukkan nama Anda.");
      return;
    }
    if (mode === "register" && password.length < 8) {
      setError("Gunakan kata sandi minimal 8 karakter.");
      return;
    }

    setBusy(true);
    try {
      if (mode === "signin") {
        await signIn(email, password);
        router.replace("/");
      } else if (mode === "register") {
        await register(name, email, password);
        router.replace("/");
      } else {
        await resetPassword(email);
        setNotice("Jika email terdaftar, tautan pemulihan akan dikirim.");
      }
    } catch (requestError) {
      setError(friendlyAuthError(requestError));
    } finally {
      setBusy(false);
    }
  }

  function changeMode(nextMode: Mode) {
    setMode(nextMode);
    setError("");
    setNotice("");
    setPassword("");
  }

  if (status === "unconfigured") {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.configCard}>
          <Text style={styles.brand}>NEXORA</Text>
          <Text style={styles.title}>Firebase setup required</Text>
          <Text style={styles.subtitle}>Lengkapi konfigurasi Firebase client di file .env aplikasi mobile sebelum mengaktifkan autentikasi.</Text>
          <Pressable onPress={() => router.replace("/")} style={styles.secondaryButton}>
            <Text style={styles.secondaryText}>Back to home</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Pressable onPress={() => router.replace("/")} style={styles.back}>
            <Text style={styles.backText}>‹  Nexora</Text>
          </Pressable>
          <View style={styles.brandMark}><Text style={styles.brandMarkText}>N</Text></View>
          <Text style={styles.brand}>NEXORA ACCOUNT</Text>
          <Text style={styles.title}>{title}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>

          <View style={styles.form}>
            {mode === "register" && (
              <>
                <Text style={styles.label}>FULL NAME</Text>
                <TextInput
                  value={name}
                  onChangeText={setName}
                  placeholder="Your name"
                  placeholderTextColor="#9AA6B5"
                  autoCapitalize="words"
                  autoComplete="name"
                  style={styles.input}
                  editable={!busy}
                />
              </>
            )}
            <Text style={styles.label}>EMAIL ADDRESS</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="you@example.com"
              placeholderTextColor="#9AA6B5"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              textContentType="emailAddress"
              style={styles.input}
              editable={!busy}
            />
            {mode !== "reset" && (
              <>
                <Text style={styles.label}>PASSWORD</Text>
                <TextInput
                  value={password}
                  onChangeText={setPassword}
                  placeholder={mode === "register" ? "At least 8 characters" : "Your password"}
                  placeholderTextColor="#9AA6B5"
                  secureTextEntry
                  autoCapitalize="none"
                  autoComplete={mode === "register" ? "new-password" : "current-password"}
                  textContentType={mode === "register" ? "newPassword" : "password"}
                  style={styles.input}
                  editable={!busy}
                />
              </>
            )}

            {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
            {!!notice && <Text accessibilityRole="status" style={styles.notice}>{notice}</Text>}

            <Pressable
              accessibilityRole="button"
              disabled={busy}
              onPress={submit}
              style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed, busy && styles.disabled]}
            >
              {busy ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryText}>
                {mode === "register" ? "Create account" : mode === "reset" ? "Send reset link" : "Sign in"}
              </Text>}
            </Pressable>

            {mode === "signin" && (
              <Pressable onPress={() => changeMode("reset")} style={styles.inlineAction}>
                <Text style={styles.inlineText}>Forgot password?</Text>
              </Pressable>
            )}
          </View>

          <View style={styles.switchRow}>
            <Text style={styles.switchHint}>{mode === "register" ? "Already have an account?" : "New to Nexora?"}</Text>
            <Pressable onPress={() => changeMode(mode === "register" ? "signin" : "register")}>
              <Text style={styles.switchAction}>{mode === "register" ? "Sign in" : "Create account"}</Text>
            </Pressable>
          </View>
          {mode === "reset" && (
            <Pressable onPress={() => changeMode("signin")} style={styles.inlineAction}>
              <Text style={styles.inlineText}>Back to sign in</Text>
            </Pressable>
          )}
          <Text style={styles.footer}>SECURE IDENTITY · PRODUCT DATA REMAINS SEPARATED</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  safe: { flex: 1, backgroundColor: "#F4F6FA" },
  content: { flexGrow: 1, width: "100%", maxWidth: 520, alignSelf: "center", paddingHorizontal: 25, paddingTop: 12, paddingBottom: 32 },
  back: { alignSelf: "flex-start", paddingVertical: 8, marginBottom: 35 },
  backText: { color: "#50647F", fontSize: 14, fontWeight: "700" },
  brandMark: { width: 48, height: 48, borderRadius: 16, backgroundColor: "#172C4B", alignItems: "center", justifyContent: "center" },
  brandMarkText: { color: "#FFFFFF", fontSize: 27, fontWeight: "900" },
  brand: { color: "#78879B", fontSize: 10, fontWeight: "900", letterSpacing: 2, marginTop: 15 },
  title: { color: "#172C4B", fontSize: 30, fontWeight: "900", letterSpacing: -0.8, marginTop: 23 },
  subtitle: { color: "#78879B", fontSize: 13, lineHeight: 20, marginTop: 8, maxWidth: 350 },
  form: { marginTop: 31 },
  label: { color: "#62738A", fontSize: 9, fontWeight: "900", letterSpacing: 1.3, marginBottom: 8, marginTop: 15 },
  input: { minHeight: 52, backgroundColor: "#FFFFFF", borderColor: "#E2E8F0", borderWidth: 1, borderRadius: 13, paddingHorizontal: 15, color: "#172C4B", fontSize: 14 },
  primaryButton: { minHeight: 53, borderRadius: 14, backgroundColor: "#172C4B", alignItems: "center", justifyContent: "center", marginTop: 22 },
  primaryText: { color: "#FFFFFF", fontSize: 13, fontWeight: "800" },
  pressed: { opacity: 0.85 },
  disabled: { opacity: 0.55 },
  error: { color: "#B42318", fontSize: 12, lineHeight: 18, marginTop: 13 },
  notice: { color: "#16704A", fontSize: 12, lineHeight: 18, marginTop: 13 },
  inlineAction: { alignSelf: "center", padding: 12 },
  inlineText: { color: "#42638B", fontSize: 12, fontWeight: "700" },
  switchRow: { flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 6, marginTop: 25 },
  switchHint: { color: "#8290A2", fontSize: 11 },
  switchAction: { color: "#294C75", fontSize: 11, fontWeight: "900" },
  footer: { color: "#A3ADBA", fontSize: 8, fontWeight: "800", letterSpacing: 1, textAlign: "center", marginTop: "auto", paddingTop: 44 },
  configCard: { flex: 1, justifyContent: "center", padding: 28 },
  secondaryButton: { padding: 14, backgroundColor: "#E7EDF5", borderRadius: 12, marginTop: 20, alignSelf: "flex-start" },
  secondaryText: { color: "#294C75", fontWeight: "800" },
});
