#! /usr/bin/env python

import tensorflow as tf
import numpy as np
import os

from core.machine_learning.cnn_classification import data_helpers
from tensorflow.contrib import learn

from core.consts.configure import CNN_YML_CONFIG_FILE,ONTOLOGY_YML_CONFIG_FILE
from core.ontology.StardogDatabase import StardogDatabase
from loguru import logger
from core.consts.machine_learning import CLASS_INDEX

# 获取当前路径
current_path = os.path.dirname(os.path.realpath(__file__))

# 获取配置信息
predict_config = CNN_YML_CONFIG_FILE["cnn"]["classfication"]["predicting"]

sparql_query_config = ONTOLOGY_YML_CONFIG_FILE["prefix"]["query"]

'''
    Define parameters
    @param1 参数名 Name
    @param2 默认值 Value
    @param3 描述 Description
'''

# Define training data set loading path
# 定义数据的路径
tf.flags.DEFINE_string("class_Flood_data_file",
                        current_path + "/" + predict_config["class_Flood_data_file"],
                       "Data source for the Flood class data.")
tf.flags.DEFINE_string("class_IncreaseInWaterLevel_data_file",
                        current_path + "/" + predict_config["class_IncreaseInWaterLevel_data_file"],
                       "Data source for the IncreaseInWaterLevel class data.")
tf.flags.DEFINE_string("class_Landslide_data_file",
                        current_path + "/" + predict_config["class_Landslide_data_file"],
                       "Data source for the Landslide class data.")
tf.flags.DEFINE_string("class_LeaningTelephonePole_data_file",
                        current_path + "/" + predict_config["class_LeaningTelephonePole_data_file"],
                       "Data source for the LeaningTelephonePole class data.")
tf.flags.DEFINE_string("class_Others_data_file",
                        current_path + "/" + predict_config["class_Others_data_file"],
                        "Data source for the Others class data.")


# Eval Parameters
tf.flags.DEFINE_integer("batch_size", predict_config["batch_size"], "Batch Size (default: 64)")
tf.flags.DEFINE_string("checkpoint_dir",  current_path, "Checkpoint directory from training run")
tf.flags.DEFINE_string("model_dir", current_path + "/" + predict_config["model_dir"], "Model dir")
tf.flags.DEFINE_string("vocab_dir", current_path + "/" + predict_config["vocab_dir"], "Vocab dir")

# Misc Parameters
tf.flags.DEFINE_boolean("allow_soft_placement",
                        predict_config["allow_soft_placement"],
                        "Allow device soft device placement")
tf.flags.DEFINE_boolean("log_device_placement",
                        predict_config["log_device_placement"],
                        "Log placement of ops on devices")

FLAGS = tf.flags.FLAGS
# 老版本为 ： FLAGS._parse_flags()
FLAGS.flag_values_dict()
# print("\nParameters:")
# for attr, value in sorted(FLAGS.__flags.items()):
#     print("{}={}".format(attr.upper(), value))
# print("")


def predict(x_raw):

    # Map data into vocabulary
    vocab_path = os.path.join(FLAGS.vocab_dir, "vocab")
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform(x_raw)))

    logger.info("\nEvaluating...\n")

    '''
        Evaluation
    '''
    # checkpoint_file = tf.train.latest_checkpoint(FLAGS.checkpoint_dir)
    graph = tf.Graph()
    with graph.as_default():
        session_conf = tf.ConfigProto(
          allow_soft_placement=FLAGS.allow_soft_placement,
          log_device_placement=FLAGS.log_device_placement)
        sess = tf.Session(config=session_conf)
        with sess.as_default():
            # Load the saved meta graph and restore variables
            saver = tf.train.import_meta_graph("{}.meta".format(FLAGS.model_dir))
            saver.restore(sess, FLAGS.model_dir)

            # Get the placeholders from the graph by name
            input_x = graph.get_operation_by_name("input_x").outputs[0]
            # input_y = graph.get_operation_by_name("input_y").outputs[0]
            dropout_keep_prob = graph.get_operation_by_name("dropout_keep_prob").outputs[0]

            # Tensors we want to evaluate
            predictions = graph.get_operation_by_name("output/predictions").outputs[0]

            scores = graph.get_operation_by_name("output/scores").outputs[0]

            # Generate batches for one epoch
            batches = data_helpers.batch_iter(list(x_test), FLAGS.batch_size, 1, shuffle=False)

            # Collect the predictions here
            all_predictions = []
            all_scores = []
            for x_test_batch in batches:

                all_predictions = sess.run(predictions, {input_x: x_test_batch, dropout_keep_prob: 1.0})
                all_scores = sess.run(scores, {input_x: x_test_batch, dropout_keep_prob: 1.0})

    logger.debug("=======================================================")
    logger.debug("All score for every classes :")
    logger.debug(all_scores)
    # 方便显示用
    all_class_display = ["Others","LeaningTelephonePole","Landslide","IncreaseInWaterLevel","Flood"]
    logger.debug(all_class_display)
    logger.debug("=======================================================")
    logger.debug("The arg max : ")
    logger.debug(all_predictions)
    logger.debug("=======================================================")

    # 临时类型和sparql对照字典
    warning_sign_sparql_dict ={
        "Landslide": "landslide_2",
        "LeaningTelephonePole": "leaning_telephone_pole_1"
    }

    all_ontology_result = {}

    # 更新预测文件的class为可读型
    all_predictions_class_name =[]

    cnn_pred_result = []
    i = 0

    sd = StardogDatabase()
    logger.info("all_predictions :",all_predictions)
    for index in all_predictions:

        all_predictions_class_name.append(CLASS_INDEX[index])
        cnn_pred_result.append(CLASS_INDEX[index])
        # 此处可以优化为key调方法

        logger.debug("| Input : " + x_raw[i] + " | Class : "+CLASS_INDEX[index]+" | ")
        logger.debug("=======================================================")


        # Warning sign
        if index == 3:

            # ontology 查询
            all_ontology_result["IncreaseInWaterLevel"] = sd.pred_query(warning_sign_sparql_dict["IncreaseInWaterLevel"],
                                                                     sparql_query_config["by_warning_sign"])
        # Warning sign
        elif index == 1:

            # ontology 查询
            all_ontology_result["LeaningTelephonePole"] = sd.pred_query(warning_sign_sparql_dict["LeaningTelephonePole"],sparql_query_config["by_warning_sign"])

        # Hazards
        elif index !=0:
            all_ontology_result[CLASS_INDEX[index]] = CLASS_INDEX[index]

        i += 1


    # # Save the evaluation to a csv
    # predictions_human_readable = np.column_stack((np.array(x_raw), all_predictions_class_name))
    # out_path = os.path.join(FLAGS.checkpoint_dir, "predictions/", "prediction_"+str(datetime.datetime.now().isoformat())+".csv")
    # logger.debug("Saving evaluation to {0}".format(out_path))
    # with open(out_path, 'w') as f:
    #     csv.writer(f).writerows(predictions_human_readable)

    return cnn_pred_result,all_ontology_result



