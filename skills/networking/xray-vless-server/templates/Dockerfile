FROM alpine:latest

RUN apk add --no-cache wget unzip

RUN wget -O /tmp/xray.zip https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip \
    && mkdir -p /usr/local/bin \
    && unzip /tmp/xray.zip -d /usr/local/bin \
    && rm /tmp/xray.zip \
    && chmod +x /usr/local/bin/xray

COPY server.crt server.key xray-config.json /etc/xray/

CMD ["/usr/local/bin/xray", "run", "-c", "/etc/xray/config.json"]