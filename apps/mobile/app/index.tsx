import { StyleSheet, Text, View } from "react-native";

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.mark}>
        <Text style={styles.markText}>N</Text>
      </View>
      <Text style={styles.eyebrow}>NEXORA PLATFORM</Text>
      <Text style={styles.title}>One platform.{ "\n" }Many possibilities.</Text>
      <Text style={styles.description}>
        A connected foundation for Nexora products, built with clear boundaries,
        secure identity, and room to grow.
      </Text>
      <View style={styles.status}>
        <View style={styles.dot} />
        <Text style={styles.statusText}>Platform foundation initialized</Text>
      </View>
      <Text style={styles.footer}>A better way to build what’s next.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 28,
    paddingVertical: 48,
    backgroundColor: "#F7F8FA",
  },
  mark: {
    width: 54,
    height: 54,
    borderRadius: 17,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#152B4A",
    marginBottom: 28,
  },
  markText: { color: "#FFFFFF", fontSize: 29, fontWeight: "800" },
  eyebrow: { color: "#55708F", fontSize: 11, fontWeight: "800", letterSpacing: 2.4 },
  title: { color: "#14243A", fontSize: 35, lineHeight: 42, fontWeight: "800", marginTop: 13 },
  description: { color: "#66758A", fontSize: 15, lineHeight: 24, marginTop: 17, maxWidth: 420 },
  status: { flexDirection: "row", alignItems: "center", marginTop: 34, gap: 9 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: "#239B73" },
  statusText: { color: "#315B50", fontSize: 12, fontWeight: "700" },
  footer: { position: "absolute", bottom: 28, left: 28, color: "#9AA6B5", fontSize: 11 },
});
