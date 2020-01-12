# create 6 VMs and register them to a application load balancer
import boto3
import sys
import time

INST_NUM = 2
ec2 = None
key = None

def createSecurityGroup(gname, ports):
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

def main():
    global ec2
    global key
    # read user data from the file
    userfd = open('userdata', 'r')
    userdata = userfd.read()

    if ec2 == None:
        ec2 = boto3.resource('ec2')
    # find the key which starts withd 'qwik'

    for k in list(ec2.key_pairs.all()):
        if k.name.startswith('qwik'):
            key = k.name
            break
    sg_id = createSecurityGroup("pyenv", [22,8080])
    key = 'vockey'
    # create VMs with userdata
    print("Create instances")
    instances = ec2.create_instances(
        ImageId='ami-062f7200baf2fa504',
        InstanceType='t2.micro',
        KeyName=key,
        MinCount=INST_NUM,
        MaxCount=INST_NUM,
        SecurityGroupIds=[sg_id],
        UserData=userdata
    )
    inst_ids = [ inst.instance_id for inst in instances]

    # client = boto3.client('elbv2')
    # elbsg_id = createSecurityGroup("pyenv elb", [80])


    # # get default subnets
    
    # vpc = list(ec2.vpcs.all())[0]
    # subnetlist = [sn.id for sn in vpc.subnets.all()]
    # print("Create load balancer")
    # # create an application load balancer
    # reslb = client.create_load_balancer(
    #     Name='pyelb',
    #     SecurityGroups=[elbsg_id],
    #     Subnets=subnetlist,
    #     Scheme='internet-facing',
    #     Type='application',
    #     IpAddressType='ipv4'
    # )
    # lbarn = reslb['LoadBalancers'][0]['LoadBalancerArn']
    # # create the target group with port 8080
    # print("Create target group")
    # restg = client.create_target_group(
    #     Name='pytg',
    #     Protocol='HTTP',
    #     Port=8080,
    #     VpcId=vpc.id,
    #     HealthCheckProtocol='HTTP',
    #     HealthCheckPort='8080',
    #     HealthCheckEnabled=True,
    #     HealthCheckPath='/',
    #     Matcher={'HttpCode': '200'}
    # )
    # tgarn = restg['TargetGroups'][0]['TargetGroupArn']

    # # wait for the initialization of VMs and register target groups
    # counter = 1
    # check_insts = inst_ids.copy()
    # while len(check_insts) != 0:
    #     sys.stdout.write('\r')
    #     sys.stdout.write('VM initializing %s' % ('.'*(INST_NUM - len(check_insts))))
    #     sys.stdout.flush()
    #     time.sleep(5)
    #     instances = ec2.instances.filter(Filters=[{'Name' : 'instance-state-name', 'Values' : ['running']}])
    #     # register target groups after finishing all the VM initialization.
    #     for inst in instances:
    #         if inst.id in check_insts:
    #             check_insts.remove(inst.id)
    #     if len(check_insts) != 0:
    #         continue
    #     sys.stdout.write('\n')
    #     print("Register targets")
    #     res = client.register_targets(
    #         TargetGroupArn=tgarn,
    #         Targets=[{'Id': vmid} for vmid in inst_ids]
    #     )
    # print("Create listener")
    # reslistener = client.create_listener(
    #     DefaultActions=[
    #         {
    #             'TargetGroupArn': tgarn,
    #             'Type': 'forward',
    #         },
    #     ],
    #     LoadBalancerArn=lbarn,
    #     Port=80,
    #     Protocol='HTTP',
    # )

if __name__ == '__main__':
    print('Set environment.')
    main()
    print('Set complete.')