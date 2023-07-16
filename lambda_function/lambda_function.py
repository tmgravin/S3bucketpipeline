import boto3
import pymysql

def lambda_handler(event, context):
    rds_instance_id = create_rds()
    ec2_instance_id = create_ec2()
    rds_ec2_connection = connect_rds_ec2(rds_instance_id, ec2_instance_id)
    create_database(rds_instance_id, rds_ec2_connection)

    return {
        'statusCode': 200,
        'body': f"RDS Instance ID: {rds_instance_id}\nEC2 Instance ID: {ec2_instance_id}\nRDS-EC2 Connection: {rds_ec2_connection}"
    }

def create_rds():
    rds_client = boto3.client('rds')
    response = rds_client.create_db_instance(
        DBInstanceIdentifier='rabin12345',
        MasterUsername='admin',
        MasterUserPassword='rabintamang',
        Engine='mysql',
        AllocatedStorage=20,
        DBInstanceClass='db.t3.micro',
        VpcSecurityGroupIds=['sg-0439827899b1c11a9'],
        Tags=[
            {
                'Key': 'cloud',
                'Value': 'c85030a1812376l4180077t1w839778766534'
            },
        ]
    )

    db_instance_id = response['DBInstance']['DBInstanceIdentifier']

    # Wait until the RDS instance is available
    waiter = rds_client.get_waiter('db_instance_available')
    waiter.wait(DBInstanceIdentifier=db_instance_id)

    return db_instance_id

def create_ec2():
    ec2_client = boto3.client('ec2')
    response = ec2_client.run_instances(
        ImageId='ami-09988af04120b3591',
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        SubnetId='subnet-018f349388df4ad57',
        SecurityGroupIds=['sg-0cbac15ececae9efa'],
        KeyName='datab',
    )

    instance_id = response['Instances'][0]['InstanceId']

    return instance_id

def connect_rds_ec2(rds_instance_id, ec2_instance_id):
    ec2_client = boto3.client('ec2')
    response = ec2_client.describe_instances(
        Filters=[
            {
                'Name': 'Name',
                'Values': ['rabindb']  # Replace with the RDS database name tag
            }
        ]
    )

    if not response['Reservations']:
        return 'Could not find EC2 instance associated with the RDS database.'

    instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
    instance_ip = response['Reservations'][0]['Instances'][0]['PrivateIpAddress']

    if instance_id != ec2_instance_id:
        return 'EC2 instance ID does not match the associated RDS instance.'

    return f"EC2 instance ID: {instance_id}, Private IP: {instance_ip}"

def create_database(rds_instance_id, rds_ec2_connection):
    rds_endpoint = rds_ec2_connection['Endpoint']['Address']
    rds_connection = pymysql.connect(
        host=rds_endpoint,
        user='admin',
        password='rabintamang',
        database='rabindb',
        port=3306
    )
    cursor = rds_connection.cursor()
    create_database_query = "CREATE DATABASE your-database-name"
    cursor.execute(create_database_query)
    rds_connection.commit()
    cursor.close()
    rds_connection.close()