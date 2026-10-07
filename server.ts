import express, { Request, Response } from 'express';
import { createServer as createViteServer } from 'vite';
import { spawn, ChildProcess } from 'child_process';
import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = 3000;
const FLASK_PORT = 5000;
let flaskProcess: ChildProcess | null = null;

function startFlaskBackend() {
  console.log('[Runner] Starting Python Flask backend on port ' + FLASK_PORT + '...');
  flaskProcess = spawn('python3', ['backend/app.py'], {
    cwd: __dirname,
    stdio: 'inherit',
    env: {
      ...process.env,
      PORT: String(FLASK_PORT),
      FLASK_ENV: 'development',
      FLASK_DEBUG: '0',
    },
  });

  flaskProcess.on('error', (err) => {
    console.error('[Flask] Failed to start Python process:', err);
  });

  flaskProcess.on('exit', (code, signal) => {
    console.log(`[Flask] Process exited with code ${code} and signal ${signal}`);
  });
}

// Clean up child process on exit
process.on('exit', () => {
  if (flaskProcess) flaskProcess.kill();
});
process.on('SIGINT', () => {
  if (flaskProcess) flaskProcess.kill();
  process.exit();
});
process.on('SIGTERM', () => {
  if (flaskProcess) flaskProcess.kill();
  process.exit();
});

async function startServer() {
  // Start the Python Flask backend
  startFlaskBackend();

  const app = express();

  // Proxy /api requests to Flask backend at localhost:5000
  app.use('/api', (req: Request, res: Response) => {
    const targetPath = `/api${req.url === '/' ? '' : req.url}`;
    const proxyReq = http.request(
      {
        hostname: '127.0.0.1',
        port: FLASK_PORT,
        path: targetPath,
        method: req.method,
        headers: {
          ...req.headers,
          host: `127.0.0.1:${FLASK_PORT}`,
        },
      },
      (proxyRes) => {
        res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
        proxyRes.pipe(res);
      }
    );

    proxyReq.on('error', (err) => {
      console.warn(`[Proxy Error] Unable to connect to Flask on port ${FLASK_PORT}:`, err.message);
      res.status(502).json({
        error: 'Bad Gateway: Flask backend is unreachable or still starting',
        details: err.message,
      });
    });

    req.pipe(proxyReq);
  });

  // Check NODE_ENV to determine whether to use Vite dev middleware or serve static files
  const isProd = process.env.NODE_ENV === 'production';

  if (!isProd) {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[Server] Application listening on http://0.0.0.0:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error('[Server Error] Failed to start server:', err);
});
