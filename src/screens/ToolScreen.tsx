import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput,
  StatusBar, Switch, ActivityIndicator,
} from 'react-native';
import { useAppStore } from '../store/appStore';
import { Terminal } from '../components/Terminal';

// Tools that are natively Python (run via Chaquopy)
const PYTHON_TOOLS = new Set([
  'sqlmap', 'nikto', 'wfuzz', 'routersploit', 'maigret', 'holehe',
  'photon', 'instaloader', 'snscrape', 'h8mail', 'osintgram',
  'volatility', 'hash-identifier', 'cewl', 'binwalk', 'wifite', 'airgeddon',
  'impacket', 'phoneinfoga',
]);

export function ToolScreen({ route, navigation }: any) {
  const { tool, category } = route.params;
  const { executeTool, toolOutput, toolRunning, appendOutput, clearOutput, rooted } = useAppStore();

  const [target, setTarget] = useState('');
  const [port, setPort] = useState('');
  const [extraArgs, setExtraArgs] = useState('');
  const [verbose, setVerbose] = useState(false);
  const [aggressive, setAggressive] = useState(false);
  const [showTerminal, setShowTerminal] = useState(true);

  const executionType = PYTHON_TOOLS.has(tool) ? 'python' : 'native';

  const handleStart = async () => {
    clearOutput();
    appendOutput(`[*] Starting ${tool} (${executionType})...`);
    if (target) appendOutput(`[*] Target: ${target}`);
    const args: any = {};
    if (target) args.target = target;
    if (port) args.port = parseInt(port);
    if (extraArgs) args.extra = extraArgs;
    if (verbose) args.verbose = true;
    if (aggressive) args.aggressive = true;
    args.timeout = 300;
    await executeTool(tool, args, executionType);
  };

  const handleStop = () => {
    appendOutput(`[!] Stopping ${tool}...`);
    // Signal stop via bridge
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0f" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{tool}</Text>
        <View style={styles.subHeader}>
          <Text style={styles.subtitle}>{category}</Text>
          <View style={[styles.execBadge, executionType === 'python' ? styles.execPython : styles.execNative]}>
            <Text style={styles.execText}>{executionType === 'python' ? 'Python' : 'Native'}</Text>
          </View>
        </View>
      </View>

      <ScrollView style={styles.content}>
        {/* Target Input */}
        <View style={styles.section}>
          <Text style={styles.label}>Target</Text>
          <TextInput
            style={styles.input}
            value={target}
            onChangeText={setTarget}
            placeholder="IP address or URL"
            placeholderTextColor="#555"
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Port (optional)</Text>
          <TextInput
            style={styles.input}
            value={port}
            onChangeText={setPort}
            placeholder="e.g., 80, 443"
            placeholderTextColor="#555"
            keyboardType="numeric"
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.label}>Extra Arguments</Text>
          <TextInput
            style={styles.input}
            value={extraArgs}
            onChangeText={setExtraArgs}
            placeholder="Additional CLI args"
            placeholderTextColor="#555"
          />
        </View>

        {/* Toggles */}
        <View style={styles.toggleRow}>
          <Text style={styles.toggleLabel}>Verbose</Text>
          <Switch value={verbose} onValueChange={setVerbose} trackColor={{ false: '#333', true: '#4ecdc4' }} />
        </View>
        <View style={styles.toggleRow}>
          <Text style={styles.toggleLabel}>Aggressive</Text>
          <Switch value={aggressive} onValueChange={setAggressive} trackColor={{ false: '#333', true: '#4ecdc4' }} />
        </View>

        {/* Action Buttons */}
        <View style={styles.btnRow}>
          <TouchableOpacity
            style={[styles.btn, styles.btnStart, toolRunning && styles.btnDisabled]}
            onPress={handleStart}
            disabled={toolRunning}
          >
            {toolRunning ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={styles.btnText}>▶ Start</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity style={[styles.btn, styles.btnStop]} onPress={handleStop}>
            <Text style={styles.btnText}>⏹ Stop</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.toggleTerminal} onPress={() => setShowTerminal(!showTerminal)}>
          <Text style={styles.toggleTerminalText}>
            {showTerminal ? '▼ Hide Terminal' : '▶ Show Terminal'}
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Terminal Output */}
      {showTerminal && <Terminal output={toolOutput} />}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  header: { paddingTop: 50, paddingHorizontal: 20, paddingBottom: 12, borderBottomWidth: 1, borderBottomColor: '#1a1a2e' },
  backBtn: { marginBottom: 6 },
  backText: { color: '#4ecdc4', fontSize: 14 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#fff' },
  subHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 2 },
  subtitle: { fontSize: 12, color: '#888' },
  execBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  execPython: { backgroundColor: '#6c5ce7' },
  execNative: { backgroundColor: '#00b894' },
  execText: { fontSize: 10, color: '#fff', fontWeight: '700' },
  content: { flex: 1, padding: 16 },
  section: { marginBottom: 14 },
  label: { fontSize: 13, color: '#aaa', marginBottom: 6, fontWeight: '600' },
  input: {
    backgroundColor: '#12121a', borderWidth: 1, borderColor: '#2a2a3e',
    borderRadius: 10, padding: 12, color: '#fff', fontSize: 14,
  },
  toggleRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#1a1a2e',
  },
  toggleLabel: { fontSize: 14, color: '#ddd' },
  btnRow: { flexDirection: 'row', gap: 12, marginTop: 16 },
  btn: { flex: 1, padding: 14, borderRadius: 12, alignItems: 'center' },
  btnStart: { backgroundColor: '#00b894' },
  btnStop: { backgroundColor: '#d63031' },
  btnDisabled: { opacity: 0.5 },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  toggleTerminal: { marginTop: 16, padding: 10, alignItems: 'center' },
  toggleTerminalText: { color: '#4ecdc4', fontSize: 13 },
});
