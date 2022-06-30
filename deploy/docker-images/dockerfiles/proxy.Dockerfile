FROM openresty/openresty:1.19.3.1-bionic

ARG PROJECT_PATH=/nginx
RUN mkdir -p /nginx/logs
COPY ./deploy/configs/proxy/lua ${PROJECT_PATH}/lua

RUN luarocks install luasocket
RUN luarocks install lua-cjson

WORKDIR /nginx

CMD ["nginx", "-p", "/nginx", "-c", "/nginx/conf/nginx.conf", "-g", "daemon off;"]
