# Nginx Integration Guide for Docker Deployment

## Current Setup Compatibility

Based on your existing configuration:

- ✅ Domain: `resmatch-api.ddns.net`
- ✅ HTTPS: Certbot SSL certificates
- ✅ Reverse proxy: Nginx → Backend service

## Recommended Nginx Configuration

Your existing Nginx config should work perfectly with the Docker setup. Here's the optimal configuration:

### `/etc/nginx/sites-available/resmatch`

```nginx
server {
    listen 80;
    server_name resmatch-api.ddns.net;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name resmatch-api.ddns.net;

    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/resmatch-api.ddns.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/resmatch-api.ddns.net/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy to Docker container
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (optional - for monitoring)
    location /healthz {
        proxy_pass http://127.0.0.1:8000/healthz;
        access_log off;
    }

    # Prevent access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

## Integration Steps

### 1. Verify Current Configuration

```bash
# Check current Nginx config
sudo nginx -t

# View current sites
ls -la /etc/nginx/sites-enabled/

# Check SSL certificate status
sudo certbot certificates
```

### 2. Update Docker Port Binding

Ensure your Docker container binds to `127.0.0.1:8000` only:

```yaml
# In /opt/resmatch/docker-compose.yml
services:
  api:
    ports:
      - "127.0.0.1:8000:8000" # ✅ Correct: Private binding
```

### 3. Test Integration

After deployment:

```bash
# Test internal connection (from EC2)
curl http://127.0.0.1:8000/healthz

# Test external HTTPS connection
curl https://resmatch-api.ddns.net/healthz

# Test CORS headers
curl -i -X OPTIONS 'https://resmatch-api.ddns.net/api/v1/auth/token' \
  -H 'Origin: https://res-match-ui.vercel.app' \
  -H 'Access-Control-Request-Method: POST'
```

## Certbot Auto-Renewal

Your existing Certbot setup should continue working. Verify:

```bash
# Check renewal configuration
sudo systemctl status certbot.timer

# Test renewal
sudo certbot renew --dry-run
```

## Monitoring & Logs

### Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### Docker Container Logs

```bash
# Application logs
docker logs -f resmatch-api

# Health check logs
docker logs resmatch-api 2>&1 | grep healthz
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**

   ```bash
   # Check if Docker container is running
   docker ps | grep resmatch-api

   # Check if port 8000 is listening
   netstat -tulpn | grep :8000
   ```

2. **CORS Issues**

   ```bash
   # Verify CORS configuration in container
   docker exec resmatch-api python -c "
   from app.core.config import settings
   print('CORS origins:', settings.BACKEND_CORS_ORIGINS)
   "
   ```

3. **SSL Issues**
   ```bash
   # Check certificate validity
   openssl x509 -in /etc/letsencrypt/live/resmatch-api.ddns.net/cert.pem -text -noout | grep "Not After"
   ```

## Performance Optimization

### Nginx Optimization

Add to your server block:

```nginx
# Gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# Client body size (for file uploads)
client_max_body_size 10M;

# Connection optimization
keepalive_timeout 65;
```

### Docker Container Optimization

Your Docker setup already includes:

- ✅ Health checks
- ✅ Log rotation
- ✅ Resource limits
- ✅ Non-root user

## Backup Considerations

```bash
# Backup Nginx config
sudo cp -r /etc/nginx/sites-available /opt/backups/nginx-$(date +%Y%m%d)/

# Backup SSL certificates (automatic with Certbot)
# Certificates are automatically backed up in /etc/letsencrypt/
```
