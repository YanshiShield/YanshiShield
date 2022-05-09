#  Copyright 2022 The Neursafe FL Authors. All Rights Reserved.
#  SPDX-License-Identifier: Apache-2.0

# pylint:disable=no-member, bad-str-strip-call
"""Federated Learning Visualization Module.

The backend of this module is Tensorboard, references:
https://github.com/tensorflow/tensorboard
"""

import tensorflow as tf

tf.compat.v1.disable_v2_behavior()


class FlBoard:
    """Federate Learning Board.

    FlBoard implement blocks of web page that needs to be displayed. Including
    Job info, round info, training status, log and so on. Each block with
    different style.
    Mainly including Text and Scalar Dashboard.

    Attributes:
        __board: backend interface package of tensorboard.
        __style: markdown style of string.
    """
    LOG_SCOPE = "Server_Log"
    ROUND_SCOPE = "Round_Info"
    FL_SCOPE = "Federate_Learning_Settings"
    CLIENT_SCOPE = "Client_Details"

    def __init__(self):
        self.__board = None
        self.__style = None
        self.__round_num = 0

        self._initialize()

    def _initialize(self):
        log_dir = "./tb_logs"
        self.__board = Board(log_dir)
        self.__style = MDStyle()

    def add_job_info(self, data):
        """Job summary info

        Display in the form of text with markdown.
        """
        preamble = "     Job Summary    \n"
        preamble = self.__style.header(preamble, size=2)
        content = ["%s: %s  \n" % (k, v) for k, v in data.items()]
        content = self.__style.header(content, size=3)
        split_line = "---  \n"
        text = tf.strings.join([preamble, split_line, content])
        self.__board.add_text(text, tag="BaseInfo", name_scope=self.FL_SCOPE)

    def add_hyper_params(self, data):
        """Job hyper parameters of federate learning.

        Display in the form of text with markdown.
        """
        preamble = "     Hyper Parameters    \n"
        preamble = self.__style.header(preamble, size=2)
        content = ["%s: %s  \n" % (k, v) for k, v in data.items()]
        content = self.__style.header(content, size=3)
        split_line = "---  \n"
        text = tf.strings.join([preamble, split_line, content])
        self.__board.add_text(text, tag="HyperParams", name_scope=self.FL_SCOPE)

    def add_client_info(self, clients):
        """Clients info that participate in this job.

        Display in the form of a table in Text.
        """
        preamble = "     Client Details    \n"
        preamble = self.__style.header(preamble, size=2)
        table = self.__board.add_table(clients[0].keys())
        for client in clients:
            table = self.__board.insert_table_row(table, client.values())
        split_line = "---  \n"
        text = tf.strings.join([preamble, split_line, table])
        self.__board.add_text(text, tag="Clients", name_scope=self.CLIENT_SCOPE)

    def add_round_info(self, data, round_num):
        """Round statistics info

        Display in the form of a table in Text.
        """
        preamble = "Current Round %s details:  \n" % round_num
        preamble = self.__style.header(preamble, size=4)
        table = self.__board.add_table(data.keys())
        table = self.__board.insert_table_row(table, data.values())
        text = tf.strings.join([preamble, table])
        self.__board.add_text(text, tag="Round Details",
                              name_scope=self.ROUND_SCOPE)

    def add_log(self, data, round_num):
        """Round coordinator log

        Display in the form of text.
        """
        preamble = "Current Round %s log:  \n" % round_num
        preamble = self.__style.header(preamble, size=4)
        log = self.__style.text(data, bold=True)
        split_line = "---  \n"
        text = tf.strings.join([preamble, split_line, log])
        self.__board.add_text(text, tag="Round Log", name_scope=self.LOG_SCOPE)

    def plot_metrics(self, metrics, round_num):
        """Training metrics curve.

        Display in the form of a curve graph in Scalar.
        Including loss, accuracy and so on.
        """
        for key, val in metrics.items():
            self.__board.add_scalar(key, float(val), round_num)

    def add_statistics(self):
        """Final statistics of federate learning.

        Display in the form of Text.
        """

    def refresh(self, round_num):
        """Refresh memory data to local hard disk.
        """
        self.__board.refresh(round_num)

    def close(self):
        """Close the file writer of tensorboard.
        """
        self.__board.close()


class Board:
    """Module wraps the tensorboard interface.

    Providing basic dashboard interface, such as Text, Scalar, Graph and so on.
    More internal display styles should use tensorboard module directly.

    Attributes:
        log_dir: the directory of event files to be saved.
    """

    def __init__(self, log_dir):
        self.__writer = tf.compat.v1.summary.FileWriter(log_dir)
        self.__step_placeholder = 0
        tf.compat.v1.reset_default_graph()

    def refresh(self, round_num):
        """refresh the memory summary into disk.
        """
        self.__step_placeholder = tf.compat.v1.placeholder(tf.int32)
        with tf.compat.v1.Session() as sess:
            all_summaries = tf.compat.v1.summary.merge_all()
            summary = sess.run(all_summaries,
                               feed_dict={self.__step_placeholder: round_num})
            self.__writer.add_summary(summary, global_step=round_num)

    def close(self):
        """Close the file writer of tensorboard.
        """
        self.__writer.close()

    def add_scalar(self, key, value, step=0):
        """Add Scalar data of tenorboard.

        Args:
            key: the data name of the displayed graph, such as loss, accuracy.
            value: the value of this data in current step. (y-axis)
            step: the current step. (x-axis)
        """
        with self.__writer.as_default():
            tf.summary.scalar(key, value, step=step)

    def add_text(self, text, tag, name_scope="Default"):
        """Add Text data of tenorboard.

        Args:
            text: the text data need to be displayed.
            tag: tag(label) for the displayed text.
            name_scope: the namespace of this text.(or block)
        """
        with tf.name_scope(name_scope):
            tf.compat.v1.summary.text(tag, text)

    def add_table(self, headers):
        """Add a table in a Text block.

        Args:
            headers: the table header info, list. each item reference a column.
        Returns:
            the string form of the table header.
        """
        header_row = "".join(["%s | " % item for item in headers]).rstrip(" | ")
        split_line = "".join(["---|" for _ in headers]).rstrip("|")
        table = tf.strings.join([header_row, split_line], separator="\n")
        return table

    def insert_table_row(self, table, row_values):
        """Insert one row to a table.

        Args:
            table: the string form of the table header.
            row_values: the values of one row, list.
        Returns:
            the string form of the table with new row values.
        """
        row = "".join(["%s | " % item for item in row_values]).rstrip(" | ")
        table_row = tf.strings.reduce_join(inputs=row, separator="\n")
        insert_table = tf.strings.join([table, table_row], separator="\n")
        return insert_table


class MDStyle:
    """Module convert the string to MarkDown style.
    """

    def header(self, text, size=6):
        """Convert the string the markdown header.

        Args:
            text: the title content.
            size: the header size, form 1 ~ 6 level.
        """
        form = "#" * size
        if isinstance(text, list):
            return form + form.join(text)

        return "".join([form, text])

    def text(self, text, bold=False, italic=False):
        """Convert the string to bold or italic markdown style.
        """
        if bold and italic:
            return "***%s***" % text
        if bold:
            return "**%s**" % text
        if italic:
            return "*%s*" % text
        return text

    def code(self):
        """Code block"""
