#!/bin/bash
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

SCRIPTDIR=`dirname $0`
LABBUCKET=$1
if [ "$LABBUCKET" == "" ]
then
    echo "Usage: $0 <lab bucket>"
    exit 1
fi

aws s3 sync \
    --exclude ".git/*" \
    --exclude "*/.gitignore" \
    --exclude "*/package-lock.json" \
    --exclude "*/package.json" \
    --exclude "*/*.zip" \
    --exclude "*/node_modules/*" \
    --exclude "*/.serverless/*" \
    $SCRIPTDIR/.. s3://$LABBUCKET/lab
