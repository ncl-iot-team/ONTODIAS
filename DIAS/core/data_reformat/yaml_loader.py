import os
import yaml


class YAMLLoader:

    def load_file(self, file_path, file_name):

        yml = os.path.join(file_path, file_name)

        file = open(yml)  # 打开yaml文件

        config = yaml.load(file, Loader=yaml.FullLoader)

        return config  # 使用load方法加载

