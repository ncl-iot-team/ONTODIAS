#! /usr/bin/env python

import tensorflow as tf
import numpy as np
import os
import time
import datetime
from core.machine_learning.cnn_classification import data_helpers
from core.machine_learning.cnn_classification.text_cnn import TextCNN
from tensorflow.contrib import learn
from tqdm import tqdm

from core.consts.configure import CNN_YML_CONFIG_FILE

'''
    pip3 install tqdm
'''

def train():
    '''
        此程序单独运行的话不需要改路径
        如果需要联合运行 需要 core/nlp_engine_cnn/

    '''

    # 获取当前路径
    current_path = os.path.dirname(os.path.realpath(__file__))


    # 获取config
    train_config = CNN_YML_CONFIG_FILE["cnn"]["classfication"]["training"]  # 通过字典的取值来取值

    '''
        Define parameters
        @param1 参数名 Name
        @param2 默认值 Value
        @param3 描述 Description
    '''
    # Define testing data set rate
    # 定义测试集
    tf.flags.DEFINE_float("dev_sample_percentage", .1, "Percentage of the training data to use for validation")
    # Define training data set loading path
    # 定义数据的路径
    tf.flags.DEFINE_string("class_Flood_data_file",
                           current_path+"/"+train_config["class_Flood_data_file"],
                           "Data source for the Flood class data.")
    tf.flags.DEFINE_string("class_IncreaseInWaterLevel_data_file",
                           current_path+"/"+train_config["class_IncreaseInWaterLevel_data_file"],
                           "Data source for the IncreaseInWaterLevel class data.")
    tf.flags.DEFINE_string("class_Landslide_data_file",
                           current_path+"/"+train_config["class_Landslide_data_file"],
                           "Data source for the Landslide class data.")
    tf.flags.DEFINE_string("class_LeaningTelephonePole_data_file",
                           current_path+"/"+train_config["class_LeaningTelephonePole_data_file"],
                           "Data source for the LeaningTelephonePole class data.")
    tf.flags.DEFINE_string("class_Others_data_file",
                           current_path+"/"+train_config["class_Others_data_file"],
                           "Data source for the Others class data.")

    '''
        Define model hyper-parameters
    '''

    # 定义隐层的维度
    tf.flags.DEFINE_integer("embedding_dim", train_config["embedding_dim"], "Dimensionality of character embedding (default: 128)")
    # 定义filter_size
    tf.flags.DEFINE_string("filter_sizes", train_config["filter_sizes"], "Comma-separated filter sizes (default: '3,4,5,6')")
    # 定义特征图数量
    tf.flags.DEFINE_integer("num_filters", train_config["num_filters"], "Number of filters per filter size (default: 128)")
    # 定义dropout
    tf.flags.DEFINE_float("dropout_keep_prob", train_config["dropout_keep_prob"], "Dropout keep probability (default: 0.5)")
    # 定义L2惩罚项
    tf.flags.DEFINE_float("l2_reg_lambda", train_config["l2_reg_lambda"], "L2 regularization lambda (default: 0.0)")


    '''
        Define training parameters
    '''

    # 定义batch_size
    tf.flags.DEFINE_integer("batch_size", train_config["batch_size"], "Batch Size (default: 64)")
    # 定义迭代轮次
    tf.flags.DEFINE_integer("num_epochs", train_config["num_epochs"], "Number of training epochs (default: 200)")
    # 定义评估频率
    tf.flags.DEFINE_integer("evaluate_every", train_config["evaluate_every"], "Evaluate model on dev set after this many steps (default: 100)")
    # 定义模型保存频率
    tf.flags.DEFINE_integer("checkpoint_every", train_config["checkpoint_every"], "Save model after this many steps (default: 100)")
    # 定义check point
    tf.flags.DEFINE_integer("num_checkpoints", train_config["num_checkpoints"], "Number of checkpoints to store (default: 5)")


    '''
        Define Misc Parameters
    '''

    # 当指定设备不存在时候，是否自动分配设备 CPU GPU
    tf.flags.DEFINE_boolean("allow_soft_placement", train_config["allow_soft_placement"], "Allow device soft device placement")
    # 是否打印日志
    tf.flags.DEFINE_boolean("log_device_placement", train_config["log_device_placement"], "Log placement of ops on devices")

    # 定义vocb 路径
    tf.flags.DEFINE_string("vocab_dir", current_path+"/"+train_config["vocab_dir"], "Vocab saving path")

    '''
        Define Misc Parameters
        解析Flag并打印参数
    '''

    FLAGS = tf.flags.FLAGS
    # 老版本为 ： FLAGS._parse_flags()
    FLAGS.flag_values_dict()
    # print("\nAll parameters list :")
    # # 排序打印
    # for attr, value in sorted(FLAGS.__flags.items()):
    #     print("{} = {}".format(attr.upper(), value))
    # print("=================================================================================")


    '''
        Data Preparation
    '''

    # Load data
    # 加载数据
    print("Loading data...")

    x_text, y = data_helpers.load_data_and_labels(
        FLAGS.class_Flood_data_file,
        FLAGS.class_IncreaseInWaterLevel_data_file,
        FLAGS.class_Landslide_data_file,
        FLAGS.class_LeaningTelephonePole_data_file,
        FLAGS.class_Others_data_file
    )

    # Build vocabulary
    # 获取最大长度
    max_document_length = max([len(x.split(" ")) for x in x_text])
    # 填充0补全为最大长度
    vocab_processor = learn.preprocessing.VocabularyProcessor(max_document_length)
    x = np.array(list(vocab_processor.fit_transform(x_text)))

    # Randomly shuffle data
    # 洗数据
    np.random.seed(10)
    shuffle_indices = np.random.permutation(np.arange(len(y)))
    x_shuffled = x[shuffle_indices]
    # https://blog.csdn.net/accumulate_zhang/article/details/78808038 为什么用np.array
    y_shuffled = np.array(y)[shuffle_indices]

    # Split train/test set
    # TODO: This is very crude, should use cross-validation
    # 乘 -1 因为想做一个从后往前取  如果为-100  从后往前去我100 个作为验证集
    dev_sample_index = -1 * int(FLAGS.dev_sample_percentage * float(len(y)))
    x_train, x_dev = x_shuffled[:dev_sample_index], x_shuffled[dev_sample_index:]
    y_train, y_dev = y_shuffled[:dev_sample_index], y_shuffled[dev_sample_index:]
    print("Vocabulary Size: {:d}".format(len(vocab_processor.vocabulary_)))
    print("Train/Dev split: {:d}/{:d}".format(len(y_train), len(y_dev)))


    '''
        Training 
    '''

    with tf.Graph().as_default():
        # 设置 session 参数
        session_conf = tf.ConfigProto(
          allow_soft_placement=FLAGS.allow_soft_placement,
          log_device_placement=FLAGS.log_device_placement)
        # 导入session
        sess = tf.Session(config=session_conf)

        # 定义CNN
        with sess.as_default():
            cnn = TextCNN(
                sequence_length=x_train.shape[1],
                #分成几类
                num_classes=y_train.shape[1],
                vocab_size=len(vocab_processor.vocabulary_),
                embedding_size=FLAGS.embedding_dim,
                filter_sizes=list(map(int, FLAGS.filter_sizes.split(","))),
                num_filters=FLAGS.num_filters,
                l2_reg_lambda=FLAGS.l2_reg_lambda)

            # Define Training procedure
            global_step = tf.Variable(0, name="global_step", trainable=False)
            # 指定Adam优化器
            optimizer = tf.train.AdamOptimizer(1e-3)
            # 获取梯度
            grads_and_vars = optimizer.compute_gradients(cnn.loss)
            train_op = optimizer.apply_gradients(grads_and_vars, global_step=global_step)

            # Keep track of gradient values and sparsity (optional)
            grad_summaries = []
            for g, v in grads_and_vars:
                if g is not None:
                    grad_hist_summary = tf.summary.histogram("{}/grad/hist".format(v.name), g)
                    sparsity_summary = tf.summary.scalar("{}/grad/sparsity".format(v.name), tf.nn.zero_fraction(g))
                    grad_summaries.append(grad_hist_summary)
                    grad_summaries.append(sparsity_summary)
            grad_summaries_merged = tf.summary.merge(grad_summaries)

            # Output directory for models and summaries
            timestamp = str(int(time.time()))
            out_dir = os.path.abspath(os.path.join(current_path, "runs", timestamp))
            print("Writing to {}\n".format(out_dir))

            # Summaries for loss and accuracy
            loss_summary = tf.summary.scalar("loss", cnn.loss)
            acc_summary = tf.summary.scalar("accuracy", cnn.accuracy)

            # Train Summaries
            train_summary_op = tf.summary.merge([loss_summary, acc_summary, grad_summaries_merged])
            train_summary_dir = os.path.join(out_dir, "summaries", "train")
            train_summary_writer = tf.summary.FileWriter(train_summary_dir, sess.graph)

            # Dev summaries
            dev_summary_op = tf.summary.merge([loss_summary, acc_summary])
            dev_summary_dir = os.path.join(out_dir, "summaries", "dev")
            dev_summary_writer = tf.summary.FileWriter(dev_summary_dir, sess.graph)

            # Checkpoint directory. Tensorflow assumes this directory already exists so we need to create it
            checkpoint_dir = os.path.abspath(os.path.join(out_dir, "checkpoints"))
            checkpoint_prefix = os.path.join(checkpoint_dir, "model")
            if not os.path.exists(checkpoint_dir):
                os.makedirs(checkpoint_dir)

            # 保存model
            saver = tf.train.Saver(tf.global_variables(), max_to_keep=FLAGS.num_checkpoints)

            # Write vocabulary
            vocab_processor.save(os.path.join(out_dir, "vocab"))

            # Write vocabulary use for detect
            vocab_processor.save(os.path.join(FLAGS.vocab_dir, "vocab"))

            # Initialize all variables
            sess.run(tf.global_variables_initializer())

            def train_step(x_batch, y_batch, bar):
                """
                A single training step
                """
                feed_dict = {
                  cnn.input_x: x_batch,
                  cnn.input_y: y_batch,
                  cnn.dropout_keep_prob: FLAGS.dropout_keep_prob
                }
                _, step, summaries, loss, accuracy = sess.run(
                    [train_op, global_step, train_summary_op, cnn.loss, cnn.accuracy],
                    feed_dict)
                time_str = datetime.datetime.now().isoformat()
                bar.set_description('{}: step {}, loss={:.6f}, acc {:g}'.format(
                    time_str,
                    step,
                    loss,
                    accuracy
                ))
                # print("{}: step {}, loss {:g}, acc {:g}".format(time_str, step, loss, accuracy))
                train_summary_writer.add_summary(summaries, step)

            def dev_step(x_batch, y_batch, writer=None):
                """
                Evaluates model on a dev set
                """
                feed_dict = {
                  cnn.input_x: x_batch,
                  cnn.input_y: y_batch,
                  cnn.dropout_keep_prob: 1.0
                }
                step, summaries, loss, accuracy = sess.run(
                    [global_step, dev_summary_op, cnn.loss, cnn.accuracy],
                    feed_dict)
                time_str = datetime.datetime.now().isoformat()
                print("{}: step {}, loss {:g}, acc {:g}".format(time_str, step, loss, accuracy))
                if writer:
                    writer.add_summary(summaries, step)

            # Generate batches
            batches = data_helpers.batch_iter(
                list(zip(x_train, y_train)), FLAGS.batch_size, FLAGS.num_epochs)
            # Training loop. For each batch...

            bar = tqdm(batches, total=(int(len(x_text)/FLAGS.batch_size))*FLAGS.num_epochs/100*100)

            for batch in bar:
                x_batch, y_batch = zip(*batch)
                train_step(x_batch, y_batch, bar)
                current_step = tf.train.global_step(sess, global_step)
                if current_step % FLAGS.evaluate_every == 0:
                    print("\nEvaluation:")
                    dev_step(x_dev, y_dev, writer=dev_summary_writer)
                    print("")
                if current_step % FLAGS.checkpoint_every == 0:
                    path = saver.save(sess, current_path+"/"+"models/landslipPred", global_step=current_step)
                    print("Saved model checkpoint to {}\n".format(path))


