"""A Kubernetes Python Pulumi program"""

import pulumi
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    PodSpecArgs,
    PodTemplateSpecArgs,
    ServiceAccount,
)
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from pulumi_kubernetes.core.v1 import Namespace, Service
from pulumi_kubernetes.storage.v1 import StorageClass, StorageClassArgs

# TODO: check this eksctl utils associate-iam-oidc-provider --cluster StarKube --approve

def configure_efs_storage(resources):

    efs_service_account = ServiceAccount(
        "efs-csi-controller-sa",
        metadata=ObjectMetaArgs(
            labels={"app.kubernetes.io/name": "aws-efs-csi-driver"},
            name="efs-csi-controller-sa",
            namespace="kube-system",
            annotations={
                "eks.amazonaws.com/role-arn": resources["aws_stack_ref"].get_output("efs_csi_driver_role_arn"),
            },
        ),
    )

    aws_efs_csi_driver = Release(
        "aws-efs-csi-driver",
        ReleaseArgs(
            chart="aws-efs-csi-driver",
            name="aws-efs-csi-driver",
            repository_opts=RepositoryOptsArgs(
                repo="https://kubernetes-sigs.github.io/aws-efs-csi-driver/",
            ),
            namespace="kube-system",
            values={
                "image": {
                    "repository": "602401143452.dkr.ecr.eu-central-1.amazonaws.com/eks/aws-efs-csi-driver",
                },
                "controller": {
                    "serviceAccount": {
                        "create": False,
                        "name": "efs-csi-controller-sa",
                    }
                },
            },
        ),
    )

    pulumi.export("aws-efs-csi-driver", aws_efs_csi_driver.status.name)

    efs_storage_class = StorageClass(
        "efs-sc",
        metadata=ObjectMetaArgs(
            name="efs-sc",
        ),
        provisioner="efs.csi.aws.com",
        parameters={
            "provisioningMode": "efs-ap",
            "fileSystemId": resources["aws_stack_ref"].get_output("k8s_efs_id"),
            "directoryPerms": "700",
            "basePath": "/eks_dynamic",
        },
    )

    return resources
