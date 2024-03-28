import os
import yaml
from dotenv import load_dotenv

class KubernetesResource:
    def __init__(self, name):
        self.name = name

    def generate_yaml(self):
        raise NotImplementedError("Subclasses must implement generate_yaml method")

class Deployment(KubernetesResource):
    def __init__(self, name, image, replicas):
        super().__init__(name)
        self.image = image
        self.replicas = replicas

    def generate_yaml(self):
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': f'microservice-{self.name}'
            },
            'spec': {
                'replicas': self.replicas,
                'selector': {
                    'matchLabels': {
                        'app': f'microservice-{self.name}'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': f'microservice-{self.name}'
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': f'microservice-{self.name}',
                            'image': self.image,
                            'ports': [{
                                'containerPort': 8080
                            }]
                        }]
                    }
                }
            }
        }
        return yaml.dump(deployment)

class Service(KubernetesResource):
    def generate_yaml(self):
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f'microservice-{self.name}'
            },
            'spec': {
                'selector': {
                    'app': f'microservice-{self.name}'
                },
                'ports': [{
                    'protocol': 'TCP',
                    'port': 80,
                    'targetPort': 8080
                }]
            }
        }
        return yaml.dump(service)

class Namespace(KubernetesResource):
    def generate_yaml(self):
        namespace = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': f'{self.name}-namespace'
            }
        }
        return yaml.dump(namespace)

class Secret(KubernetesResource):
    def __init__(self, name, data):
        super().__init__(name)
        self.data = data

    def generate_yaml(self):
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': f'microservice-{self.name}-secret'
            },
            'data': self.data
        }
        return yaml.dump(secret)

class KubernetesDeployer:
    def __init__(self, microservice_name, docker_image, replicas):
        self.microservice_name = microservice_name
        self.docker_image = docker_image
        self.replicas = replicas

        # Cargar variables de entorno desde el archivo .env
        load_dotenv()
        self.load_environment_variables()

    def load_environment_variables(self):
        # Variables de entorno para PostgreSQL
        self.db_name = os.getenv('DB_NAME')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_host = os.getenv('DB_HOST')
        self.db_port = os.getenv('DB_PORT')

    def generate_resources(self):
        postgresql_data = {
            'DB_NAME': self.db_name.encode('utf-8'),
            'DB_USER': self.db_user.encode('utf-8'),
            'DB_PASSWORD': self.db_password.encode('utf-8'),
            'DB_HOST': self.db_host.encode('utf-8'),
            'DB_PORT': self.db_port.encode('utf-8')
        }

        resources = [
            Deployment(f'{self.microservice_name}-deployment', self.docker_image, self.replicas),
            Service(f'{self.microservice_name}-service'),
            Namespace(f'{self.microservice_name}-namespace'),
            Secret(f'{self.microservice_name}-secret', postgresql_data)
        ]

        return resources

    def write_yaml_files(self, resources):
        # Create 'k8s' directory if it doesn't exist
        k8s_dir = 'k8s'
        if not os.path.exists(k8s_dir):
            os.makedirs(k8s_dir)

        # Write YAML files in 'k8s' directory
        for resource in resources:
            with open(os.path.join(k8s_dir, f'{resource.name}.yaml'), 'w') as f:
                f.write(resource.generate_yaml())

if __name__ == "__main__":
    deployer = KubernetesDeployer('references', 'my_docker_image:tag', 3)
    resources = deployer.generate_resources()
    deployer.write_yaml_files(resources)
