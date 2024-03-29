import os
import yaml
import json
import base64

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
        self.metadata = {}

    def generate_yaml(self):
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': self.metadata,
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
    def __init__(self, name, port):
        super().__init__(name)
        self.metadata = {}
        self.port = port


    def generate_yaml(self):
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': self.metadata,
            'spec': {
                'selector': {
                    'app': f'microservice-{self.name}'
                },
                'ports': [{
                    'protocol': 'TCP',
                    'port': self.port,
                    'targetPort': self.port
                }]
            }
        }
        return yaml.dump(service)

class Namespace(KubernetesResource):
    def __init__(self, name):
        super().__init__(name)
        self.metadata = {}

    def generate_yaml(self):
        namespace = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': f'{self.name}'
            }
        }
        return yaml.dump(namespace)

class Secret(KubernetesResource):
    def __init__(self, name, data):
        super().__init__(name)
        self.data = data
        self.metadata = {}

    def generate_yaml(self):
        encoded_data = {key: base64.b64encode(value.encode('utf-8')).decode('utf-8') for key, value in self.data.items()}
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': f'microservice-{self.name}'
            },
            'data': encoded_data
        }
        return yaml.dump(secret)

class KubernetesDeployer:
    def __init__(self, config):
        self.config = config
        self.microservice_name = config['MICROSERVICE_NAME']
        self.secrets = config.get('SECRETS', {})

    def generate_resources(self):
        namespace = Namespace(f'namespace-{self.microservice_name}')

        resources = []
        for resource_config in self.config['resources']:
            component_name = resource_config['component_name']
            docker_image = resource_config['docker_image']
            replicas = resource_config['replicas']
            port = resource_config.get('port')

            deployment = Deployment(f'{component_name}-deployment-{self.microservice_name}', docker_image, replicas)            
            resources.extend([deployment])

            if port is not None:
                service = Service(f'{component_name}-service-{self.microservice_name}', port)
                resources.append(service)

            if 'db_secrets' in resource_config:
                secret_data = resource_config['db_secrets']
                secret = Secret(f'{component_name}-secret-{self.microservice_name}', secret_data)
                resources.append(secret)

        # Asociar todos los recursos al mismo Namespace
        for resource in resources:
            resource.metadata['namespace'] = self.microservice_name

        return [namespace] + resources

    def write_yaml_files(self, resources):
        # Crear el directorio 'k8s' si no existe
        k8s_dir = 'k8s'
        if not os.path.exists(k8s_dir):
            os.makedirs(k8s_dir)

        # Escribir archivos YAML en el directorio 'k8s'
        for resource in resources:
            with open(os.path.join(k8s_dir, f'{self.microservice_name}-{resource.name}.yaml'), 'w') as f:
                f.write(resource.generate_yaml())

if __name__ == "__main__":
    with open('config.json') as config_file:
        config = json.load(config_file)

    deployer = KubernetesDeployer(config)
    resources = deployer.generate_resources()
    deployer.write_yaml_files(resources)
