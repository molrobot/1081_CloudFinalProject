from flask import Flask, session, abort, flash, request, redirect, url_for, render_template
import boto3
import random
import string
app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html', pagetitle='Login page')

@app.route('/dashboard')
def dashboard():
    if True:
        return render_template('dashboard.html', pagetitle='Dashboard')
    else:
        return redirect(url_for('login'))

@app.route('/ec2')
def dashboard_ec2():
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances()
    print(response)
    return render_template('ec2_dashboard.html', pagetitle='EC2 | Dashboard', content1=response)

@app.route('/ec2/launch', methods=['GET', 'POST'])
def ec2_launch():
    if request.method == 'POST':
        # print(request.form['number'])
        # print(request.form['securitygroup'])
        # print(request.form['keyid'])
        # print(request.form['userdata'])

        ec2 = boto3.resource('ec2')
        key = request.form['keyid']
        INST_NUM = int(request.form['number'])
        sg_id = createSecurityGroup(request.form['securitygroup'], [22,8080], ec2)
        userdata = str(request.form['userdata'])

        print("Create instances")
        instances = ec2.create_instances(
            ImageId='ami-062f7200baf2fa504',
            InstanceType='t2.medium',
            KeyName=key,
            MinCount=INST_NUM,
            MaxCount=INST_NUM,
            SecurityGroupIds=[sg_id],
            UserData=userdata
        )
        inst_ids = [ inst.instance_id for inst in instances]
        print("Launch complete.")
        return render_template('launch_complete.html', instance=instances, id=inst_ids)
    return render_template('ec2_launch.html', pagetitle='Launch Instance | EC2')

@app.route('/s3')
def dashboard_s3():
    s3 = boto3.client('s3')
    return render_template('s3_dashboard.html', pagetitle='S3 | Dashboard', content1=s3)

@app.route('/s3/launch')
def service_s3(service):
    if request.method == 'POST':
        return render_template('')
    return render_template('s3_launch.html', pagetitle=service+' | S3')

def createSecurityGroup(gname, ports, ec2):
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
    app.run()