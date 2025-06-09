- - -
# Flasky (PHP version)

### 1. Setup environment (LEMP stack - Nginx, PHP)
```bash
sudo apt update
sudo apt install nginx php php-fpm -y

sudo systemctl start nginx.service
sudo systemctl start php8.4-fpm.service

sudo apt install php-xml -y
sudo systemctl restart php*-fpm

sudo mkdir -p /var/www/flasky-php
cd /var/www/flasky-php

#Write contents of this directory here

sudo chown -R www-data:www-data /var/www/flasky-php

sudo nano /etc/nginx/sites-available/flasky-php
#server {
#    listen 80;
#    server_name localhost;
#
#    root /var/www/xxe-php-app;
#    index index.php;
#
#    location / {
#        try_files $uri $uri/ =404;
#    }
#
#    location ~ \.php$ {
#        include snippets/fastcgi-php.conf;
#        fastcgi_pass unix:/var/run/php/php-fpm.sock;
#    }
#
#    location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
#        try_files $uri =404;
#    }
#}

sudo ln -s /etc/nginx/sites-available/flasky-php /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. XXE in PHP app
Open http://localhost/

