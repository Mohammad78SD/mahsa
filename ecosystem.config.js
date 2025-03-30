module.exports = {
  apps : [{
    name: 'Panel',
    script: '  gunicorn MetafanLunch.wsgi:application --bind 0.0.0.0:8002;  ',
    args: 'one two',
    merge_logs: true,
    autorestart: true,
    log_file: "logs/combined.outerr.log",
    out_file: "logs/out.log",
    error_file: "logs/err.log",
    log_date_format : "YYYY-MM-DD HH:mm Z",
    append_env_to_name: true,
    watch: false,
    max_memory_restart: '5G',
  }],

};
