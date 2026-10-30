module.exports = {
  apps: [
    {
      name: "nextshift-api",
      cwd: "/home/janidu/workbench/nextshift",
      script: "/home/janidu/.local/bin/uv",
      args: "run uvicorn app.main:app --host 0.0.0.0 --port 8000",
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