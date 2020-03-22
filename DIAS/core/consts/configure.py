'''
        START CONFIGURATION FILE LOAD
'''
# datasource_config.yaml
from core.data_reformat.yaml_loader import YAMLLoader

yml_loader = YAMLLoader()
DATASOURCE_YML_CONFIG_FILE = yml_loader.load_file(file_path="./conf", file_name="datasource_config.yaml")

# cnn_config.yaml
CNN_YML_CONFIG_FILE = yml_loader.load_file(file_path="./conf", file_name="cnn_classification.yaml")

# ontology_config.yaml
ONTOLOGY_YML_CONFIG_FILE = yml_loader.load_file(file_path="./conf", file_name="ontology_config.yaml")

# ontology_config.yaml
SYSTEM_CONFIG_FILE = yml_loader.load_file(file_path="./conf", file_name="sys_config.yaml")

'''
        END CONFIGURATION FILE LOAD
'''

