#!/usr/bin/env bash

set -e
mount_path=$1
nginx_conf_path=$2

mkdir -p $mount_path
# if storage is s3, mount first

if [ "$STORAGE_TYPE" = "s3" ]; then
  echo $S3_ACCESS_KEY:$S3_SECRET_KEY > /.passwd-s3fs
  chmod 600 /.passwd-s3fs
  s3fs $WORKSPACE_BUCKET $mount_path  -o no_check_certificate -o passwd_file=/.passwd-s3fs -o use_path_request_style -o url=$S3_ENDPOINT -o allow_other

  echo "S3FS mounting."

  num=1
  while (($num <= 10))
  do
    if mountpoint -q $mount_path; then
        echo "$mount_path already mounted."
        break
    else
        echo "$mount_path is mounting."
        ((num++))
        sleep 1
    fi
  done

  if (($num > 10)); then
    echo "$mount_path mount failed."
    exit
  fi

fi

# start nginx
echo "start nginx"
nginx -p /nginx -c $nginx_conf_path -g "daemon off;"
