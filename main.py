from flask import Flask, session, abort, flash, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import boto3
import random
import string
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
ec2 = None
s3 = None

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
    for v in visitors:
        print(str(v.id) + ' ' + v.name + ' ' + v.password)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        pw = request.form['password']
        visitors = Visitor.query.all()
        for v in visitors:
            if v.name == name and v.password == pw:
                session['username'] = name
                return render_template('dashboard.html', pagetitle='Dashboard')
        db.session.add(Visitor(name, pw))
        db.session.commit()
        session['username'] = name
        return render_template('dashboard.html', pagetitle='Dashboard')
    return render_template('login.html', pagetitle='Login page')

@app.route('/dashboard')
def dashboard():
    if session.get('username') != None:
        return render_template('dashboard.html', pagetitle='Dashboard')
    else:
        return redirect(url_for('login'))

@app.route('/ec2')
def dashboard_ec2():
    if session.get('username') != None:
        return render_template('dashboard.html', pagetitle='Dashboard')
    else:
        return redirect(url_for('login'))

    global ec2
    if ec2 == None:
        ec2 = boto3.resource('ec2')
    return render_template('ec2_dashboard.html', pagetitle='EC2 | Dashboard', response=ec2)

@app.route('/ec2/launch', methods=['GET', 'POST'])
def ec2_launch():
    if session.get('username') != None:
        return render_template('dashboard.html', pagetitle='Dashboard')
    else:
        return redirect(url_for('login'))

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
        key = request.form['keyid']
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

        
        image = str(request.form['image'])
        instance = 't2.micro'
        inst_num = int(request.form['number'])
        sg_id = createSecurityGroup(request.form['securitygroup'], [22,8080])
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
            UserData=userdata
        )
        inst_ids = [ inst.instance_id for inst in instances]
        print("Launch complete.")
        return render_template('ec2_launch_complete.html', pagetitle='Launch Instance | EC2',
            instance=instances, material=material)

    # 取得映像id (unfinished)
    images = ec2.images.all()
    # 取得所有security group
    securitygroups = list(ec2.security_groups.all())
    print(securitygroups)
    # 取得所有key_pair
    keys = list(ec2.key_pairs.all())
    print(keys)
    return render_template('ec2_launch.html', pagetitle='Launch Instance | EC2',
        image=images, securitygroup=securitygroups, key=keys)

@app.route('/s3')
def dashboard_s3():
    global s3
    s3 = boto3.client('s3')
    return render_template('s3_dashboard.html', pagetitle='S3 | Dashboard')

@app.route('/s3/launch')
def service_s3(service):
    global s3
    if request.method == 'POST':
        return render_template('')
    return render_template('s3_launch.html', pagetitle=service+' | S3')

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