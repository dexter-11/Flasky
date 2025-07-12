- - -
# Flasky (PHP version)

### 1. Setup environment (LEMP stack - Nginx, PHP)
```bash
sudo apt update
sudo apt install nginx php php-fpm php-xml -y

sudo systemctl start nginx.service
sudo systemctl start php8.4-fpm.service

sudo mkdir -p /var/www/flasky-php
cd /var/www/flasky-php

#Write contents of this directory here

sudo chown -R www-data:www-data /var/www/flasky-php

sudo nano /etc/nginx/sites-available/flasky-php
#server {
#    listen 80;
#    server_name localhost;
#
#    root /var/www/flasky-php;
#    index index.php;
#
#    location / {
#        try_files $uri $uri/ =404;
#    }
#
#    location ~ \.php$ {
#        include snippets/fastcgi-php.conf;
#        fastcgi_pass unix:/var/run/php/php8.4-fpm.sock;
#    }
#
#    location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
#        try_files $uri =404;
#    }
#}

sudo ln -s /etc/nginx/sites-available/flasky-php /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart php*-fpm
```

### 2. XXE in PHP app
Open http://localhost/

