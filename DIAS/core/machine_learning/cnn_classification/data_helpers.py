import numpy as np
import re


def clean_str(string):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()


# 加载文件
def load_data_and_labels(*files):
    """
    Loads MR polarity data from files, splits the data into words and generates labels.
    Returns split sentences and labels.
    """

    x_text = []
    y_labels = []

    # Load data from all files
    for data_file in files:

        # 加载数据
        data = open(data_file, "rb").read().decode('utf-8')

        # 按换行分割   最后一行会有一个回车
        data_without_enter = data.split('\n')[:-1]

        # 去掉空格
        data_without_space = [s.strip() for s in data_without_enter]

        x_text += data_without_space

        # 需要测试不知道可不可行

        names = data_file.split("/")

        class_tags = []

        if "Flood" in names:
            class_tags = [0, 0, 0, 0, 1]
        elif "IncreaseInWaterLevel" in names:
            class_tags = [0, 0, 0, 1, 0]
        elif "Landslide" in names:
            class_tags = [0, 0, 1, 0, 0]
        elif "LeaningTelephonePole" in names:
            class_tags = [0, 1, 0, 0, 0]
        elif "Others" in names:
            class_tags = [1, 0, 0, 0, 0]

        labels = [class_tags for _ in data_without_space]

        #组合所有标签
        y_labels += labels

    # Split by words
    # 清理数据中的字符
    x_text = [clean_str(sent) for sent in x_text]

    return [x_text, y_labels]


def batch_iter(data, batch_size, num_epochs, shuffle=True):
    """
    Generates a batch iterator for a dataset.
    """
    data = np.array(data)
    data_size = len(data)
    # 计算每个epoch 需要多少次迭代  保守 加1
    num_batches_per_epoch = int((len(data)-1)/batch_size) + 1
    for epoch in range(num_epochs):
        # Shuffle the data at each epoch
        if shuffle:
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
        else:
            shuffled_data = data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield shuffled_data[start_index:end_index]
