FROM openresty/openresty:1.19.3.1-bionic

ARG PROJECT_PATH=/nginx
RUN mkdir -p /nginx/logs

COPY ./neursafe_fl/proxy/lua ${PROJECT_PATH}/lua
COPY ./deploy/configs/proxy/start_nginx.sh /nginx/start_nginx.sh
RUN chmod +x /nginx/start_nginx.sh

RUN luarocks install luasocket
RUN luarocks install lua-cjson

WORKDIR /nginx

RUN apt update && apt install -y s3fs
