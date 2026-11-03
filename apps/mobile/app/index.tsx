import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";

import { useAuth } from "../src/providers/AuthProvider";

const products = [
  { code: "DD", name: "Day-Date", category: "Lifestyle", description: "Build meaningful connections", state: "Planned" },
  { code: "NM", name: "Nexora Muslim", category: "Faith & daily life", description: "A thoughtful companion for everyday life", state: "Planned" },
  { code: "DG", name: "Dignity", category: "Learning", description: "Learning, campus and personal growth", state: "Planned" },
  { code: "NV", name: "Nexverse", category: "Digital media", description: "Books, stories and entertainment", state: "Planned" },
] as const;

function ProductCard({
  code,
  name,
  category,
  description,
  state,
}: (typeof products)[number]) {
  return (
    <View style={styles.productCard}>
      <View style={styles.productTop}>
        <View style={styles.productMark}>
          <Text style={styles.productMarkText}>{code}</Text>
        </View>
        <View style={styles.productState}>
          <View style={styles.stateDot} />
          <Text style={styles.stateText}>{state}</Text>
        </View>
      </View>
      <Text style={styles.productCategory}>{category}</Text>
      <Text style={styles.productName}>{name}</Text>
      <Text style={styles.productDescription}>{description}</Text>
    </View>
  );
}

export default function HomeScreen() {
  const { status, user, signOut } = useAuth();
  const authStatusLabel = status === "loading"
    ? "Checking account session"
    : status === "signed-in"
      ? `Signed in · ${user?.displayName ?? user?.email ?? "Nexora account"}`
      : status === "signed-out"
        ? "Firebase connected · Not signed in"
        : status === "unconfigured"
          ? "Firebase client configuration required"
          : "Authentication unavailable";

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View style={styles.brand}>
            <View style={styles.brandMark}><Text style={styles.brandMarkText}>N</Text></View>
            <View>
              <Text style={styles.brandName}>NEXORA</Text>
              <Text style={styles.brandCaption}>UNIVERSAL PLATFORM</Text>
            </View>
          </View>
          <Pressable onPress={() => router.push(status === "signed-in" ? "/account" : "/auth")} style={styles.avatar}><Text style={styles.avatarText}>{status === "signed-in" ? (user?.displayName?.[0] ?? user?.email?.[0] ?? "N").toUpperCase() : "↗"}</Text></Pressable>
        </View>

        <View style={styles.hero}>
          <Text style={styles.heroEyebrow}>ONE ACCOUNT. CONNECTED EXPERIENCES.</Text>
          <Text style={styles.heroTitle}>Your digital world,{"\n"}in one place.</Text>
          <Text style={styles.heroBody}>
            A shared foundation for Nexora products, designed around one identity and clear
            boundaries for every service.
          </Text>
          <View style={styles.heroFoot}>
            <View style={[styles.onlineDot, status !== "signed-in" && styles.pendingDot]} />
            <Text style={styles.heroFootText}>{authStatusLabel}</Text>
          </View>
        </View>

        <View style={styles.accountCard}>\n          <View style={styles.accountCopy}>\n            <Text style={styles.accountTitle}>{status === "signed-in" ? "Your Nexora account" : "Get started with Nexora"}</Text>\n            <Text style={styles.accountBody}>{status === "signed-in" ? (user?.email ?? "Your account is connected") : "Sign in or create an account to access your connected products."}</Text>\n          </View>\n          {status === "signed-in" ? (\n            <Pressable onPress={() => router.push("/account")} style={styles.accountButton}><Text style={styles.accountButtonText}>Manage</Text></Pressable>\n          ) : (\n            <Pressable onPress={() => router.push("/auth")} style={styles.accountButton}><Text style={styles.accountButtonText}>Continue</Text></Pressable>\n          )}\n        </View>\n\n        <View style={styles.sectionHeading}>
          <View>
            <Text style={styles.sectionEyebrow}>THE ECOSYSTEM</Text>
            <Text style={styles.sectionTitle}>Explore Nexora</Text>
          </View>
          <Text style={styles.count}>04 PRODUCTS</Text>
        </View>

        <View style={styles.productList}>
          {products.map((product) => <ProductCard key={product.code} {...product} />)}
        </View>

        <View style={styles.securityCard}>
          <View style={styles.securityIcon}><Text style={styles.securityIconText}>✳</Text></View>
          <View style={styles.securityCopy}>
            <Text style={styles.securityTitle}>Your account, your boundaries</Text>
            <Text style={styles.securityBody}>
              Each Nexora product will request only the access it needs. Your data stays separated
              by product and permission.
            </Text>
          </View>
        </View>

        <Text style={styles.footer}>NEXORA PLATFORM  •  BUILDING WHAT’S NEXT</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F4F6FA" },
  content: { paddingHorizontal: 22, paddingTop: 10, paddingBottom: 32, maxWidth: 680, width: "100%", alignSelf: "center" },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 28 },
  brand: { flexDirection: "row", alignItems: "center", gap: 11 },
  brandMark: { width: 42, height: 42, borderRadius: 14, backgroundColor: "#172C4B", alignItems: "center", justifyContent: "center" },
  brandMarkText: { color: "#FFFFFF", fontSize: 25, fontWeight: "900" },
  brandName: { color: "#172C4B", fontSize: 14, fontWeight: "900", letterSpacing: 2.2 },
  brandCaption: { color: "#8290A4", fontSize: 8, fontWeight: "800", letterSpacing: 1.5, marginTop: 3 },
  avatar: { width: 38, height: 38, borderRadius: 19, backgroundColor: "#E5EAF2", alignItems: "center", justifyContent: "center" },
  avatarText: { color: "#52647D", fontWeight: "800", fontSize: 14 },
  hero: { borderRadius: 25, padding: 24, backgroundColor: "#172C4B", overflow: "hidden" },
  heroEyebrow: { color: "#9CB6D8", fontSize: 9, letterSpacing: 1.5, fontWeight: "800" },
  heroTitle: { color: "#FFFFFF", fontSize: 34, lineHeight: 39, fontWeight: "800", marginTop: 17, letterSpacing: -0.8 },
  heroBody: { color: "#C0CDDE", fontSize: 13, lineHeight: 21, marginTop: 14, maxWidth: 420 },
  heroFoot: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 23 },
  onlineDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: "#65D6A8" },
  pendingDot: { backgroundColor: "#D7B66A" },
  heroFootText: { color: "#D3E1F1", fontSize: 10, fontWeight: "700" },
  accountCard: { flexDirection: "row", alignItems: "center", gap: 12, backgroundColor: "#FFFFFF", borderRadius: 17, borderWidth: 1, borderColor: "#E9EDF3", padding: 15, marginTop: 15 },\n  accountCopy: { flex: 1 },\n  accountTitle: { color: "#1B2D46", fontSize: 12, fontWeight: "800" },\n  accountBody: { color: "#7C899B", fontSize: 10, lineHeight: 15, marginTop: 4 },\n  accountButton: { paddingHorizontal: 15, paddingVertical: 10, backgroundColor: "#172C4B", borderRadius: 10 },\n  accountButtonText: { color: "#FFFFFF", fontSize: 10, fontWeight: "800" },\n  sectionHeading: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end", marginTop: 30, marginBottom: 14 },
  sectionEyebrow: { color: "#8997AA", fontSize: 9, fontWeight: "800", letterSpacing: 1.7 },
  sectionTitle: { color: "#1B2D46", fontSize: 22, fontWeight: "800", marginTop: 5 },
  count: { color: "#8997AA", fontSize: 9, fontWeight: "800", letterSpacing: 1 },
  productList: { gap: 11 },
  productCard: { backgroundColor: "#FFFFFF", borderRadius: 18, borderWidth: 1, borderColor: "#E9EDF3", padding: 17 },
  productTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  productMark: { width: 36, height: 36, borderRadius: 11, backgroundColor: "#EEF2F8", alignItems: "center", justifyContent: "center" },
  productMarkText: { color: "#263E5E", fontSize: 11, fontWeight: "900" },
  productState: { flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 9, paddingVertical: 5, backgroundColor: "#F2F4F7", borderRadius: 20 },
  stateDot: { width: 5, height: 5, borderRadius: 3, backgroundColor: "#9AA7B7" },
  stateText: { color: "#77869A", fontSize: 9, fontWeight: "700" },
  productCategory: { color: "#8190A4", fontSize: 9, fontWeight: "800", letterSpacing: 1.1, marginTop: 14 },
  productName: { color: "#1B2D46", fontSize: 17, fontWeight: "800", marginTop: 4 },
  productDescription: { color: "#7C899B", fontSize: 11, lineHeight: 17, marginTop: 5 },
  securityCard: { flexDirection: "row", gap: 13, backgroundColor: "#EAF0F7", borderRadius: 18, padding: 17, marginTop: 18 },
  securityIcon: { width: 34, height: 34, borderRadius: 11, backgroundColor: "#D9E4F1", alignItems: "center", justifyContent: "center" },
  securityIconText: { color: "#315477", fontSize: 20, fontWeight: "700" },
  securityCopy: { flex: 1 },
  securityTitle: { color: "#294563", fontSize: 12, fontWeight: "800" },
  securityBody: { color: "#63778F", fontSize: 10, lineHeight: 16, marginTop: 5 },
  footer: { color: "#A3ADBA", fontSize: 8, fontWeight: "800", letterSpacing: 1.3, textAlign: "center", marginTop: 27 },
});
