import unittest
from unittest.mock import patch
import os
import yaml
from dotenv import load_dotenv

from deployer import (KubernetesResource, Deployment, Service,
                      Namespace, Secret, KubernetesDeployer)

class TestKubernetesResource(unittest.TestCase):
    def test_generate_yaml_not_implemented(self):
        resource = KubernetesResource('test')
        with self.assertRaises(NotImplementedError):
            resource.generate_yaml()

class TestDeployment(unittest.TestCase):
    def test_generate_yaml(self):
        deployment = Deployment('test', 'image', 3)
        expected_yaml = """<YOUR_EXPECTED_YAML_HERE>"""
    
        self.assertEqual(deployment.generate_yaml(), expected_yaml)

class TestService(unittest.TestCase):
    def test_generate_yaml(self):
        service = Service('test')
        expected_yaml = """<YOUR_EXPECTED_YAML_HERE>"""
        self.assertEqual(service.generate_yaml(), expected_yaml)


class TestKubernetesDeployer(unittest.TestCase):
    def test_load_environment_variables(self):
        with patch.dict(os.environ, {'DB_NAME': 'test_db'}):
            deployer = KubernetesDeployer('test', 'image', 3)
            deployer.load_environment_variables()
            self.assertEqual(deployer.db_name, 'test_db')


if __name__ == '__main__':
    unittest.main()
