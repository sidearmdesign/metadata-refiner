const { app, BrowserWindow, dialog, ipcMain, shell, Menu, Tray } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const net = require('net');

// Keep a global reference of the window object
let mainWindow;
let flaskProcess;
let serverPort = 5001;
let tray = null;

// Check if port is available
function checkPort(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.listen(port, () => {
      server.once('close', () => resolve(true));
      server.close();
    });
    server.on('error', () => resolve(false));
  });
}

// Find available port starting from 5001
async function findAvailablePort() {
  let port = 5001;
  while (port < 5100) {
    if (await checkPort(port)) {
      return port;
    }
    port++;
  }
  throw new Error('No available port found');
}

// Start Flask server
async function startFlaskServer() {
  try {
    serverPort = await findAvailablePort();
    console.log(`Starting Flask server on port ${serverPort}`);
    
    const pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
    const appPath = app.isPackaged ? 
      path.join(process.resourcesPath, 'app') : 
      __dirname;
    
    // Set environment variables
    const env = {
      ...process.env,
      FLASK_ENV: 'production',
      FLASK_DEBUG: '0',
      PORT: serverPort.toString()
    };
    
    flaskProcess = spawn(pythonExecutable, [path.join(appPath, 'app.py')], {
      env,
      cwd: appPath,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    flaskProcess.stdout.on('data', (data) => {
      console.log(`Flask stdout: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
      console.error(`Flask stderr: ${data}`);
    });

    flaskProcess.on('close', (code) => {
      console.log(`Flask process exited with code ${code}`);
    });

    // Wait a bit for server to start
    await new Promise(resolve => setTimeout(resolve, 3000));
    
  } catch (error) {
    console.error('Error starting Flask server:', error);
    throw error;
  }
}

// Stop Flask server
function stopFlaskServer() {
  if (flaskProcess) {
    console.log('Stopping Flask server...');
    flaskProcess.kill();
    flaskProcess = null;
  }
}

// Create the browser window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false
    },
    icon: path.join(__dirname, 'static/resources/icon.png'),
    title: 'MetaData Refiner',
    show: false // Don't show until ready
  });

  // Load the app
  mainWindow.loadURL(`http://localhost:${serverPort}`);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Open DevTools in development
  if (!app.isPackaged) {
    mainWindow.webContents.openDevTools();
  }
}

// Create system tray
function createTray() {
  const iconPath = path.join(__dirname, 'static/resources/tray-icon.png');
  
  // Use default icon if custom not found
  if (!fs.existsSync(iconPath)) {
    return;
  }
  
  tray = new Tray(iconPath);
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show App',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: 'Quit',
      click: () => {
        app.quit();
      }
    }
  ]);
  
  tray.setToolTip('MetaData Refiner');
  tray.setContextMenu(contextMenu);
  
  // Double click to show app
  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

// Create application menu
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Images...',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const result = await dialog.showOpenDialog(mainWindow, {
              properties: ['openFile', 'multiSelections'],
              filters: [
                { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'] },
                { name: 'All Files', extensions: ['*'] }
              ]
            });
            
            if (!result.canceled) {
              mainWindow.webContents.send('files-selected', result.filePaths);
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About MetaData Refiner',
              message: 'MetaData Refiner',
              detail: 'AI-powered image metadata generation tool\nVersion 1.0.0'
            });
          }
        }
      ]
    }
  ];

  // macOS specific menu adjustments
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    });
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// App event handlers
app.whenReady().then(async () => {
  try {
    await startFlaskServer();
    createWindow();
    createMenu();
    createTray();
  } catch (error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox('Startup Error', 'Failed to start the application server. Please try again.');
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  stopFlaskServer();
});

// Handle IPC messages
ipcMain.handle('show-save-dialog', async (event, options) => {
  const result = await dialog.showSaveDialog(mainWindow, options);
  return result;
});

ipcMain.handle('show-open-dialog', async (event, options) => {
  const result = await dialog.showOpenDialog(mainWindow, options);
  return result;
});

// Handle notifications
ipcMain.on('show-notification', (event, title, body) => {
  new Notification(title, { body }).show();
});

// Prevent navigation away from app
app.on('web-contents-created', (event, contents) => {
  contents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    
    if (parsedUrl.origin !== `http://localhost:${serverPort}`) {
      event.preventDefault();
    }
  });
});