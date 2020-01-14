from flask import Flask, session, abort, flash, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import boto3
import time
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
ec2 = None
s3 = None

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

class Visitor(db.Model):
    __tablename__ = "visitor"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=True, nullable=False)
    def __init__(self, k, v):
        self.name = k
        self.password = v
    def __repr__(self):
        return '<Visitor %r>' % self.key

@app.route('/show')
def show():
    visitors = Visitor.query.all()
    out = ""
    for v in visitors:
        out += str(v.id) + ' ' + v.name + ' ' + v.password + '<br>'
    return out

@app.route('/renew', methods=['GET', 'POST'])
def renew():
    if request.method == 'POST':
        keyid = request.form['id']
        key = request.form['key']
        stoken = request.form['session']
        os.environ['AWS_ACCESS_KEY_ID'] = keyid
        os.environ['AWS_SECRET_ACCESS_KEY'] = key
        os.environ['AWS_SESSION_TOKEN'] = stoken
        return redirect('/')
    return render_template('renew.html', pagetitle='Renew')

@app.route('/', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        name = request.form['name']
        pw = request.form['password']
        visitors = Visitor.query.all()
        for v in visitors:
            if v.name == name and v.password == pw:
                session['username'] = name
            return redirect('/dashboard')
        db.session.add(Visitor(name, pw))
        db.session.commit()
        session['username'] = name
        return redirect('/dashboard')
    return render_template('login.html', pagetitle='Login page')

@app.route('/dashboard')
def dashboard():
    if session.get('username') == None:
        return redirect('/')
    
    return render_template('dashboard.html', pagetitle='Login page' + session.get('username'))

@app.route('/ec2', methods=['GET', 'POST'])
def ec2_dashboard():
    if session.get('username') == None:
        return redirect('/')

    client = boto3.client('ec2')
    if request.method == 'POST':
            response = client.describe_instances()
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['Tags'][0]['Value'] == session.get('username'):
                        if request.form['action'] == 'terminate':
                            client.terminate_instances(
                                InstanceIds=[instance['InstanceId']]
                            )
                        elif request.form['action'] == 'start':
                            client.start_instances(
                                InstanceIds=[instance['InstanceId']]
                            )
                        elif request.form['action'] == 'stop':
                            client.stop_instances(
                                InstanceIds=[instance['InstanceId']]
                            )
                        elif request.form['action'] == 'reboot':
                            client.reboot_instances(
                                InstanceIds=[instance['InstanceId']]
                            )
    
    time.sleep(3)
    instances = []
    response = client.describe_instances()
    for reservation in response['Reservations']:
        # print(reservation['Instances'])
        for instance in reservation['Instances']:
            if instance['Tags'][0]['Value'] == session.get('username'):
                instances.append(instance)

    # print(instances)      
    return render_template('ec2_dashboard.html', pagetitle='EC2 | Dashboard' +
        ' ' + session.get('username'), instance=instances)

@app.route('/ec2/launch', methods=['GET', 'POST'])
def ec2_launch():
    if session.get('username') == None:
        return redirect('/')

    global ec2
    if ec2 == None:
        ec2 = boto3.resource('ec2')

    if request.method == 'POST':
        # print(request.form['number'])
        # print(request.form['securitygroup'])
        # print(request.form['keyid'])
        # print(request.form['userdata'])
        if ec2 == None:
            ec2 = boto3.resource('ec2')

        # find the key
        flag = True
        key = session.get('username')
        for k in list(ec2.key_pairs.all()):
            if k.name == key:
                flag = False
                break
        
        material = ""
        if flag:
            key_pair = ec2.create_key_pair(
                KeyName=key,
                DryRun=False
            )
            material = key_pair.key_material
            print(material)

        tag = session.get('username')
        tags = [
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': tag
                    },
                ]
            },
        ]

        image = str(request.form['image'])
        instance = 't2.micro'
        inst_num = int(request.form['number'])
        sg_id = createSecurityGroup(session.get('username'), [22,8080])
        userdata = str(request.form['userdata'])

        # create VMs with userdata
        print("Create instances")
        instances = ec2.create_instances(
            ImageId=image,
            InstanceType=instance,
            KeyName=key,
            MinCount=inst_num,
            MaxCount=inst_num,
            SecurityGroupIds=[sg_id],
            UserData=userdata,
            TagSpecifications=tags,
        )
        # inst_ids = [ inst.instance_id for inst in instances]
        print("Launch complete.")
        return render_template('ec2_launch_complete.html', pagetitle='Launch Complete | EC2' +
            ' ' + session.get('username'), instance=instances, material=material)

    # 取得映像id (unfinished)
    images = ec2.images.all()
    # 取得所有security group
    securitygroups = list(ec2.security_groups.all())
    print(securitygroups)
    # 取得所有key_pair
    keys = list(ec2.key_pairs.all())
    print(keys)
    return render_template('ec2_launch.html', pagetitle='Launch Instance | EC2' +
        ' ' + session.get('username'), image=images, securitygroup=securitygroups, key=keys)

@app.route('/s3')
def s3_dashboard():
    if session.get('username') == None:
        return redirect('/')

    buckets = dict()
    client = boto3.client('s3')
    response = client.list_buckets()
    for bucket in response['Buckets']:
        buckets[bucket['Name']] = list_files(bucket['Name'])
    print(buckets)
    return render_template('s3_dashboard.html', buckets=buckets)

# Function to list files in a given S3 bucket
def list_files(bucket):
    contents = []
    try:
        for item in client.list_objects(Bucket=bucket)['Contents']:
            print(item)
            contents.append(item)
    except Exception as e:
        pass
    return contents

@app.route('/s3/create', methods=['GET', 'POST'])
def s3_create():
    if session.get('username') == None:
        return redirect('/')

    if request.method == "POST":
        new_bucket_name = str(request.form['name'])
        client = boto3.client('s3')
        response = client.create_bucket(
            ACL='public-read-write',
            Bucket=new_bucket_name
        )
        # global BUCKET
        # BUCKET=new_bucket_name
        # print(BUCKET)
        return redirect('/s3')

def createSecurityGroup(gname, ports):
    global ec2
    print("Create security group")
    try:
        sg = ec2.create_security_group(
            Description='boto3 allow ' + ' '.join(str(n) for n in ports),
            GroupName=gname,
        )
        print("Authorize ingress")
        for p in ports:
            sg.authorize_ingress(
                IpProtocol="tcp",
                CidrIp="0.0.0.0/0",
                FromPort=p,
                ToPort=p
            )
    except Exception:
        print("Security group exists.")
        sgall = ec2.security_groups.all()
        for sg in sgall:
            if sg.group_name == gname:
                return sg.group_id
    return sg.id


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)