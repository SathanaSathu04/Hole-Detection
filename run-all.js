const { spawn } = require('child_process');
const path = require('path');

const rootDir = __dirname;
const isWin = process.platform === 'win32';

console.log('\x1b[36m%s\x1b[0m', '===================================================');
console.log('\x1b[32m%s\x1b[0m', '🚀 Launching Textile Thread Insertion System...');
console.log('\x1b[36m%s\x1b[0m', '===================================================');

// 1. Launch FastAPI Backend
const pythonUvicorn = isWin
  ? path.join(rootDir, 'backend', 'venv', 'Scripts', 'uvicorn.exe')
  : path.join(rootDir, 'backend', 'venv', 'bin', 'uvicorn');

const backendProcess = spawn(
  pythonUvicorn,
  ['app.main:app', '--reload', '--host', '127.0.0.1', '--port', '8000'],
  { cwd: path.join(rootDir, 'backend'), stdio: 'inherit', shell: true }
);

console.log('\x1b[33m%s\x1b[0m', '➜ Backend starting at:  http://127.0.0.1:8000 (Swagger: http://127.0.0.1:8000/docs)');

// 2. Launch Angular Frontend
const npmCmd = isWin ? 'npm.cmd' : 'npm';
const frontendProcess = spawn(
  npmCmd,
  ['start'],
  { cwd: path.join(rootDir, 'frontend'), stdio: 'inherit', shell: true }
);

console.log('\x1b[35m%s\x1b[0m', '➜ Frontend starting at: http://localhost:4200');

function cleanup() {
  console.log('\nStopping servers...');
  backendProcess.kill();
  frontendProcess.kill();
  process.exit();
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
