import { create } from 'zustand';
import { toolBridge } from '../bridge/python';

export interface AppState {
  rooted: boolean;
  totalTools: number;
  availableTools: number;
  categories: string[];
  currentCategory: string | null;
  currentTool: string | null;
  toolOutput: string[];
  toolRunning: boolean;
  terminalVisible: boolean;

  setStatus: (status: any) => void;
  setCategory: (cat: string) => void;
  setTool: (tool: string | null) => void;
  appendOutput: (line: string) => void;
  clearOutput: () => void;
  setToolRunning: (running: boolean) => void;
  toggleTerminal: () => void;
  loadStatus: () => Promise<void>;
  executeTool: (tool: string, args: object, executionType: 'native' | 'python') => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  rooted: false,
  totalTools: 0,
  availableTools: 0,
  categories: [],
  currentCategory: null,
  currentTool: null,
  toolOutput: [],
  toolRunning: false,
  terminalVisible: true,

  setStatus: (status) => set({
    rooted: status.rooted || false,
    totalTools: status.total_tools || 0,
    availableTools: status.available_tools || 0,
    categories: status.categories || [],
  }),
  setCategory: (cat) => set({ currentCategory: cat }),
  setTool: (tool) => set({ currentTool: tool, toolOutput: [] }),
  appendOutput: (line) => set((s) => ({ toolOutput: [...s.toolOutput, line] })),
  clearOutput: () => set({ toolOutput: [] }),
  setToolRunning: (running) => set({ toolRunning: running }),
  toggleTerminal: () => set((s) => ({ terminalVisible: !s.terminalVisible })),

  loadStatus: async () => {
    try {
      const status = await toolBridge.getStatus();
      get().setStatus(status);
    } catch {
      // fallback
    }
  },

  executeTool: async (tool, args, executionType) => {
    set({ toolRunning: true, toolOutput: [`[*] Starting ${tool} (${executionType})...`] });
    try {
      const result = await toolBridge.execute(tool, args, executionType);
      if (result.output) {
        result.output.split('\n').forEach((line: string) => get().appendOutput(line));
      }
      if (result.error) {
        get().appendOutput(`[!] Error: ${result.error}`);
      }
      if (result.success && result.exitCode !== undefined) {
        get().appendOutput(`[✓] Exit code: ${result.exitCode}`);
      }
    } catch (e: any) {
      get().appendOutput(`[!] ${e.message}`);
    } finally {
      set({ toolRunning: false });
    }
  },
}));
