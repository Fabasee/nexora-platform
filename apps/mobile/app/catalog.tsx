import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "../src/providers/AuthProvider";
import {
  activateFreeProduct,
  ApiError,
  fetchProductCatalog,
  type NexoraCatalogProduct,
} from "../src/lib/api";

export default function ProductCatalogScreen() {
  const { status, user } = useAuth();
  const [products, setProducts] = useState<NexoraCatalogProduct[]>([]);
  const [loading, setLoading] = useState(false);
  const [activatingKey, setActivatingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadCatalog = useCallback(async () => {
    if (status !== "signed-in" || !user) {
      setProducts([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const token = await user.getIdToken();
      setProducts(await fetchProductCatalog(token));
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 403) {
        setError("Verifikasi email Nexora diperlukan sebelum membuka katalog produk.");
      } else if (cause instanceof ApiError && cause.status === 401) {
        setError("Sesi akun berakhir. Silakan masuk kembali.");
      } else {
        setError(cause instanceof Error ? cause.message : "Katalog belum dapat dimuat.");
      }
    } finally {
      setLoading(false);
    }
  }, [status, user]);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  const onActivate = async (productKey: string) => {
    if (!user || activatingKey) return;
    setActivatingKey(productKey);
    setError(null);
    try {
      const token = await user.getIdToken();
      await activateFreeProduct(token, productKey);
      await loadCatalog();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Aktivasi produk gagal.");
    } finally {
      setActivatingKey(null);
    }
  };

  if (status !== "signed-in") {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.center}>
          <Text style={styles.title}>Katalog Nexora</Text>
          <Text style={styles.muted}>Masuk ke akun Nexora untuk melihat dan mengaktifkan produk.</Text>
          <Pressable style={styles.primaryButton} onPress={() => router.push("/auth")}>
            <Text style={styles.primaryText}>Masuk / Daftar</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Pressable accessibilityRole="button" onPress={() => router.back()}>
            <Text style={styles.back}>‹ Kembali</Text>
          </Pressable>
          <Pressable accessibilityRole="button" onPress={() => void loadCatalog()}>
            <Text style={styles.refresh}>Muat ulang</Text>
          </Pressable>
        </View>
        <Text style={styles.eyebrow}>NEXORA PLATFORM</Text>
        <Text style={styles.title}>Katalog produk</Text>
        <Text style={styles.subtitle}>
          Pilih produk untuk mengaktifkan keanggotaan Free. Aktivasi hanya berlaku pada produk yang Anda pilih.
        </Text>

        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        {loading ? (
          <View style={styles.loading}><ActivityIndicator color="#24466D" /><Text style={styles.muted}>Memuat katalog...</Text></View>
        ) : products.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>Belum ada produk tersedia</Text>
            <Text style={styles.muted}>Produk akan muncul di sini setelah didaftarkan dan diaktifkan oleh pengelola Nexora.</Text>
          </View>
        ) : (
          <View style={styles.list}>
            {products.map((product) => {
              const busy = activatingKey === product.key;
              const blocked = product.membership_status === "suspended" || product.membership_status === "revoked";
              return (
                <View key={product.key} style={styles.card}>
                  <View style={styles.cardTop}>
                    <View style={styles.mark}><Text style={styles.markText}>{product.name.slice(0, 2).toUpperCase()}</Text></View>
                    <View style={styles.statusPill}>
                      <Text style={styles.statusText}>
                        {blocked ? "Dibatasi" : product.is_activated ? "Aktif" : "Tersedia"}
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.productName}>{product.name}</Text>
                  {product.description ? <Text style={styles.description}>{product.description}</Text> : null}
                  {product.subscription ? (
                    <Text style={styles.plan}>
                      Paket {product.subscription.plan_name} · {product.subscription.tier.toUpperCase()}
                    </Text>
                  ) : (
                    <Text style={styles.plan}>Paket Free tersedia saat aktivasi</Text>
                  )}
                  {product.is_activated ? (
                    <View style={styles.activeButton}><Text style={styles.activeText}>Produk aktif</Text></View>
                  ) : (
                    <Pressable
                      accessibilityRole="button"
                      disabled={busy || blocked}
                      onPress={() => void onActivate(product.key)}
                      style={[styles.primaryButton, (busy || blocked) && styles.disabledButton]}
                    >
                      {busy ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryText}>{blocked ? "Hubungi dukungan" : "Aktifkan Free"}</Text>}
                    </Pressable>
                  )}
                </View>
              );
            })}
          </View>
        )}
        <Text style={styles.footnote}>Status paket dan hak akses ditentukan oleh server Nexora.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F4F6FA" },
  content: { padding: 22, paddingBottom: 40, maxWidth: 680, width: "100%", alignSelf: "center" },
  header: { flexDirection: "row", justifyContent: "space-between", marginBottom: 28 },
  back: { color: "#24466D", fontSize: 13, fontWeight: "700" },
  refresh: { color: "#24466D", fontSize: 12, fontWeight: "700" },
  eyebrow: { color: "#8290A4", fontSize: 10, fontWeight: "800", letterSpacing: 1.6 },
  title: { color: "#172C4B", fontSize: 29, fontWeight: "900", marginTop: 7 },
  subtitle: { color: "#718096", fontSize: 13, lineHeight: 20, marginTop: 9, marginBottom: 20 },
  list: { gap: 12 },
  card: { backgroundColor: "#FFFFFF", borderRadius: 18, borderWidth: 1, borderColor: "#E7ECF3", padding: 17 },
  cardTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  mark: { width: 38, height: 38, borderRadius: 12, backgroundColor: "#EAF0F7", alignItems: "center", justifyContent: "center" },
  markText: { color: "#24466D", fontSize: 12, fontWeight: "900" },
  statusPill: { backgroundColor: "#F0F3F7", borderRadius: 20, paddingHorizontal: 10, paddingVertical: 5 },
  statusText: { color: "#62748A", fontSize: 10, fontWeight: "800" },
  productName: { color: "#1B2D46", fontSize: 17, fontWeight: "800", marginTop: 13 },
  description: { color: "#7C899B", fontSize: 12, lineHeight: 18, marginTop: 5 },
  plan: { color: "#536981", fontSize: 11, fontWeight: "700", marginTop: 13 },
  primaryButton: { minHeight: 42, borderRadius: 11, backgroundColor: "#172C4B", alignItems: "center", justifyContent: "center", paddingHorizontal: 16, marginTop: 15 },
  primaryText: { color: "#FFFFFF", fontSize: 12, fontWeight: "800" },
  disabledButton: { opacity: 0.55 },
  activeButton: { minHeight: 42, borderRadius: 11, backgroundColor: "#EAF5EF", alignItems: "center", justifyContent: "center", marginTop: 15 },
  activeText: { color: "#28734D", fontSize: 12, fontWeight: "800" },
  error: { color: "#A33B3B", backgroundColor: "#FCEEEE", padding: 12, borderRadius: 10, fontSize: 12, lineHeight: 18, marginBottom: 14 },
  loading: { alignItems: "center", gap: 10, padding: 30 },
  empty: { backgroundColor: "#FFFFFF", borderRadius: 16, padding: 20, gap: 8 },
  emptyTitle: { color: "#1B2D46", fontWeight: "800", fontSize: 15 },
  muted: { color: "#7C899B", fontSize: 12, lineHeight: 18, textAlign: "center" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24, gap: 14 },
  footnote: { color: "#98A4B3", fontSize: 10, lineHeight: 16, textAlign: "center", marginTop: 24 },
});
