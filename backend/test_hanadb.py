import hdbcli.dbapi

conn = hdbcli.dbapi.connect(
    address="b99f38e1-2a79-4b7c-96dd-a3dd672b6075.hana.trial-us10.hanacloud.ondemand.com",
    port=443,
    user="DBADMIN",
    password="Bitu@1212"
)

print("Connected Successfully!")

conn.close()
