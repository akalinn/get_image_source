# -*- coding: utf-8 -*-

import compute
import sys
import re
import os
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QComboBox

# GUI下拉栏显示为关键词的时候state为0 
_INCLUDE_KEYWORDS = 0
# GUI下拉栏显示为屏蔽词的时候state为1  
_EXCLUDE_KEYWORDS = 1

class ResumeFilterGUI(QWidget):
    """
    功能描述：主要实现了简历筛选文件的GUI功能。包括功能：关键词/屏蔽词导入
             保存导出，关键词格式检测，关键词，屏蔽词，简历文件名的归类，
             以及输出到界面以及保存到文本。
    """
    def __init__(self):
        """
        初始化
        """
        super().__init__()
        # 设置窗口大小和标题
        self.setGeometry(500, 150, 700, 800)
        self.setWindowTitle("简历筛选")
        
        # 字典格式的关键词， 具体格式为{"关键词":[匹配度，软硬度]
        self.dict_keywords = {}
        # 屏蔽词字符串表示
        self.exclude_words = ""
        # 关键词字符串表示
        self._keywords = ""
        # 错误关键词列表
        self._error_lines = []
        # 计算后返回结果：包不包含屏蔽词
        self._result_with = ""
        self._result_with_out = ""
        # 简历保存文件夹地址
        self.resume_dir = ""
        # flag，检查当前在处理关键词还是屏蔽词
        self._current_state = _INCLUDE_KEYWORDS
        # 当切换关键词/屏蔽词时，备份窗口关键词/屏蔽词信息
        self._word_insert_bk = ""

        self.initUI()
        self.show()

    def initUI(self):
        """
        功能描述：GUI参数初始化和界面布局
        """
        # 按键，下拉栏，文本框初始化
        search_btn = QPushButton("筛选", self)
        output_result_btn = QPushButton('导出排名', self)
        clear_btn = QPushButton("清空", self)
        key_load_btn = QPushButton("导入", self)
        save_key_btn = QPushButton("保存", self)
        output_key_btn = QPushButton("另存为", self)

        combo = QComboBox(self)
        combo.addItem("关键词")
        combo.addItem("屏蔽词")
        
        self.search_result = QTextEdit()
        self.word_insert = QTextEdit()

        # 按钮，文本栏，下拉栏的位置设定
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.addWidget(combo, 4, 0)
        grid.addWidget(search_btn, 1, 1)
        grid.addWidget(output_result_btn, 2, 1)
        grid.addWidget(clear_btn, 3, 1)
        grid.addWidget(key_load_btn, 1, 0)
        grid.addWidget(save_key_btn, 2, 0)
        grid.addWidget(output_key_btn, 3, 0)
        grid.addWidget(self.search_result, 4, 1, 3 , 1)
        grid.addWidget(self.word_insert, 5, 0)
        self.setLayout(grid)
 
        # 按钮和下拉栏的功能设定
        self.search_result.setText("")
        self.word_insert.setText("")
        search_btn.clicked.connect(self.search)
        clear_btn.clicked.connect(self.clear)
        key_load_btn.clicked.connect(lambda: self.load(self._keywords, self._current_state))
        output_result_btn.clicked.connect(self.save_result)
        save_key_btn.clicked.connect(lambda: self.save(self._current_state))
        output_key_btn.clicked.connect(lambda: self.save_text(self.word_insert))
        combo.activated[str].connect(self.onActivate)

        # 窗口的美观设计
        self.setStyleSheet(
            """
            QPushButton {
                background-color: rgb(255, 250, 250);
                border: 1px solid rgb(160, 160, 160);
                border-radius: 5px;
                color: black;
                min-width: 78;
                min-height: 20;
            }
            QComboBox {
                background-color: rgb(255, 250, 250);
                border: 1px solid rgb(160, 160, 160);
                border-radius: 5px;
                color: rgb(30,30,30);
                min-width: 78;
                min-height: 20;
            }
            QPushButton:hover {
                background-color: rgb(185, 211, 238);
                border: 1px solid rgb(106, 178, 248);
                color: white;
            }
            QTextEdit{
                background-color: white;
                border: 1px solid rgb(160, 160, 160);
                border-radius: 5px;
            }
            """
        )
        self.setWindowOpacity(0.98)


    def onActivate(self,text):
        """
        功能描述：下拉表切换时，需要更改窗口上信息。会需要更改flag和备份之前窗口信息。
        """
        if text == "关键词":
            self._current_state = _INCLUDE_KEYWORDS
            self._word_insert_bk = self.word_insert.toPlainText()
            self.formatted_display(self._keywords)
        else:
            self._current_state = _EXCLUDE_KEYWORDS
            self._word_insert_bk = self.word_insert.toPlainText()
            self.formatted_display(self.exclude_words)

    def search(self):
        """
        功能描述：会检查一系列格式或未保存问题。然后会让用户读取一个文件夹
                 来寻找简历并导入文件名，之后通过接口计算排名后，显示到窗口
        异常描述：当关键词格式不正确，未导入，未保存； 屏蔽词未保存时，会弹窗并退出
        """
        if self._error_lines != []:
            self.warning("关键词格式没有全部正确，请修改！")
            return

        if self._keywords == "":
            self.warning("关键词未导入！")
            return

        if self._current_state == _INCLUDE_KEYWORDS:
            if self._keywords != self.formatting_keywords( \
                self.word_insert.toPlainText()):
                self.warning("关键词未保存！")
                return
            elif self.exclude_words != self.formatting_keywords( \
                self._word_insert_bk):
                self.warning("屏蔽词未保存！")
                return          
        elif self._current_state == _EXCLUDE_KEYWORDS:
            if self.exclude_words != self.formatting_keywords( \
                self.word_insert.toPlainText()):
                self.warning("屏蔽词未保存！")
                return
            elif self._keywords != self.formatting_keywords( \
                self._word_insert_bk):
                self.warning("关键词未保存！")
                return          

        # 重置result
        self._result_with = ""
        self._result_with_out = ""

        # 会去读取选择文件下的文件名
        filename_list = self.load_resumes()
        if len(filename_list) == 0:
            return

        # 简历得分算法
        result = compute.get_score(self.dict_keywords, \
            self.exclude_words.split("\n"), \
            self.filename_list, self.resume_dir)

        # 保存信息到string
        result_with = []
        result_with_out = []
        for member in result:
            if member[2] == 2:
                result_with.append(member[3] + "-" + str(member[0]) + ":" + \
                    str(member[1]))
            else:
                result_with_out.append(member[3] + "-" + str(member[0]) + \
                    ":" + str(member[1]))

        result_with = sorted(result_with)
        result_with_out = sorted(result_with_out)
        self.result_with = '\n'.join(result_with)
        self.result_with_out = '\n'.join(result_with_out)

        # 规范输出格式
        out_str=''
        for member in result:
            out_str += '序号：' + member[3] \
                    + '\t相关度：' + str(member[0]) \
                    + '\t软硬度：' + str(member[1]) \
                    + ('\t有排除词' if member[2] == 2 else '\t无排除词') + '\n'

        self.search_result.setText(out_str)
                
    def load_resumes(self):
        """
        功能描述：讲用户选择文件夹下的所有txt文件名储存到一个dict
        返回值：{"编号":["文件名1","文件名2"],...}格式的dict
        异常描述：当文件夹下无txt时会弹窗警告并退出
        """
        self.filename_list = {}
        cwd = os.getcwd()
        self.resume_dir = ''
        self.resume_dir = QFileDialog.getExistingDirectory(self, "选取文件夹", cwd)
        if len(self.resume_dir) == 0:
            self.warning("该目录下没有读取到可用txt文件，文件名为 数字 + _ + 内容！")
            return self.filename_list
        
        for file in os.listdir(self.resume_dir):
            if file.endswith(".txt"):
                index = file.split("_")[0]

                # 检查格式是否为 [数字 + _ + 内容]
                if not index.isdigit():
                    continue

                # 检查文件内是否带有input，output文件
                if "input" in file or "output" in file:
                    continue

                if index not in self.filename_list:
                    self.filename_list[index] = []
                self.filename_list[index].append(file)

        return self.filename_list

    def clear(self):
        """
        功能描述：清空文本框内所有文字，并初始化所有值
        """
        self._error_lines = []
        self._keywords = ""
        self.exclude_words = ""
        self._result_with = ""
        self._result_with_out = ""
        self.dict_keywords = {} 
        self.dict_exclude_words = {}
        self.search_result.setText("")
        self.word_insert.setText("")
        self._word_insert_bk = ""

    def formatted_display(self, words):
        """
        功能描述：会在显示文本时加上行号
        """
        display = ""
        words = words.split("\n")
        cnt = 0
        for word in words:
            if word == "":
                continue

            cnt += 1
            display = display + str(cnt) + '\t' + word + "\n"

        self.word_insert.setText(display)

    def load(self, words, label):
        """
        功能描述：选择文件并读取文件内容
        异常描述：当文件因编码问题无法读取时，会报错
                 当未选择文件就退出时，会弹窗并返回
        """
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setNameFilter("Text files (*.txt)")
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            f = open(filenames[0], 'r')
            with f:
                # 可能存在unicode编码错误
                try:
                   line = f.read()
                except UnicodeDecodeError:
                    self.warning("此文件有Unicode转码问题！")
                    return
                finally:
                    f.close()

                words = self.formatting_keywords(line)
            f.close()
        else:
            self.warning("导入失败！")
            return

        if label == _INCLUDE_KEYWORDS:
            if self.check_insert_label_format(words):
                self._keywords = words
        elif label == _EXCLUDE_KEYWORDS:
            words = self.remove_repeat(words)
            
            if self.check_exclude_word_len(words):
                self.exclude_words = words
                self.warning("屏蔽词导入成功！")

        self.formatted_display(words)

    def save(self, label):
        """
        功能描述：讲文本框内文字保存到对应函数（关键词 / 屏蔽词）
        """

        words = self.formatting_keywords(
                            self.word_insert.toPlainText())
        
        if label == _INCLUDE_KEYWORDS:
            if self.check_insert_label_format(words):
                self._keywords = words
        elif label == _EXCLUDE_KEYWORDS:
            words = self.remove_repeat(words)
            if self.check_exclude_word_len(words):
                self.exclude_words = words
                self.warning("屏蔽词保存成功！")

        print(repr(words))
        self.formatted_display(words)

    def check_exclude_word_len(self,input_val):
        """
        功能描述：确保文本长度小于30字
        """
        input_val = input_val.split("\n")
        for val in input_val:
            if len(val) > 30:
                self.warning("存在屏蔽词长度大30字符, 未保存！")
                return False
        return True

    def save_result(self):
        """
        功能描述：将文本框内内容保存到output1和output2
        异常描述：当未保存或输入文件就退出时，会弹窗并退出
        """
        with open("output2.txt","w") as f:
            f.write(self.formatting_keywords(self.result_with))

        with open("output1.txt","w") as f:
            f.write(self.formatting_keywords(self.result_with_out))

        self.warning("已将信息保存到当前文件夹下！")

    def save_text(self, text_name):
        """
        功能描述：将文本框内内容保存到本地
        异常描述：当未保存或输入文件就退出时，会弹窗并退出
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,
            "QFileDialog.getSaveFileName()","","Text Files (*.txt)",
            options=options)
        
        if fileName:
            # 当文件名不带 .txt 时，会补全
            if fileName[-4:] != ".txt":
                fileName += ".txt"

            with open(fileName,"w") as f:
                f.write(self.formatting_keywords(text_name.toPlainText()))
        else:
            self.warning("文件未保存！")

    def formatting_keywords(self,input_keywords):
        """
        功能描述：去掉多余空格，换行符和行尾换行符
        """
        input_keywords = re.sub(r'[ ]+','',input_keywords)
        input_keywords = re.sub(r'\n{2,}','\n',input_keywords)
        input_keywords = re.sub(r'\n$','',input_keywords)
        input_keywords = re.sub(r'^\n','',input_keywords)
        input_keywords = re.sub(r'\d+\t','',input_keywords)

        return input_keywords

    def remove_repeat(self, input_val):
        """
        功能描述：去除重复词
        """
        return '\n'.join(list(set(input_val.split("\n"))))

    def warning(self, text):
        """
        功能描述：弹窗（特定文字）
        """
        QMessageBox.warning(self,"Warning", text)

    def check_insert_label_format(self, keywords):
        """
        功能描述：会检查关键词格式是否正确，是否存在重复。如果都正确，
                 会将keyword的string保存为一个dict。
        返回值： bool
        异常描述：如果关键词格式不正确会弹窗并报错，会输出那几行错了。
                 如果关键词出现重复，会弹窗并报错，会输出重复的关键词。
        """
        keywords = keywords.split('\n')
        keyword_format = r'^\S+?\:[1-5]\:\-?[0-2]$'
        line_num = 0
        self._error_lines = []

        #if keywords

        # 检查关键词格式
        for line in keywords:
            line_num += 1
            if not re.match(keyword_format, line):
                self._error_lines.append(str(line_num))

        # 检查关键词是否重复
        if self._error_lines == []:
            if not self.no_repeat_keywords(keywords):
                self.dict_keywords = {}
            else:
                for line in keywords:
                    line = line.split(":")
                    self.dict_keywords[line[0]] = [int(line[1]),int(line[2])]
                self.warning("格式全部正确，可以开始搜索打分！")
                return True
        else:
            self.dict_keywords = {}
            error_message = "第" + "，".join(self._error_lines) + \
                "行的格式不匹配,请修改！\n\n" + \
                "**格式 -- 关键词:关键词权重(小 1~5 大):偏软件/偏硬件(软 -2~2 硬)"
            self.warning(error_message)
            return False

    def no_repeat_keywords(self, keywords):
        """
        功能描述：检查词是否出现重复
        返回值: bool
        异常描述：如果格式不正确会弹窗并告知具体重复单词
        """
        name_list = []
        repeat_list = []

        for line in keywords:
            line = line.split(":")[0]
            line = line.lower()
            if line not in name_list:
                name_list.append(line)
            elif line not in repeat_list:
                repeat_list.append(line)

        if len(repeat_list) == 0:
            return True
        else:
            self.warning("关键词<"+"><".join(repeat_list)+">出现重复")
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ResumeFilterGUI()
    sys.exit(app.exec_())
