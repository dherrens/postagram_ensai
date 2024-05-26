#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.default_vpc import DefaultVpc
from cdktf_cdktf_provider_aws.default_subnet import DefaultSubnet
from cdktf_cdktf_provider_aws.launch_template import LaunchTemplate
from cdktf_cdktf_provider_aws.lb import Lb
from cdktf_cdktf_provider_aws.lb_target_group import LbTargetGroup
from cdktf_cdktf_provider_aws.lb_listener import LbListener, LbListenerDefaultAction
from cdktf_cdktf_provider_aws.autoscaling_group import AutoscalingGroup
from cdktf_cdktf_provider_aws.security_group import SecurityGroup, SecurityGroupIngress, SecurityGroupEgress
from cdktf_cdktf_provider_aws.data_aws_caller_identity import DataAwsCallerIdentity

import base64

bucket="postagram-bucket20240517111124201400000001"
dynamo_table="posts"
region="us-east-1"
your_repo="https://github.com/dherrens/postagram_ensai.git"


user_data = base64.b64encode(f"""#!/bin/bash
echo "userdata-start"
echo 'export BUCKET={bucket}' >> /etc/environment
echo 'export DYNAMO_TABLE={dynamo_table}' >> /etc/environment
echo 'export REGION={region}' >> /etc/environment
source /etc/environment
apt update
apt install -y python3-pip
git clone {your_repo}
cd postagram_ensai/webservice
rm .env
pip3 install -r requirements.txt
python3 app.py
echo "userdata-end""".encode("ascii")).decode("ascii")



class ServerStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        AwsProvider(self, "AWS", region="us-east-1")
        account_id = DataAwsCallerIdentity(self, "acount_id").account_id

        default_vpc = DefaultVpc(
            self, "default_vpc"
        )
         
        # Les AZ de us-east-1 sont de la forme us-east-1x 
        # avec x une lettre dans abcdef. Ne permet pas de déployer
        # automatiquement ce code sur une autre région. Le code
        # pour y arriver est vraiment compliqué.
        az_ids = [f"us-east-1{i}" for i in "abcdef"]
        subnets = []
        for i,az_id in enumerate(az_ids):
            subnets.append(DefaultSubnet(
                self, f"default_sub{i}",
                availability_zone=az_id
            ).id)
            
        security_group = SecurityGroup(
            self, "sg-tp",
            ingress=[
                SecurityGroupIngress(
                    from_port=22,
                    to_port=22,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP",
                ),
                SecurityGroupIngress(
                    from_port=80,
                    to_port=80,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP"
                ),
                SecurityGroupIngress(
                    from_port=8080,
                    to_port=8080,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="TCP"
                )
            ],
            egress=[
                SecurityGroupEgress(
                    from_port=0,
                    to_port=0,
                    cidr_blocks=["0.0.0.0/0"],
                    protocol="-1"
                )
            ]
            )
        
        launch_template = LaunchTemplate(
            self, "compute",
            image_id="ami-0557a15b87f6559cf",
            instance_type="t2.micro",
            user_data=user_data,
            vpc_security_group_ids=[security_group.id],
            key_name="vockey",
            iam_instance_profile={"name": "LabInstanceProfile"}
        )

        lb = Lb(
            self, "lb",
            load_balancer_type="application",
            security_groups=[security_group.id],
            subnets=subnets
        )

        target_group = LbTargetGroup(
            self, "tg_group",
            port=8080,
            protocol="HTTP",
            vpc_id=default_vpc.id,
            target_type="instance"
        )

        lb_listener = LbListener(
            self, "lb_listener",
            load_balancer_arn=lb.arn,
            port=80,
            protocol="HTTP",
            default_action=[LbListenerDefaultAction(type="forward", target_group_arn=target_group.arn)]
        )

        asg = AutoscalingGroup(
            self, "asg",
            min_size=1,
            max_size=4,
            desired_capacity=1,
            launch_template={"id":launch_template.id},
            vpc_zone_identifier= subnets,
            target_group_arns=[target_group.arn]
        )
        
        TerraformOutput(
            self, "url",
            value="http://{}".format(lb.dns_name),
        )

app = App()
ServerStack(app, "cdktf_server")
app.synth()
