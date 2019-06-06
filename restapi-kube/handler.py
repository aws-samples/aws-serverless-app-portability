# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from __future__ import print_function
import time
import sys
import logging
import pymysql
import json
import os
import traceback
import stomp
import ssl
from stomp import *

#rds settings
rds_host  = os.environ['DB_HOST']
name = os.environ["DB_USER"]
password = os.environ["DB_PASS"]
db_name = os.environ["DB_NAME"]
mq_endpoint_1 = os.environ["MQ_EP_1"]
mq_endpoint_2 = os.environ["MQ_EP_2"]
mq_user = os.environ["MQ_USER"]
mq_password = os.environ["MQ_PASS"]
mq_queue = os.environ["MQ_QUEUE"]

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
    print("Received event: " + str(event))
    operation = event['data']['httpMethod']

    payload = event['data']['queryStringParameters'] if operation == 'GET' else json.loads(event['data']['body'])
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

        # send message to MQ
        mqclient = stomp.Connection([(mq_endpoint_1, 61614), (mq_endpoint_2, 61614)])
        mqclient.set_ssl([(mq_endpoint_1, 61614), (mq_endpoint_2, 61614)])
        mqclient.set_listener('', PrintingListener())
        mqclient.start()
        mqclient.connect(mq_user, mq_password, wait=True)
        mqclient.send(mq_queue, "Created user {0}".format(user_id))
        mqclient.disconnect()

        return respond(None, payload)
    except Exception as e:
        trc = traceback.format_exc()
        logger.error("ERROR: Unexpected error: Could not create user: {0} - {1}".format(str(e), trc))
        return respond(ValueError("ERROR: Unexpected error: Could not create user: {0} - {1}".format(str(e), trc)))

def get(event, context):
    '''
    Retrieve all users
    '''
    print("Received event: " + str(event))

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
    print("Received event: " + str(event))

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

