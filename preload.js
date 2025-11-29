/**
 * Preload script for secure IPC communication between Electron main process and renderer.
 * This uses contextBridge to expose only specific APIs to the renderer process,
 * preventing direct access to Node.js and Electron internals.
 */
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // File dialog handlers
    showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
    showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),

    // Notification handler
    showNotification: (title, body) => ipcRenderer.send('show-notification', title, body),

    // Listen for files selected from menu
    onFilesSelected: (callback) => {
        // Remove any existing listeners to prevent duplicates
        ipcRenderer.removeAllListeners('files-selected');
        ipcRenderer.on('files-selected', (event, filePaths) => callback(filePaths));
    },

    // Check if running in Electron
    isElectron: true
});
