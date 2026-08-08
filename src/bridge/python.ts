import { NativeModules, Platform } from 'react-native';
import { EventEmitter } from 'events';

const { BinaryExecutor, ChaquopyBridge } = NativeModules;

/**
 * Bridge client — routes tool execution to the correct backend:
 * - Native binaries → Java BinaryExecutor (direct exec)
 * - Python tools → Chaquopy py_runner (embedded Python)
 */
class ToolBridge extends EventEmitter {
  private connected = false;

  connect() {
    this.connected = true;
    this.emit('connected');
  }

  /**
   * Execute a native binary tool directly via Java.
   * No Python involved — binary runs directly from assets/binaries/.
   */
  async executeNative(toolName: string, args: object): Promise<any> {
    if (!BinaryExecutor) {
      return { success: false, error: 'BinaryExecutor not available' };
    }
    return await BinaryExecutor.executeNative(toolName, args);
  }

  /**
   * Execute a Python-native tool via Chaquopy.
   * Runs the actual tool source code (sqlmap, nikto, routersploit, etc.)
   */
  async executePython(toolName: string, args: object): Promise<any> {
    if (!ChaquopyBridge) {
      return { success: false, error: 'ChaquopyBridge not available' };
    }
    return await ChaquopyBridge.executePythonTool(toolName, args);
  }

  /**
   * Smart route: picks native or Python based on tool type.
   */
  async execute(toolName: string, args: object, executionType: 'native' | 'python'): Promise<any> {
    if (executionType === 'python') {
      return this.executePython(toolName, args);
    }
    return this.executeNative(toolName, args);
  }

  async getStatus(): Promise<any> {
    if (!ChaquopyBridge) return { rooted: false, total_tools: 0, available_tools: 0 };
    return await ChaquopyBridge.getStatus();
  }

  async getAvailableTools(): Promise<any[]> {
    if (!ChaquopyBridge) return [];
    return await ChaquopyBridge.getAvailableTools();
  }

  disconnect() {
    this.connected = false;
    this.emit('disconnected');
  }
}

export const toolBridge = new ToolBridge();
export default toolBridge;
