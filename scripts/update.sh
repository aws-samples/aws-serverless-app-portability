#!/usr/bin/env bash

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

templatebucket=$1
templateprefix=$2
stackname=$3
region=$4
SCRIPTDIR=`dirname $0`
if [ "$templatebucket" == "" ]
then
    echo "Usage: $0 <template bucket> <template prefix> <stack name> <region>"
    exit 1
fi
if [ "$templateprefix" == "" ]
then
    echo "Usage: $0 <template bucket> <template prefix> <stack name> <region>"
    exit 1
fi
if [ "$stackname" == "" ]
then
    echo "Usage: $0 <template bucket> <template prefix> <stack name> <region>"
    exit 1
fi
if [ "$region" == "" ]
then
    echo "Usage: $0 <template bucket> <template prefix> <stack name> <region>"
    exit 1
fi

# Check if we need to append region to S3 URL
TEMPLATE_URL=https://s3.amazonaws.com/$templatebucket/$templateprefix/master.yaml
if [ "$region" != "us-east-1" ]
then
    TEMPLATE_URL=https://s3-$region.amazonaws.com/$templatebucket/$templateprefix/master.yaml
fi

aws s3 cp $SCRIPTDIR/../cfn/master.yaml s3://$templatebucket/$templateprefix/master.yaml
aws s3 cp $SCRIPTDIR/../cfn/network.yaml s3://$templatebucket/$templateprefix/network.yaml
aws s3 cp $SCRIPTDIR/../cfn/secgroups.yaml s3://$templatebucket/$templateprefix/secgroups.yaml
aws s3 cp $SCRIPTDIR/../cfn/aurora.yaml s3://$templatebucket/$templateprefix/aurora.yaml
aws s3 cp $SCRIPTDIR/../cfn/mq.yaml s3://$templatebucket/$templateprefix/mq.yaml
aws s3 cp $SCRIPTDIR/../cfn/jumphost.yaml s3://$templatebucket/$templateprefix/jumphost.yaml

aws cloudformation update-stack --stack-name $stackname \
    --template-url $TEMPLATE_URL \
    --parameters \
    ParameterKey=TemplateBucketName,ParameterValue=$templatebucket \
    ParameterKey=TemplateBucketPrefix,ParameterValue=$templateprefix \
    ParameterKey=ProjectTag,ParameterValue=PortableApps \
    ParameterKey=vpccidr,ParameterValue="10.20.0.0/16" \
    ParameterKey=AllowedCidrIngress,ParameterValue="0.0.0.0/0" \
    ParameterKey=AppPrivateCIDRA,ParameterValue="10.20.3.0/24" \
    ParameterKey=AppPrivateCIDRB,ParameterValue="10.20.4.0/24" \
    ParameterKey=AppPublicCIDRA,ParameterValue="10.20.1.0/24" \
    ParameterKey=AppPublicCIDRB,ParameterValue="10.20.2.0/24" \
    ParameterKey=DatabaseName,ParameterValue="portabledb" \
    ParameterKey=DatabaseUser,ParameterValue="dbuser" \
    ParameterKey=DatabasePassword,ParameterValue="Mydbcred01" \
    ParameterKey=DbInstanceSize,ParameterValue="db.r4.large" \
    ParameterKey=BrokerName,ParameterValue="portablemq" \
    ParameterKey=BrokerUser,ParameterValue="mquser" \
    ParameterKey=BrokerPassword,ParameterValue="Mymqbrokercred01" \
    ParameterKey=BrokerInstanceSize,ParameterValue="mq.m5.large" \
    ParameterKey=keyname,ParameterValue="KEY" \
    --tags Key=Project,Value=PortableApps \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
