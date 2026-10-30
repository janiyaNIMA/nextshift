module.exports = {
  apps: [
    {
      name: "nextshift-api",
      cwd: "/root/Projects/nextshift",
      script: "/root/Projects/nextshift/.venv/bin/python",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 2000,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};