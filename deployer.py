import os
import yaml
import json
import base64

class KubernetesResource:
    def __init__(self, name):
        self.name = name
        self.metadata = {}

    def generate_yaml(self):
        raise NotImplementedError("Subclasses must implement generate_yaml method")

class Deployment(KubernetesResource):
    def __init__(self, microservice_name, name, image, replicas, related_resources=None):
        super().__init__(name)
        self.image = image
        self.replicas = replicas     
        self.related_resources = related_resources   
        self.microservice_name = microservice_name

    def generate_yaml(self):

        
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': self.metadata,
            'spec': {
                'replicas': self.replicas,
                'selector': {
                    'matchLabels': {
                        'app': f'{self.name}'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': f'{self.name}'
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': f'{self.name}',
                            'image': self.image,
                            'ports': [{
                                'containerPort': 8080
                            }],
                            'envFrom': self._related_resources()
                        }]
                    }
                }
            }
        }
        return yaml.dump(deployment)

    def _related_resources(self):        
        env_from = []
        for related  in self.related_resources:
            if 'secret' in related:
                secret_references = related.get("secret")
                env_from.append({'secretRef': {'name': f'{self.microservice_name}-{secret_references}-secret'}})
            return env_from


class Service(KubernetesResource):
    def __init__(self, name, port):
        super().__init__(name)
        self.port = port

    def generate_yaml(self):
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': self.metadata,
            'spec': {
                'selector': {
                    'app': f'{self.name}'
                },
                'ports': [{
                    'protocol': 'TCP',
                    'port': self.port,
                    'targetPort': self.port
                }]
            }
        }
        return yaml.dump(service)

class ConfigMap(KubernetesResource):
    def __init__(self, name, data):
        super().__init__(name)
        self.data = data

    def generate_yaml(self):
        config_map = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': self.metadata,
            'data': self.data
        }
        return yaml.dump(config_map)

class Namespace(KubernetesResource):
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

    def generate_yaml(self):
        encoded_data = {key: base64.b64encode(value.encode('utf-8')).decode('utf-8') for key, value in self.data.items()}
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': f'{self.name}'
            },
            'data': encoded_data
        }
        return yaml.dump(secret)

class KubernetesDeployer:
    def __init__(self, config):
        self.config = config
        self.microservice_name = config['MICROSERVICE_NAME']        

    def generate_resources(self):
        namespace = Namespace(f'namespace-{self.microservice_name}')
        resources = [namespace]

        resource_map = {}

        for resource_config in self.config['resources']:
            component_name = resource_config['component_name']
            docker_image = resource_config['docker_image']
            replicas = resource_config['replicas']
            config_data = resource_config.get('config', {})
            port = resource_config.get('port')
            related_resources = resource_config.get('related_resources', [])
        
            deployment_name = f'{self.microservice_name}-{component_name}-deployment'
            deployment = Deployment(self.microservice_name, deployment_name, docker_image, replicas, related_resources)
            resources.append(deployment)
            resource_map[component_name] = deployment


            # Service
            if port is not None:
                service_name = f'{self.microservice_name}-{component_name}-service'
                service = Service(service_name, port)
                resources.append(service)
                resource_map[f'{component_name}-service'] = service

            # Secret
            if 'db_secrets' in resource_config:
                secret_data = resource_config['db_secrets']
                secret_name = f'{self.microservice_name}-{component_name}-secret'
                secret = Secret(secret_name, secret_data)
                resources.append(secret)
                resource_map[f'{component_name}-secret'] = secret

            # ConfigMap
            if config_data:
                config_map_name = f'{self.microservice_name}-{component_name}-config'
                config_map = ConfigMap(config_map_name, config_data)
                resources.append(config_map)
                resource_map[f'{component_name}-config'] = config_map
            

        # Set namespace for all resources
        for resource in resources:
            resource.metadata['namespace'] = self.microservice_name
            resource.metadata['name'] = f'{self.microservice_name}-{component_name}'


        return resources

    def write_yaml_files(self, resources):
        k8s_dir = 'k8s'
        if not os.path.exists(k8s_dir):
            os.makedirs(k8s_dir)

        for resource in resources:
            with open(os.path.join(k8s_dir, f'{self.microservice_name}-{resource.name}.yaml'), 'w') as f:
                f.write(resource.generate_yaml())


if __name__ == "__main__":
    with open('config.json') as config_file:
        config = json.load(config_file)

    deployer = KubernetesDeployer(config)
    resources = deployer.generate_resources()
    deployer.write_yaml_files(resources)