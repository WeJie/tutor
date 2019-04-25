import os
import click

from . import config as tutor_config
from . import env as tutor_env
from . import exceptions
from . import fmt
from . import opts
from . import scripts
from . import serialize
from . import utils


@click.group(help="Run Open edX on Kubernetes on Aliyun[BETA FEATURE]")
def aliyun():
    pass

@click.command(
    help="Configure and run Open edX from scratch"
)
@opts.root
def quickstart(root):
    click.echo(fmt.title("Interactive platform configuration"))
    tutor_config.save(root)
    click.echo(fmt.title("Stopping any existing platform"))
    stop.callback()
    click.echo(fmt.title("Starting the platform"))
    start.callback(root)
    click.echo(fmt.title("Running migrations. NOTE: this might fail. If it does, please retry 'tutor aliyun databases' later"))
    databases.callback(root)

@click.command(help="Run all configured Open edX services")
@opts.root
def start(root):
    config = tutor_config.load(root)
    kubectl_no_fail("create", "-f", tutor_env.pathjoin(root, "aliyun", "namespace.yml"))

    kubectl("create", "configmap", "nginx-config", "--from-file", tutor_env.pathjoin(root, "apps", "nginx"))
    if config['ACTIVATE_MYSQL']:
        kubectl("create", "configmap", "mysql-config", "--from-env-file", tutor_env.pathjoin(root, "apps", "mysql", "auth.env"))
    kubectl("create", "configmap", "openedx-settings-lms", "--from-file", tutor_env.pathjoin(root, "apps", "openedx", "settings", "lms"))
    kubectl("create", "configmap", "openedx-settings-cms", "--from-file", tutor_env.pathjoin(root, "apps", "openedx", "settings", "cms"))
    kubectl("create", "configmap", "openedx-config", "--from-file", tutor_env.pathjoin(root, "apps", "openedx", "config"))

    kubectl("create", "-f", tutor_env.pathjoin(root, "aliyun", "volumes.yml"))
    kubectl("create", "-f", tutor_env.pathjoin(root, "aliyun", "ingress.yml"))
    kubectl("create", "-f", tutor_env.pathjoin(root, "aliyun", "services.yml"))
    kubectl("create", "-f", tutor_env.pathjoin(root, "aliyun", "deployments.yml"))

@click.command(help="Stop a running platform")
def stop():
    kubectl("delete", "deployments,services,ingress,configmaps", "--all")

@click.command(help="Completely delete an existing platform")
@click.option("-y", "--yes", is_flag=True, help="Do not ask for confirmation")
def delete(yes):
    if not yes:
        click.confirm('Are you sure you want to delete the platform? All data will be removed.', abort=True)
    kubectl("delete", "namespace", Aliyun.NAMESPACE)

@click.command(
    help="Create databases and run database migrations",
)
@opts.root
def databases(root):
    scripts.migrate(root, run_bash)

@click.command(help="Create an Open edX user and interactively set their password")
@opts.root
@click.option("--superuser", is_flag=True, help="Make superuser")
@click.option("--staff", is_flag=True, help="Make staff user")
@click.argument("name")
@click.argument("email")
def createuser(root, superuser, staff, name, email):
    scripts.create_user(root, run_bash, superuser, staff, name, email)

@click.command(help="Import the demo course")
@opts.root
def importdemocourse(root):
    click.echo(fmt.info("Importing demo course"))
    scripts.import_demo_course(root, run_bash)
    click.echo(fmt.info("Re-indexing courses"))
    indexcourses.callback(root)

@click.command(help="Re-index courses for better searching")
@opts.root
def indexcourses(root):
    # Note: this is currently broken with "pymongo.errors.ConnectionFailure: [Errno 111] Connection refused"
    # I'm not quite sure the settings are correctly picked up. Which is weird because migrations work very well.
    scripts.index_courses(root, run_bash)

@click.command(
    help="Launch a shell in LMS or CMS",
)
@opts.root
@click.argument("service", type=click.Choice(["lms", "cms"]))
def shell(root, service):
    Aliyun(root).execute(service, "bash")

@click.command(help="Create a Kubernetesadmin user")
@opts.root
def adminuser(root):
    utils.kubectl("create", "-f", tutor_env.pathjoin(root, "aliyun", "adminuser.yml"))

@click.command(help="Print the Kubernetes admin user token")
@opts.root
def admintoken(root):
    click.echo(Aliyun().admin_token())

@click.command(help="hello world")
def hello():
    click.echo('world')

def kubectl(*command):
    """
    Run kubectl commands in the right namespace. Also, errors are completely
    ignored, to avoid stopping on "AlreadyExists" errors.
    """
    args = list(command)
    args += [
        "--namespace", Aliyun.NAMESPACE
    ]
    kubectl_no_fail(*args)

def kubectl_no_fail(*command):
    """
    Run kubectl commands and ignore exceptions, to avoid stopping on
    "AlreadyExists" errors.
    """
    try:
        utils.kubectl(*command)
    except exceptions.TutorError:
        pass


class Aliyun:
    CLIENT = None
    NAMESPACE = "openedx"

    def __init__(self, root=''):
        if root:
            config = tutor_config.load(root)
            self.NAMESPACE = config.get('ALIYUN_NAMESPACE', self.NAMESPACE)

    @property
    def client(self):
        if self.CLIENT is None:
            # Import moved here for performance reasons
            import kubernetes
            kubernetes.config.load_kube_config()
            self.CLIENT = kubernetes.client.CoreV1Api()
        return self.CLIENT

    def pod_name(self, app):
        selector = "app=" + app
        try:
            return self.client.list_namespaced_pod(self.NAMESPACE, label_selector=selector).items[0].metadata.name
        except IndexError:
            raise exceptions.TutorError("Pod with app {} does not exist. Make sure that the pod is running.")

    def admin_token(self):
        # Note: this is a HORRIBLE way of looking for a secret

        try:
            secrets = []
            for s in self.client.list_namespaced_secret("kube-system").items:
                if s.metadata.name.startswith("admin-user-token"):
                    secrets.append(s)
            secret = secrets[0]

        except IndexError:
            raise exceptions.TutorError("Secret 'admin-user-token'. Make sure that admin user was created.")
        return self.client.read_namespaced_secret(secret.metadata.name, "kube-system").data["token"]

    def execute(self, app, *command):
        podname = self.pod_name(app)
        click.echo(podname)
        kubectl_no_fail("exec", "--namespace", self.NAMESPACE, "-it", podname, "--", *command)


def run_bash(root, service, command):
    Aliyun().execute(service, "bash", "-e", "-c", command)

aliyun.add_command(quickstart)
aliyun.add_command(start)
aliyun.add_command(stop)
aliyun.add_command(delete)
aliyun.add_command(databases)
aliyun.add_command(createuser)
aliyun.add_command(importdemocourse)
aliyun.add_command(indexcourses)
aliyun.add_command(shell)
aliyun.add_command(adminuser)
aliyun.add_command(admintoken)
aliyun.add_command(hello)
