import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { reload } from "firebase/auth";
import { SafeAreaView } from "react-native-safe-area-context";

import { fetchCurrentAccount, fetchSecurityEvents, fetchIdentitySessions, revokeIdentitySession, type NexoraAccount, type NexoraSecurityEvent, type NexoraIdentitySession } from "../src/lib/api";
import { useAuth } from "../src/providers/AuthProvider";

export default function AccountScreen() {
  const { user, status, signOut, sendVerificationEmail } = useAuth();
  const [emailVerified, setEmailVerified] = useState(user?.emailVerified ?? false);
  const [verificationBusy, setVerificationBusy] = useState(false);
  const [verificationNotice, setVerificationNotice] = useState("");
  const [account, setAccount] = useState<NexoraAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [securityEvents, setSecurityEvents] = useState<NexoraSecurityEvent[]>([]);
  const [eventsLoading, setEventsLoading] = useState(true);
  const [eventsError, setEventsError] = useState("");\n  const [sessions, setSessions] = useState<NexoraIdentitySession[]>([]);\n  const [sessionsLoading, setSessionsLoading] = useState(true);\n  const [sessionsError, setSessionsError] = useState("");\n  const [sessionBusyId, setSessionBusyId] = useState<string | null>(null);\n  const [sessionNotice, setSessionNotice] = useState("");

  useEffect(() => {
    if (user) setEmailVerified(user.emailVerified);
  }, [user]);

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
          setEventsLoading(false);\n          setSessionsLoading(false);
        }
      }
    }
    void loadAccount();
    return () => { active = false; };
  }, [user, refreshKey]);

  async function handleVerification() {
    if (!user) return;
    setVerificationBusy(true);
    setVerificationNotice("");
    try {
      if (emailVerified) {
        await reload(user);
        setEmailVerified(user.emailVerified);
        setVerificationNotice(user.emailVerified
          ? "Email sudah terverifikasi."
          : "Status verifikasi belum berubah. Periksa email Anda.");
      } else {
        await sendVerificationEmail();
        setVerificationNotice("Tautan verifikasi telah dikirim. Periksa kotak masuk atau folder spam.");
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
          <InfoRow label="Email verification" value={emailVerified ? "Verified" : "Not verified"} />
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
    case "identity.credential_changed": return "Credential changed";
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
  infoRow: { borderTopWidth: 1, borderTopColor: "#EEF1F5", paddingVertical: 11, gap: 5 },
  infoLabel: { color: "#8794A6", fontSize: 10, fontWeight: "700" },
  infoValue: { color: "#263E5E", fontSize: 11, fontWeight: "700" },
  loader: { padding: 15 },
  error: { color: "#B42318", fontSize: 11, lineHeight: 17 },
  retry: { alignSelf: "flex-start", marginTop: 8, paddingVertical: 7 },
  retryText: { color: "#294C75", fontSize: 11, fontWeight: "800" },
  verifyButton: { minHeight: 42, borderRadius: 11, backgroundColor: "#294C75", alignItems: "center", justifyContent: "center", marginTop: 8, paddingHorizontal: 12 },
  verifyText: { color: "#FFFFFF", fontSize: 11, fontWeight: "800" },
  verificationNotice: { color: "#42638B", fontSize: 10, lineHeight: 15, marginTop: 8 },
  sessionIntro: { color: "#8794A6", fontSize: 9, lineHeight: 14, marginBottom: 8 },\n  sessionRow: { flexDirection: "row", alignItems: "center", gap: 8, borderTopWidth: 1, borderTopColor: "#EEF1F5", paddingVertical: 12 },\n  sessionCopy: { flex: 1, gap: 4 },\n  revokeButton: { minWidth: 62, minHeight: 32, borderRadius: 9, borderWidth: 1, borderColor: "#E7C9C7", alignItems: "center", justifyContent: "center", paddingHorizontal: 8 },\n  revokeText: { color: "#A33D37", fontSize: 9, fontWeight: "900" },\n  eventRow: { flexDirection: "row", gap: 10, borderTopWidth: 1, borderTopColor: "#EEF1F5", paddingVertical: 12 },
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
