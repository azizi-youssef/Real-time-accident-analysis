#!/bin/bash

if [ "$SPARK_MODE" == "master" ]; then
    echo "Starting Spark master node..."
    ${SPARK_HOME}/sbin/start-master.sh
    tail -f ${SPARK_HOME}/logs/*
elif [ "$SPARK_MODE" == "worker" ]; then
    echo "Starting Spark worker node..."
    ${SPARK_HOME}/sbin/start-worker.sh ${SPARK_MASTER_URL}
    
    echo "Starting Spark Streaming application..."
    /opt/bitnami/spark/bin/spark-submit \
        --master ${SPARK_MASTER_URL} \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1 \
        /app/src/streaming.py &
    
    tail -f ${SPARK_HOME}/logs/*
else
    echo "Please specify SPARK_MODE as 'master' or 'worker'"
    exit 1
fi 


