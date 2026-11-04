import { useEffect, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import QRCode from "react-native-qrcode-svg";

import { fetchCurrentAccount, fetchSecurityEvents, fetchIdentitySessions, revokeIdentitySession, type NexoraAccount, type NexoraSecurityEvent, type NexoraIdentitySession } from "../src/lib/api";
import { useAuth } from "../src/providers/AuthProvider";
import type { AuthMfaFactor } from "../src/lib/auth-types";

export default function AccountScreen() {
  const { user, status, signOut, sendVerificationEmail, getMfaFactors, beginTotpEnrollment, completeTotpEnrollment, cancelTotpEnrollment, removeMfaFactor } = useAuth();
  const [emailVerified, setEmailVerified] = useState(user?.emailVerified ?? false);
  const [verificationBusy, setVerificationBusy] = useState(false);
  const [verificationNotice, setVerificationNotice] = useState("");
  const [account, setAccount] = useState<NexoraAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [securityEvents, setSecurityEvents] = useState<NexoraSecurityEvent[]>([]);
  const [eventsLoading, setEventsLoading] = useState(true);
  const [eventsError, setEventsError] = useState("");
  const [sessions, setSessions] = useState<NexoraIdentitySession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [sessionsError, setSessionsError] = useState("");
  const [sessionBusyId, setSessionBusyId] = useState<string | null>(null);
  const [sessionNotice, setSessionNotice] = useState("");
  const [mfaFactors, setMfaFactors] = useState<AuthMfaFactor[]>([]);
  const [mfaLoading, setMfaLoading] = useState(true);
  const [mfaBusy, setMfaBusy] = useState(false);
  const [mfaError, setMfaError] = useState("");
  const [mfaNotice, setMfaNotice] = useState("");
  const [totpDraft, setTotpDraft] = useState<{ secretKey: string } | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [mfaCurrentPassword, setMfaCurrentPassword] = useState("");

  useEffect(() => {
    if (user) setEmailVerified(user.emailVerified);
  }, [user]);

  useEffect(() => () => {
    cancelTotpEnrollment();
  }, []);

  useEffect(() => {
    let active = true;
    async function loadAccount() {
      if (!user) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError("");
      try {
        const token = await user.getIdToken();
        const result = await fetchCurrentAccount(token);
        if (active) setAccount(result);
        try {
          const events = await fetchSecurityEvents(token);
          if (active) setSecurityEvents(events);
        } catch {
          if (active) setEventsError("Riwayat keamanan belum dapat dimuat.");
        } finally {
          if (active) setEventsLoading(false);
        }
        try {
          const currentSessions = await fetchIdentitySessions(token);
          if (active) setSessions(currentSessions);
        } catch {
          if (active) setSessionsError("Daftar perangkat dan sesi belum dapat dimuat.");
        } finally {
          if (active) setSessionsLoading(false);
        }
      } catch (requestError) {
        if (active) {
          const code = (requestError as { status?: number })?.status;
          setError(code === 401
            ? "Sesi tidak valid. Silakan masuk kembali."
            : "Informasi akun belum dapat dimuat. Periksa API dan koneksi Anda.");
        }
      } finally {
        if (active) {
          setLoading(false);
          setEventsLoading(false);
          setSessionsLoading(false);
        }
      }
    }
    void loadAccount();
    return () => { active = false; };
  }, [user, refreshKey]);

  useEffect(() => {
    let active = true;
    async function loadFactors() {
      if (!user) {
        setMfaLoading(false);
        return;
      }
      setMfaLoading(true);
      try {
        const factors = await getMfaFactors();
        if (active) setMfaFactors(factors);
      } catch {
        if (active) setMfaError("Daftar faktor MFA belum dapat dimuat pada platform ini.");
      } finally {
        if (active) setMfaLoading(false);
      }
    }
    void loadFactors();
    return () => { active = false; };
  }, [user, refreshKey]);

  async function handleVerification() {
    if (!user) return;
    setVerificationBusy(true);
    setVerificationNotice("");
    try {
      await user.reload();
      const refreshedToken = await user.getIdToken(true);
      const refreshedAccount = await fetchCurrentAccount(refreshedToken);
      setAccount(refreshedAccount);
      setEmailVerified(refreshedAccount.email_verified);
      if (refreshedAccount.email_verified) {
        setVerificationNotice("Email sudah terverifikasi dan status server telah diperbarui.");
      } else {
        await sendVerificationEmail();
        setVerificationNotice("Email belum terverifikasi. Tautan verifikasi baru telah dikirim.");
      }
    } catch {
      setVerificationNotice("Permintaan verifikasi belum berhasil. Coba kembali beberapa saat lagi.");
    } finally {
      setVerificationBusy(false);
    }
  }

  async function handleRevokeSession(sessionId: string) {
    if (!user) return;
    setSessionBusyId(sessionId);
    setSessionNotice("");
    try {
      await revokeIdentitySession(await user.getIdToken(), sessionId);
      setSessions((current) => current.map((session) =>
        session.id === sessionId
          ? { ...session, is_active: false, revoked_at: new Date().toISOString() }
          : session
      ));
      setSessionNotice("Sesi perangkat berhasil dicabut. Perangkat tersebut tidak dapat lagi menggunakan API Nexora dengan sesi ini.");
    } catch {
      setSessionNotice("Sesi belum berhasil dicabut. Muat ulang halaman dan coba kembali.");
    } finally {
      setSessionBusyId(null);
    }
  }

  async function handleBeginTotp() {
    setMfaBusy(true);
    setMfaError("");
    setMfaNotice("");
    try {
      if (!mfaCurrentPassword) { setMfaError("Masukkan kata sandi saat ini untuk verifikasi ulang."); return; }
      const draft = await beginTotpEnrollment(mfaCurrentPassword);
      setTotpDraft(draft);
      setTotpCode("");
      setMfaCurrentPassword("");
      setMfaNotice("Simpan secret ini di aplikasi authenticator. Secret hanya ditampilkan selama proses setup.");
    } catch (requestError) {
      const code = (requestError as { message?: string })?.message;
      setMfaError(code === "VERIFIED_EMAIL_REQUIRED"
        ? "Verifikasi email terlebih dahulu sebelum mengaktifkan MFA."
        : "Setup authenticator belum berhasil. Periksa konfigurasi Firebase Identity Platform dan coba lagi.");
    } finally {
      setMfaBusy(false);
    }
  }

  async function handleCompleteTotp() {
    setMfaBusy(true);
    setMfaError("");
    setMfaNotice("");
    try {
      await completeTotpEnrollment(totpCode, "Nexora authenticator");
      setTotpDraft(null);
      setTotpCode("");
      const factors = await getMfaFactors();
      setMfaFactors(factors);
      await user?.getIdToken(true);
      setMfaNotice("Authenticator berhasil didaftarkan. MFA akan diverifikasi pada sesi login berikutnya setelah Anda masuk ulang.");
    } catch (requestError) {
      const code = (requestError as { message?: string })?.message;
      setMfaError(code === "INVALID_TOTP_CODE"
        ? "Masukkan kode 6 digit dari aplikasi authenticator."
        : code === "TOTP_ENROLLMENT_EXPIRED"
          ? "Sesi setup kedaluwarsa. Mulai setup kembali."
          : "Kode tidak valid atau pendaftaran MFA gagal. Periksa waktu perangkat authenticator dan coba lagi.");
    } finally {
      setMfaBusy(false);
    }
  }

  function handleRemoveTotp(factor: AuthMfaFactor) {
    if (!mfaCurrentPassword) { setMfaError("Masukkan kata sandi saat ini untuk verifikasi ulang sebelum menghapus faktor."); return; }
    Alert.alert(
      "Hapus faktor MFA?",
      "Perangkat authenticator ini tidak lagi dapat digunakan untuk verifikasi dua langkah.",
      [
        { text: "Batal", style: "cancel" },
        {
          text: "Hapus",
          style: "destructive",
          onPress: () => { void (async () => {
            setMfaBusy(true);
            setMfaError("");
            setMfaNotice("");
            try {
              await removeMfaFactor(factor.uid, mfaCurrentPassword);
              setMfaCurrentPassword("");
              setMfaFactors(await getMfaFactors());
              setMfaNotice("Faktor authenticator telah dihapus.");
            } catch {
              setMfaError("Faktor MFA belum berhasil dihapus. Coba kembali.");
            } finally {
              setMfaBusy(false);
            }
          })(); },
        },
      ],
    );
  }

  async function handleSignOut() {
    try {
      await signOut();
      router.replace("/");
    } catch {
      setError("Tidak dapat mengakhiri sesi. Silakan coba kembali.");
    }
  }

  if (status !== "signed-in" || !user) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}>
          <Text style={styles.heading}>Account unavailable</Text>
          <Text style={styles.body}>Silakan masuk untuk melihat informasi akun Nexora.</Text>
          <Pressable onPress={() => router.replace("/auth")} style={styles.primary}>
            <Text style={styles.primaryText}>Sign in</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  const mfaStatus = account?.mfa_verified
    ? `Aktif pada sesi ini (${account.second_factor_type.toUpperCase()})`
    : "Belum diverifikasi pada sesi ini";

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Pressable onPress={() => router.replace("/")} style={styles.back}>
          <Text style={styles.backText}>‹  Home</Text>
        </Pressable>
        <Text style={styles.eyebrow}>NEXORA IDENTITY</Text>
        <Text style={styles.heading}>Account & security</Text>
        <Text style={styles.body}>Manage your central Nexora account and review its identity status.</Text>

        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{(user.displayName?.[0] ?? user.email?.[0] ?? "N").toUpperCase()}</Text>
          </View>
          <Text style={styles.name}>{user.displayName ?? "Nexora member"}</Text>
          <Text style={styles.email}>{user.email ?? "Email not provided"}</Text>
          <View style={styles.statusPill}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>Firebase session active</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Nexora account</Text>
          {loading ? (
            <ActivityIndicator color="#294C75" style={styles.loader} />
          ) : error ? (
            <View>
              <Text style={styles.error}>{error}</Text>
              <Pressable onPress={() => setRefreshKey((value) => value + 1)} style={styles.retry}>
                <Text style={styles.retryText}>Try again</Text>
              </Pressable>
            </View>
          ) : account ? (
            <>
              <InfoRow label="Internal account ID" value={account.id} />
              <InfoRow label="Account status" value={account.status} />
              <InfoRow label="Created" value={new Date(account.created_at).toLocaleDateString()} />
              <InfoRow label="Identity providers" value={account.providers.map((item) => item.provider).join(", ") || "None"} />
            </>
          ) : null}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Security</Text>
          <InfoRow label="Sign-in method" value="Email and password" />
          <InfoRow label="Email verification" value={(account?.email_verified ?? emailVerified) ? "Verified" : "Not verified"} />
          <InfoRow label="Multi-factor authentication" value={mfaStatus} />
          <Text style={styles.sessionIntro}>Status MFA berasal dari klaim token Firebase yang diverifikasi server, bukan dari nilai yang dikirim aplikasi.</Text>
          {mfaLoading ? (
            <ActivityIndicator color="#294C75" style={styles.loader} />
          ) : (
            <>
              <Text style={styles.label}>CURRENT PASSWORD (RE-AUTHENTICATION)</Text>
              <TextInput
                value={mfaCurrentPassword}
                onChangeText={setMfaCurrentPassword}
                secureTextEntry
                autoCapitalize="none"
                placeholder="Enter your current password"
                placeholderTextColor="#9AA6B5"
                style={styles.totpInput}
                editable={!mfaBusy}
              />
              <Text style={styles.sessionIntro}>
                Faktor authenticator terdaftar: {mfaFactors.length}. Pendaftaran memerlukan email terverifikasi dan Firebase Identity Platform dengan TOTP diaktifkan.
              </Text>
              {mfaFactors.map((factor) => (
                <View key={factor.uid} style={styles.mfaFactorRow}>
                  <View style={styles.sessionCopy}>
                    <Text style={styles.eventTitle}>{factor.displayName || "Authenticator app"}</Text>
                    <Text style={styles.eventMeta}>TOTP · {factor.enrollmentTime ? new Date(factor.enrollmentTime).toLocaleString() : "Enrolled"}</Text>
                  </View>
                  <Pressable disabled={mfaBusy} onPress={() => handleRemoveTotp(factor)} style={styles.revokeButton}>
                    <Text style={styles.revokeText}>Remove</Text>
                  </Pressable>
                </View>
              ))}
              {!totpDraft ? (
                <Pressable
                  disabled={mfaBusy || !account?.email_verified}
                  onPress={handleBeginTotp}
                  style={[styles.verifyButton, (!account?.email_verified || mfaBusy) && styles.disabledButton]}
                >
                  {mfaBusy
                    ? <ActivityIndicator color="#FFFFFF" />
                    : <Text style={styles.verifyText}>Set up authenticator (TOTP)</Text>}
                </Pressable>
              ) : (
                <View style={styles.totpSetup}>
                  <Text style={styles.totpTitle}>1. Scan this QR code with your authenticator</Text>
                  <View style={styles.totpQrFrame}>
                    <QRCode value={totpDraft.qrCodeUrl} size={196} backgroundColor="#FFFFFF" color="#172C4B" />
                  </View>
                  <Text style={styles.sessionIntro}>
                    QR dibuat secara lokal di perangkat. Jangan bagikan atau screenshot QR/secret ini. Jika aplikasi authenticator tidak dapat memindai QR, masukkan secret manual di bawah.
                  </Text>
                  <Text style={styles.totpTitle}>Manual setup key</Text>
                  <Text selectable style={styles.totpSecret}>{totpDraft.secretKey}</Text>
                  <Text style={styles.sessionIntro}>
                    Account: {user.email ?? user.uid} · Issuer: Nexora · Type: Time-based (6 digits, 30 seconds).
                  </Text>
                  <Text style={styles.totpTitle}>3. Enter the 6-digit code</Text>
                  <TextInput
                    value={totpCode}
                    onChangeText={(value) => setTotpCode(value.replace(/\D/g, "").slice(0, 6))}
                    keyboardType="number-pad"
                    maxLength={6}
                    placeholder="000000"
                    placeholderTextColor="#9AA6B5"
                    style={styles.totpInput}
                    editable={!mfaBusy}
                    accessibilityLabel="Six digit authenticator code"
                  />
                  <Pressable disabled={mfaBusy || totpCode.length !== 6} onPress={handleCompleteTotp} style={[styles.verifyButton, (mfaBusy || totpCode.length !== 6) && styles.disabledButton]}>
                    {mfaBusy ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.verifyText}>Verify and enable MFA</Text>}
                  </Pressable>
                  <Pressable disabled={mfaBusy} onPress={() => { cancelTotpEnrollment(); setTotpDraft(null); setTotpCode(""); setMfaCurrentPassword(""); }} style={styles.cancelTotp}>
                    <Text style={styles.inlineText}>Cancel setup</Text>
                  </Pressable>
                </View>
              )}
            </>
          )}
          {!!mfaError && <Text accessibilityRole="alert" style={styles.error}>{mfaError}</Text>}
          {!!mfaNotice && <Text accessibilityLiveRegion="polite" style={styles.verificationNotice}>{mfaNotice}</Text>}
          <Pressable disabled={verificationBusy} onPress={handleVerification} style={styles.verifyButton}>
            {verificationBusy
              ? <ActivityIndicator color="#FFFFFF" />
              : <Text style={styles.verifyText}>{emailVerified ? "Refresh verification status" : "Send verification email"}</Text>}
          </Pressable>
          {!!verificationNotice && (
            <Text accessibilityLiveRegion="polite" style={styles.verificationNotice}>{verificationNotice}</Text>
          )}
          <InfoRow label="Last token refresh" value="Managed securely by Firebase" />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent security activity</Text>
          {eventsLoading ? (
            <ActivityIndicator color="#294C75" style={styles.loader} />
          ) : eventsError ? (
            <Text style={styles.eventError}>{eventsError}</Text>
          ) : securityEvents.length === 0 ? (
            <Text style={styles.eventEmpty}>Belum ada aktivitas keamanan yang tercatat.</Text>
          ) : (
            securityEvents.slice(0, 10).map((event) => (
              <View key={event.id} style={styles.eventRow}>
                <View style={styles.eventDot} />
                <View style={styles.eventCopy}>
                  <Text style={styles.eventTitle}>{formatEventType(event.event_type)}</Text>
                  <Text style={styles.eventMeta}>
                    {new Date(event.occurred_at).toLocaleString()} · {event.provider || "Nexora"}
                  </Text>
                  {!!event.source_ip && <Text style={styles.eventMeta}>IP: {event.source_ip}</Text>}
                </View>
              </View>
            ))
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Devices & active sessions</Text>
          <Text style={styles.sessionIntro}>Sesi dibuat berdasarkan waktu autentikasi Firebase dan dikontrol oleh API Nexora.</Text>
          {sessionsLoading ? (
            <ActivityIndicator color="#294C75" style={styles.loader} />
          ) : sessionsError ? (
            <Text style={styles.eventError}>{sessionsError}</Text>
          ) : sessions.length === 0 ? (
            <Text style={styles.eventEmpty}>Belum ada sesi yang tercatat.</Text>
          ) : (
            sessions.map((session) => (
              <View key={session.id} style={styles.sessionRow}>
                <View style={styles.sessionCopy}>
                  <Text style={styles.eventTitle}>
                    {session.is_current ? "This device" : "Signed-in device"}
                    {session.is_active ? " · Active" : " · Revoked"}
                  </Text>
                  <Text style={styles.eventMeta}>Last activity: {new Date(session.last_seen_at).toLocaleString()}</Text>
                  <Text style={styles.eventMeta}>MFA: {session.mfa_verified ? session.second_factor_type.toUpperCase() : "Not verified"}</Text>
                  <Text numberOfLines={2} style={styles.eventMeta}>{session.user_agent || "Unknown device information"}</Text>
                  {!!session.source_ip && <Text style={styles.eventMeta}>IP: {session.source_ip}</Text>}
                </View>
                {session.is_active && !session.is_current && (
                  <Pressable
                    disabled={sessionBusyId === session.id}
                    onPress={() => handleRevokeSession(session.id)}
                    style={styles.revokeButton}
                  >
                    {sessionBusyId === session.id
                      ? <ActivityIndicator color="#A33D37" size="small" />
                      : <Text style={styles.revokeText}>Revoke</Text>}
                  </Pressable>
                )}
              </View>
            ))
          )}
          {!!sessionNotice && <Text accessibilityLiveRegion="polite" style={styles.verificationNotice}>{sessionNotice}</Text>}
        </View>

        <Pressable onPress={handleSignOut} style={styles.signOut}>
          <Text style={styles.signOutText}>Sign out</Text>
        </Pressable>
        <Text style={styles.footer}>Product access and data permissions are enforced by the Nexora API.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function formatEventType(eventType: string): string {
  switch (eventType) {
    case "identity.authenticated": return "Successful sign-in";
    case "identity.account_viewed": return "Account viewed";
    case "identity.verification_requested": return "Verification email requested";
    case "identity.password_reset_requested": return "Password reset requested";
    case "identity.session_revoked": return "Session revoked";
    case "identity.email_verification_confirmed": return "Email verification confirmed";
    case "identity.credential_changed": return "Credential changed";
    case "identity.auth_context_changed": return "Sign-in context changed";
    case "identity.mfa_authenticated": return "Multi-factor authentication completed";
    default: return "Security activity";
  }
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text selectable style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#F4F6FA" },
  content: { width: "100%", maxWidth: 620, alignSelf: "center", paddingHorizontal: 22, paddingTop: 12, paddingBottom: 36 },
  back: { alignSelf: "flex-start", paddingVertical: 8, marginBottom: 24 },
  backText: { color: "#50647F", fontSize: 13, fontWeight: "800" },
  eyebrow: { color: "#8190A4", fontSize: 9, fontWeight: "900", letterSpacing: 1.7 },
  heading: { color: "#172C4B", fontSize: 27, fontWeight: "900", marginTop: 7 },
  body: { color: "#78879B", fontSize: 12, lineHeight: 19, marginTop: 7 },
  profileCard: { backgroundColor: "#172C4B", borderRadius: 21, padding: 21, alignItems: "center", marginTop: 23 },
  avatar: { width: 58, height: 58, borderRadius: 20, backgroundColor: "#E3EAF3", alignItems: "center", justifyContent: "center" },
  avatarText: { color: "#172C4B", fontSize: 24, fontWeight: "900" },
  name: { color: "#FFFFFF", fontSize: 17, fontWeight: "800", marginTop: 12 },
  email: { color: "#B8C8DB", fontSize: 11, marginTop: 4 },
  statusPill: { flexDirection: "row", alignItems: "center", gap: 6, backgroundColor: "#284563", paddingHorizontal: 10, paddingVertical: 6, borderRadius: 20, marginTop: 13 },
  statusDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: "#65D6A8" },
  statusText: { color: "#D5E4F4", fontSize: 9, fontWeight: "700" },
  section: { backgroundColor: "#FFFFFF", borderWidth: 1, borderColor: "#E8EDF3", borderRadius: 17, padding: 17, marginTop: 15 },
  sectionTitle: { color: "#1B2D46", fontSize: 13, fontWeight: "900", marginBottom: 9 },
  label: { color: "#62738A", fontSize: 9, fontWeight: "900", letterSpacing: 1.1, marginBottom: 7, marginTop: 9 },
  inlineText: { color: "#42638B", fontSize: 12, fontWeight: "700" },
  infoRow: { borderTopWidth: 1, borderTopColor: "#EEF1F5", paddingVertical: 11, gap: 5 },
  infoLabel: { color: "#8794A6", fontSize: 10, fontWeight: "700" },
  infoValue: { color: "#263E5E", fontSize: 11, fontWeight: "700" },
  loader: { padding: 15 },
  error: { color: "#B42318", fontSize: 11, lineHeight: 17 },
  retry: { alignSelf: "flex-start", marginTop: 8, paddingVertical: 7 },
  retryText: { color: "#294C75", fontSize: 11, fontWeight: "800" },
  verifyButton: { minHeight: 42, borderRadius: 11, backgroundColor: "#294C75", alignItems: "center", justifyContent: "center", marginTop: 8, paddingHorizontal: 12 },
  verifyText: { color: "#FFFFFF", fontSize: 11, fontWeight: "800" },
  disabledButton: { opacity: 0.45 },
  mfaFactorRow: { flexDirection: "row", alignItems: "center", gap: 8, borderTopWidth: 1, borderTopColor: "#EEF1F5", paddingVertical: 10 },
  totpSetup: { backgroundColor: "#F6F8FB", borderRadius: 12, padding: 12, marginTop: 10 },
  totpQrFrame: { alignSelf: "center", backgroundColor: "#FFFFFF", borderRadius: 12, padding: 12, marginVertical: 8, borderWidth: 1, borderColor: "#E2E8F0" },
  totpQrFrame: { alignSelf: "center", backgroundColor: "#FFFFFF", padding: 12, borderRadius: 12, marginVertical: 8 },
  totpTitle: { color: "#263E5E", fontSize: 10, fontWeight: "900", marginTop: 8, marginBottom: 7 },
  totpSecret: { color: "#172C4B", backgroundColor: "#E8EEF6", padding: 12, borderRadius: 9, fontSize: 15, fontWeight: "900", letterSpacing: 1.1 },
  totpInput: { minHeight: 46, borderWidth: 1, borderColor: "#DCE4EE", backgroundColor: "#FFFFFF", borderRadius: 10, paddingHorizontal: 12, color: "#172C4B", fontSize: 18, fontWeight: "800", letterSpacing: 5, textAlign: "center" },
  cancelTotp: { alignSelf: "center", padding: 10 },
  verificationNotice: { color: "#42638B", fontSize: 10, lineHeight: 15, marginTop: 8 },
  sessionIntro: { color: "#8794A6", fontSize: 9, lineHeight: 14, marginBottom: 8 },
  sessionRow: { flexDirection: "row", alignItems: "center", gap: 8, borderTopWidth: 1, borderTopColor: "#EEF1F5", paddingVertical: 12 },
  sessionCopy: { flex: 1, gap: 4 },
  revokeButton: { minWidth: 62, minHeight: 32, borderRadius: 9, borderWidth: 1, borderColor: "#E7C9C7", alignItems: "center", justifyContent: "center", paddingHorizontal: 8 },
  revokeText: { color: "#A33D37", fontSize: 9, fontWeight: "900" },
  eventRow: { flexDirection: "row", gap: 10, borderTopWidth: 1, borderTopColor: "#EEF1F5", paddingVertical: 12 },
  eventDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: "#5B8BBD", marginTop: 4 },
  eventCopy: { flex: 1, gap: 4 },
  eventTitle: { color: "#263E5E", fontSize: 11, fontWeight: "800" },
  eventMeta: { color: "#8794A6", fontSize: 9, lineHeight: 14 },
  eventEmpty: { color: "#8794A6", fontSize: 10, lineHeight: 16, paddingVertical: 8 },
  eventError: { color: "#A33D37", fontSize: 10, lineHeight: 16, paddingVertical: 8 },
  signOut: { minHeight: 49, borderRadius: 13, borderWidth: 1, borderColor: "#E7C9C7", alignItems: "center", justifyContent: "center", marginTop: 20, backgroundColor: "#FFF9F8" },
  signOutText: { color: "#A33D37", fontSize: 12, fontWeight: "900" },
  footer: { color: "#9AA6B5", fontSize: 9, lineHeight: 15, textAlign: "center", marginTop: 17 },
  center: { flex: 1, justifyContent: "center", padding: 25 },
  primary: { alignSelf: "flex-start", backgroundColor: "#172C4B", borderRadius: 12, paddingHorizontal: 20, paddingVertical: 13, marginTop: 18 },
  primaryText: { color: "#FFFFFF", fontSize: 12, fontWeight: "800" },
});
