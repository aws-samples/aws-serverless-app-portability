# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from __future__ import print_function
import time
import sys
import logging
import pymysql
import boto3
import json
import os
import traceback
import ssl

#rds settings
rds_host  = os.environ['DB_HOST']
name = os.environ["DB_USER"]
password = os.environ["DB_PASS"]
db_name = os.environ["DB_NAME"]
sqs_queue = os.environ["SQS_QUEUE"]
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName=sqs_queue)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": 'true'
        },
    }

def create(event, context):
    '''
    Create new user
    '''
    print("Received event: " + json.dumps(event, indent=2))
    operation = event['httpMethod']

    payload = event['queryStringParameters'] if operation == 'GET' else json.loads(event['body'])
    user_id = payload['user_id']
    email = payload['email']
    print("Creating user {0} with email {1}".format(user_id, email))

    try:
        conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")
        with conn.cursor() as cur:
            cur.execute("insert into users(user_id, email) values(\"{0}\", \"{1}\")".format(user_id, email))
            conn.commit()
        conn.close()

        # send message to SQS
        queue.send_message(MessageBody="Created user {0}".format(user_id))

        return respond(None, payload)
    except Exception as e:
        trc = traceback.format_exc()
        logger.error("ERROR: Unexpected error: Could not create user: {0} - {1}".format(str(e), trc))
        return respond(ValueError("ERROR: Unexpected error: Could not create user: {0} - {1}".format(str(e), trc)))

def get(event, context):
    '''
    Retrieve all users
    '''
    print("Received event: " + json.dumps(event, indent=2))

    print("Getting all users")

    try:
        conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")
        users = []
        with conn.cursor() as cur:
            cur.execute("select user_id, email from users")
            for row in cur:
                users.append({'user_id': row[0],
                                  'email': row[1]})
            conn.commit()
        conn.close()
        logger.info("Returning {0} users".format(str(len(users))))
        return respond(None, users)
    except Exception as e:
        trc = traceback.format_exc()
        logger.error("ERROR: Unexpected error: Could not get users: {0} - {1}".format(str(e), trc))
        return respond(ValueError("ERROR: Unexpected error: Could not get users: {0} - {1}".format(str(e), trc)))

def schema(event, context):
    '''
    Recreate schema on demand.
    '''
    print("Received event: " + json.dumps(event, indent=2))

    try:
        conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
        logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

        with conn.cursor() as cur:
            # Drop tables if they exist
            cur.execute("DROP TABLE IF EXISTS users")
            logger.info("Dropped tables")

            # create tables
            cur.execute("create table users( user_id varchar(255) NOT NULL, email varchar(255) NOT NULL, PRIMARY KEY (user_id))")
            logger.info("Created tables")
            conn.commit()
        conn.close()
        return respond(None, {'Msg': 'Created schema'})
    except Exception as e:
        trc = traceback.format_exc()
        logger.error("ERROR: Unexpected error: Could not connect to MySql instance: {0} - {1}".format(str(e), trc))
        return respond(ValueError("ERROR: Unexpected error: Could not connect to MySql instance: {0} - {1}".format(str(e), trc)))
