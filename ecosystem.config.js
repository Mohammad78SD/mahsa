// pm2 process definition. Run from the project root with the virtualenv
// activated and the environment from .env loaded:
//   set -a; source .env; set +a; pm2 start ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'mahsa',
      script: 'gunicorn',
      args: `MetafanLunch.wsgi:application --bind 0.0.0.0:${process.env.PORT || 8002}`,
      interpreter: 'none',
      cwd: __dirname,
      merge_logs: true,
      autorestart: true,
      log_file: 'logs/combined.outerr.log',
      out_file: 'logs/out.log',
      error_file: 'logs/err.log',
      log_date_format: 'YYYY-MM-DD HH:mm Z',
      watch: false,
      max_memory_restart: '1G',
    },
  ],
};
