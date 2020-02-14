#!/usr/bin/env bash

##############################
# Restore SQL Server test data
##############################

set -e

echo "Setting up DSN for test SQL Server"

export SQLUSER=sa
export SQLHOST=mssql
export SQLPORT=1433
export SQLPASSWORD='<YourStrong!Passw0rd>'

export PATH=$PATH:/opt/mssql-tools/bin

echo "sleep"
sleep 20

echo "Create Database"
sqlcmd -S $SQLHOST,$SQLPORT -U $SQLUSER -P $SQLPASSWORD -i /usr/src/QgisModelBaker/tests/testdata/mssql/setup-mssql.sql

echo "Setting up DSN for test SQL Server"
cat <<EOT > /etc/odbc.ini
[ODBC Data Sources]
testsqlserver = ODBC Driver 17 for SQL Server
[testsqlserver]
Driver       = ODBC Driver 17 for SQL Server
Description  = Test SQL Server
Server       = mssql
EOT




# Driver=/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.2.so.0.1
# DRIVER={/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.2.so.0.1}
