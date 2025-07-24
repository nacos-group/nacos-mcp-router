#!/bin/bash

set -e

VALUES_FILE="helm/values.yaml"

# 生成随机字符串，至少8位，纯 Bash 实现
rand_str() {
  length=$1
  chars=({A..Z} {a..z} {0..9})
  result=""
  for ((i=0; i<length; i++)); do
    index=$((RANDOM % ${#chars[@]}))
    result="${result}${chars[$index]}"
  done
  echo "$result"
}

# 生成 base64 token，原始长度大于32字节（如40字节）
rand_token() {
  head -c 40 </dev/urandom | base64
}

MYSQL_SERVICE_PASSWORD=$(rand_str 16)  # 至少8位，这里用16位更安全
NACOS_AUTH_TOKEN=$(rand_token)
NACOS_AUTH_IDENTITY_KEY=$(rand_str 12)
NACOS_AUTH_IDENTITY_VALUE=$(rand_str 12)

# 替换 values.yaml 中的对应字段，兼容空字符串和任意内容，分隔符用 # 防止 base64 冲突
sed -i '' "s#\(MYSQL_SERVICE_PASSWORD:\)[ ]*\"[^\"]*\"#\1 \"$MYSQL_SERVICE_PASSWORD\"#" $VALUES_FILE
sed -i '' "s#\(NACOS_AUTH_TOKEN:\)[ ]*\"[^\"]*\"#\1 \"$NACOS_AUTH_TOKEN\"#" $VALUES_FILE
sed -i '' "s#\(NACOS_AUTH_IDENTITY_KEY:\)[ ]*\"[^\"]*\"#\1 \"$NACOS_AUTH_IDENTITY_KEY\"#" $VALUES_FILE
sed -i '' "s#\(NACOS_AUTH_IDENTITY_VALUE:\)[ ]*\"[^\"]*\"#\1 \"$NACOS_AUTH_IDENTITY_VALUE\"#" $VALUES_FILE
# nacosMcpRouter.env.NACOS_PASSWORD
sed -i '' "s#\(NACOS_PASSWORD:\)[ ]*\"[^\"]*\"#\1 \"$MYSQL_SERVICE_PASSWORD\"#" $VALUES_FILE
# mysql.env.MYSQL_PASSWORD
sed -i '' "s#\(MYSQL_PASSWORD:\)[ ]*\"[^\"]*\"#\1 \"$MYSQL_SERVICE_PASSWORD\"#" $VALUES_FILE

echo "已随机生成并注入新值："
echo "MYSQL_SERVICE_PASSWORD / NACOS_PASSWORD / MYSQL_PASSWORD: $MYSQL_SERVICE_PASSWORD"
echo "NACOS_AUTH_TOKEN: $NACOS_AUTH_TOKEN"
echo "NACOS_AUTH_IDENTITY_KEY: $NACOS_AUTH_IDENTITY_KEY"
echo "NACOS_AUTH_IDENTITY_VALUE: $NACOS_AUTH_IDENTITY_VALUE" 