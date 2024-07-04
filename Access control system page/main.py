import sys, login_rc, delete_rc, resource, search_rc, mysql.connector, pandas as pd, csv, cv2, shutil, os, openpyxl

from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSizePolicy, QDialog, QStackedWidget, QMessageBox, \
    QTableWidgetItem, QComboBox, QFileDialog, QLabel, QPushButton, QDateEdit, QHeaderView
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QLineSeries, QDateTimeAxis, \
    QValueAxis, QPieSeries, QCategoryAxis
from PyQt5.QtCore import Qt, QMetaObject, QPoint, QTimer, QDate, QDateTime
from PyQt5.QtGui import QPainter, QImage, QPixmap, QBrush, QPen, QPainterPath, QIcon
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from datetime import datetime, timedelta


class LoginWindow(QDialog):
    def __init__(self, widget):
        super(LoginWindow, self).__init__()
        loadUi("loginwindow.ui", self)
        self.widget = widget
        self.login_button.clicked.connect(self.gotomainwindow)
        # 当用户名或密码输入框的文本改变时，清除错误消息
        self.username_input.textChanged.connect(self.clearErrorMessage)
        self.password_input.textChanged.connect(self.clearErrorMessage)

    def gotomainwindow(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # 检查用户名和密码是否为空
        if not username or not password:
            self.error_message_label.setStyleSheet("color: red; border: none;")
            self.error_message_label.setText("用户名或密码为空")
            return

        # 连接到数据库
        cnx = mysql.connector.connect(user='root', password='123456',
                                      host='localhost',
                                      database='user_database')
        cursor = cnx.cursor()

        # 查询数据库
        query = ("SELECT account, password, name, email, phone_number FROM users "
                 "WHERE account = %s AND password = %s")
        cursor.execute(query, (username, password))

        # 检查查询结果
        user_data = cursor.fetchone()
        if user_data is not None:
            mainwindow = MainWindow(self.widget, user_data)
            self.widget.addWidget(mainwindow)
            self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        else:
            # 在 error_message_label 中显示错误消息
            self.error_message_label.setStyleSheet("color: red; border: none;")
            self.error_message_label.setText("用户名或密码错误")

        # 关闭连接
        cursor.close()
        cnx.close()

    def clearErrorMessage(self):
        self.error_message_label.setText("")  # 清除错误消息


class MainWindow(QDialog):
    def __init__(self, widget, user_data):
        super(MainWindow, self).__init__()
        loadUi("mainwindow.ui", self)
        self.widget = widget
        self.user_data = user_data  # 保存用户的信息
        self.dateEdit.setDate(QDate.currentDate())
        self.user_page_button.clicked.connect(self.gotouserpage)
        self.user_page_button_2.clicked.connect(self.gotouserpage)
        self.face_import_button.clicked.connect(self.gotofaceimport)
        self.admin_accounts_Button.clicked.connect(self.gotouserpage_4)
        self.home_page_button.clicked.connect(self.gotohomepage)
        self.management_button.clicked.connect(self.gotomanagementpage)
        self.users_page_button.clicked.connect(self.gotouserspage)
        self.users_page_button.clicked.connect(self.gotouserspage)
        self.report_page_button.clicked.connect(self.gotoreportpage)
        self.setting_button.clicked.connect(self.gotosettingpage)

        self.show_records_button.clicked.connect(self.gotoreportpage)
        self.today_count_button.clicked.connect(self.gotoreportpage)
        self.breach_event_button.clicked.connect(self.gotoreportpage_2)
        self.attendance_button.clicked.connect(self.gotoreportpage_3)
        self.visitors_button.clicked.connect(self.gotoreportpage_4)

        # 连接到数据库
        self.db_connection = self.connect_to_database()
        self.update_table()
        self.create_bar_chart()

    def connect_to_database(self):
        # 连接到数据库
        db_connection = mysql.connector.connect(
            host='localhost',
            database='user_database',
            user='root',
            password='123456'
        )
        return db_connection

    def update_table(self):
        cursor = self.db_connection.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        query = "SELECT name, type, pass_time FROM pass_users WHERE DATE(pass_time) = %s"
        cursor.execute(query, (today,))
        results = cursor.fetchall()

        row_count = len(results)
        self.tableWidget.setRowCount(row_count)  # 设置行数

        for i, (name, type, pass_time) in enumerate(results):
            row_index = row_count - 1 - i  # 从最后一行开始往上插入数据
            self.tableWidget.setItem(row_index, 0, QTableWidgetItem(name))
            self.tableWidget.setItem(row_index, 1, QTableWidgetItem(type))
            pass_time_str = datetime.strptime(pass_time, "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
            self.tableWidget.setItem(row_index, 2, QTableWidgetItem(pass_time_str))

        self.update_labels()

    def update_labels(self):
        cursor = self.db_connection.cursor()
        today = datetime.now().strftime('%Y-%m-%d')

        # 获取今天所有通过的人数
        query = "SELECT COUNT(*) FROM pass_users WHERE DATE(pass_time) = %s"
        cursor.execute(query, (today,))
        total_count = cursor.fetchone()[0]
        self.today_count_label.setText(str(total_count))

        # 获取今天通过的考勤人数
        query = "SELECT COUNT(DISTINCT student_id) FROM pass_users WHERE DATE(pass_time) = %s AND type = '学生'"
        cursor.execute(query, (today,))
        student_count = cursor.fetchone()[0]
        self.attendance_label.setText(str(student_count))

        # 获取今天通过的访客人数
        query = "SELECT COUNT(*) FROM pass_users WHERE DATE(pass_time) = %s AND type = '访客'"
        cursor.execute(query, (today,))
        visitor_count = cursor.fetchone()[0]
        self.visitors_label.setText(str(visitor_count))

        # 获取今天违规事件的数量
        query = "SELECT COUNT(*) FROM violation_events WHERE DATE(time) = %s"
        cursor.execute(query, (today,))
        total_breach_events = cursor.fetchone()[0]
        self.breach_event_label.setText(str(total_breach_events))

    def get_daily_pass_users(self):
        db_connection = self.connect_to_database()
        cursor = db_connection.cursor()

        # 计算最近五天的日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)

        # 执行查询获取最近五天每天的通过用户数量
        query = """
            SELECT DATE(pass_time), COUNT(*) 
            FROM pass_users 
            WHERE DATE(pass_time) BETWEEN %s AND %s
            GROUP BY DATE(pass_time)
        """
        cursor.execute(query, (start_date.date(), end_date.date()))
        daily_pass_users = cursor.fetchall()

        cursor.close()
        db_connection.close()

        # 创建一个字典，包含所有日期和对应的通过用户数量（如果没有用户通过，则为0）
        all_dates = {start_date.date() + timedelta(days=i): 0 for i in range(6)}
        for date, users in daily_pass_users:
            all_dates[date] = users

        return all_dates.items()

    def create_bar_chart(self):
        daily_pass_users = self.get_daily_pass_users()  # 获取最近五天的每天通过用户数量

        # 创建一个QBarSet对象来存储数据
        set0 = QBarSet('每日人数')
        for date, users in daily_pass_users:
            set0 << users

        # 创建一个QBarSeries对象并将QBarSet对象添加到其中
        series = QBarSeries()
        series.append(set0)

        # 创建一个QChart对象，将QBarSeries对象添加到其中，并设置一些属性
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle('每日人数统计')
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # 创建一个QBarCategoryAxis对象，设置其标签，并将其设置为图表的x轴
        axisX = QBarCategoryAxis()
        labels = [date.strftime("%m-%d") for date, users in daily_pass_users]
        axisX.append(labels)
        chart.setAxisX(axisX, series)

        # 创建一个QChartView对象，将QChart对象设置为其图表
        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        # 将QChartView对象添加到daily_headcounts_chart_widget中
        self.daily_headcounts_chart_widget.setLayout(QVBoxLayout())
        self.daily_headcounts_chart_widget.layout().addWidget(chartview)

    def gotohomepage(self):
        mainwindow = MainWindow(self.widget, self.user_data)
        self.widget.addWidget(mainwindow)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotomanagementpage(self):
        managementpage = ManagementPage(self.widget, self.user_data)
        self.widget.addWidget(managementpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserpage(self):
        userpage = UserPage(self.widget, self.user_data)
        self.widget.addWidget(userpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserspage(self):
        userspage = UsersPage(self.widget, self.user_data)
        self.widget.addWidget(userspage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotoreportpage(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotosettingpage(self):
        settingpage = SettingPage(self.widget, self.user_data)
        self.widget.addWidget(settingpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotofaceimport(self):
        faceimport = FaceImport(self.widget, self.user_data)
        self.widget.addWidget(faceimport)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotoreportpage_2(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        reportpage.stackedWidget.setCurrentWidget(reportpage.page_2)  # 将stackedWidget的当前页面设置为page_2

    def gotoreportpage_3(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        reportpage.stackedWidget.setCurrentWidget(reportpage.page_3)  # 将stackedWidget的当前页面设置为page_3

    def gotoreportpage_4(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        reportpage.stackedWidget.setCurrentWidget(reportpage.page_4)  # 将stackedWidget的当前页面设置为page_4

    def gotouserpage_4(self):
        userpage = UserPage(self.widget, self.user_data)
        self.widget.addWidget(userpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
        userpage.stackedWidget.setCurrentWidget(userpage.page_4)


class ManagementPage(QDialog):
    def __init__(self, widget, user_data):
        super(ManagementPage, self).__init__()
        loadUi("managementpage.ui", self)
        self.widget = widget
        self.user_data = user_data  # 保存用户的信息
        self.dateEdit.setDate(QDate.currentDate())
        self.user_page_button.clicked.connect(self.gotouserpage)
        self.user_page_button_2.clicked.connect(self.gotouserpage)
        self.home_page_button.clicked.connect(self.gotohomepage)
        self.users_page_button.clicked.connect(self.gotouserspage)
        self.report_page_button.clicked.connect(self.gotoreportpage)
        self.setting_button.clicked.connect(self.gotosettingpage)
        # 连接到数据库
        self.connect_to_database()
        self.setup_visitor_chart()
        self.setup_attendance_chart()
        self.create_violation_event_chart()

    def connect_to_database(self):
        # 连接到数据库
        db_connection = mysql.connector.connect(
            host='localhost',
            database='user_database',
            user='root',
            password='123456'
        )
        return db_connection

    def get_recent_attendance(self):
        db_connection = self.connect_to_database()
        cursor = db_connection.cursor()

        # 计算最近一天的日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=0)

        # 执行查询获取最近一天的到校学生人数
        query = """
            SELECT COUNT(DISTINCT student_id) 
            FROM pass_users 
            WHERE DATE(pass_time) BETWEEN %s AND %s
            AND type = '学生'  -- 仅统计通过的学生用户
        """
        cursor.execute(query, (start_date.date(), end_date.date()))
        arrived_count = cursor.fetchone()[0]

        # 执行查询获取所有学生用户的数量
        query = """
            SELECT COUNT(*) 
            FROM user_data
            WHERE type = '学生'  -- 仅统计学生用户
        """
        cursor.execute(query)
        total_count = cursor.fetchone()[0]

        cursor.close()
        db_connection.close()

        return arrived_count, total_count

    def setup_attendance_chart(self):
        # 获取最近一天的到校人数和所有用户的数量
        arrived_count, total_count = self.get_recent_attendance()

        # 计算未到校人数
        not_arrived_count = total_count - arrived_count

        # 计算统计日期
        stat_date = (datetime.now() - timedelta(days=0)).strftime("%Y-%m-%d")

        # 创建一个饼图系列
        series = QPieSeries()
        series.append("已到人数", arrived_count)
        series.append("未到人数", not_arrived_count)

        # 创建一个图表并将系列添加到其中
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"考勤统计 ({stat_date})")  # 包含统计日期

        # 创建一个带有图表的图表视图，并将其添加到部件
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        # 添加一个标签来显示已到人数
        arrived_label = QLabel(f"已到人数：{arrived_count}")
        arrived_label.setAlignment(Qt.AlignCenter)

        # 将图表视图和标签添加到attendance_chart_Widget
        layout = QVBoxLayout(self.attendance_chart_Widget)
        layout.addWidget(chart_view)
        layout.addWidget(arrived_label)

    def get_recent_visitors(self):
        db_connection = self.connect_to_database()
        cursor = db_connection.cursor()

        # 计算最近五天的日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=4)

        # 执行查询获取最近五天每天的访客数量，仅统计类型为"访客"的记录
        query = """
            SELECT DATE(pass_time), COUNT(*) 
            FROM pass_users 
            WHERE DATE(pass_time) BETWEEN %s AND %s
            AND type = '访客'  -- 仅统计类型为"访客"的记录
            GROUP BY DATE(pass_time)
        """
        cursor.execute(query, (start_date.date(), end_date.date()))
        recent_visitors = cursor.fetchall()

        cursor.close()
        db_connection.close()

        # 创建一个字典，包含所有日期和对应的访客数量（如果没有访客，则为0）
        all_dates = {start_date.date() + timedelta(days=i): 0 for i in range(5)}
        for date, visitors in recent_visitors:
            all_dates[date] = visitors

        return all_dates.items()

    def setup_visitor_chart(self):
        series = QLineSeries()
        visitor_data = self.get_recent_visitors()

        for date, visitors in visitor_data:
            # 将日期转换为 QDateTime
            dt = QDateTime(date)
            # 使用 QDateTime 作为横坐标
            series.append(dt.toMSecsSinceEpoch(), visitors)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("最近五天访客统计")

        # 创建横坐标轴，并设置日期格式
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MM-dd")  # 设置日期格式为月-日
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        # 创建纵坐标轴，并设置范围为从零开始的整数
        axis_y = QValueAxis()
        axis_y.setRange(0, max([visitors for _, visitors in visitor_data]) + 1)  # 设置纵坐标轴范围
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        layout = QVBoxLayout(self.visitor_chart_Widget)
        layout.addWidget(chart_view)

    def get_recent_violation_events(self):
        db_connection = self.connect_to_database()
        cursor = db_connection.cursor()

        # 计算最近十天的日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)

        # 执行查询获取最近十天每天的违规事件数量
        query = """
            SELECT DATE(time), COUNT(*) 
            FROM violation_events 
            WHERE DATE(time) BETWEEN %s AND %s
            GROUP BY DATE(time)
        """
        cursor.execute(query, (start_date.date(), end_date.date()))
        recent_violations = cursor.fetchall()

        cursor.close()
        db_connection.close()

        # 创建一个字典，包含所有日期和对应的违规事件数量（如果没有违规事件，则为0）
        all_dates = {start_date.date() + timedelta(days=i): 0 for i in range(11)}
        for date, violations in recent_violations:
            all_dates[date] = violations

        return all_dates.items()

    def create_violation_event_chart(self):
        violation_counts = self.get_recent_violation_events()  # 获取最近十天的每天违规事件数量
        set0 = QBarSet('违规事件数量')  # 创建一个QBarSet对象来存储数据

        # 将日期和对应的违规事件数量添加到QBarSet对象中
        for date, count in violation_counts:
            set0.append(count)

        # 创建一个QBarSeries对象并将QBarSet对象添加到其中
        series = QBarSeries()
        series.append(set0)

        # 创建一个QChart对象，将QBarSeries对象添加到其中，并设置一些属性
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle('违规事件统计')
        chart.setAnimationOptions(QChart.SeriesAnimations)

        # 创建一个QBarCategoryAxis对象，设置其标签，并将其设置为图表的x轴
        axisX = QBarCategoryAxis()
        # 获取最近十天的日期，并转换为字符串格式的日期
        labels = [date.strftime("%m-%d") for date, count in violation_counts]
        axisX.append(labels)
        chart.setAxisX(axisX, series)

        # 将条形的数值显示在上方
        chart.setAxisY(QValueAxis(), series)  # 设置y轴
        chart.axisY(series).setLabelsVisible(True)  # 显示y轴标签

        # 创建一个QChartView对象，将QChart对象设置为其图表
        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        # 将QChartView对象添加到bar_chart_widget中
        self.violation_event_chart_Widget.setLayout(QVBoxLayout())
        self.violation_event_chart_Widget.layout().addWidget(chartview)

    def gotohomepage(self):
        mainwindow = MainWindow(self.widget, self.user_data)
        self.widget.addWidget(mainwindow)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserpage(self):
        userpage = UserPage(self.widget, self.user_data)
        self.widget.addWidget(userpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserspage(self):
        userspage = UsersPage(self.widget, self.user_data)
        self.widget.addWidget(userspage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotoreportpage(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotosettingpage(self):
        settingpage = SettingPage(self.widget, self.user_data)
        self.widget.addWidget(settingpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)


class UsersPage(QDialog):
    def __init__(self, widget, user_data):
        super(UsersPage, self).__init__()
        loadUi("userspage.ui", self)
        self.widget = widget
        self.user_data = user_data  # 保存用户的信息
        self.dateEdit.setDate(QDate.currentDate())
        self.user_page_button.clicked.connect(self.gotouserpage)
        self.user_page_button_2.clicked.connect(self.gotouserpage)
        self.home_page_button.clicked.connect(self.gotohomepage)
        self.management_button.clicked.connect(self.gotomanagementpage)
        self.report_page_button.clicked.connect(self.gotoreportpage)
        self.setting_button.clicked.connect(self.gotosettingpage)
        self.export_button.clicked.connect(self.export_table)
        self.add_button.clicked.connect(self.gotofaceimport)
        self.delete_button.clicked.connect(self.gotousersdeletewindow)

        # 连接user_type_comboBox的值改变事件到我们的处理函数
        self.user_type_comboBox.currentIndexChanged.connect(self.update_table)

        self.search_Button.clicked.connect(self.search_student)
        self.search_lineEdit.returnPressed.connect(self.search_student)

        self.update_table()

        column_widths = [1, 100, 50, 100, 80, 200, 80, 150, 150, 80, 80]  # 列宽度列表，索引对应列号
        for column, width in enumerate(column_widths):
            self.tableWidget.setColumnWidth(column, width)

    def update_table(self):
        user_type = self.user_type_comboBox.currentText()
        query = self.construct_query(user_type)

        try:
            cnx, cursor = self.connect_to_database()

            cursor.execute(query)
            rows = cursor.fetchall()

            if rows:
                self.initialize_table(rows)
            else:
                QMessageBox.information(self, "提示", "没有可用的数据")

        except Exception as e:
            print("An error occurred:", e)
        finally:
            self.close_database_connection(cnx, cursor)

    def export_table(self):
        # 获取用户选择的文件名和文件类型
        fileName, _ = QFileDialog.getSaveFileName(self, "导出到CSV", "", "CSV Files (*.csv)")

        if fileName:
            with open(fileName, 'w', newline='', encoding='utf_8_sig') as file:
                writer = csv.writer(file)
                header = []
                for i in range(self.tableWidget.columnCount()):
                    header.append(self.tableWidget.horizontalHeaderItem(i).text())
                writer.writerow(header)
                for row in range(self.tableWidget.rowCount()):
                    rowdata = []
                    for column in range(self.tableWidget.columnCount()):
                        item = self.tableWidget.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)

    def search_student(self):
        search_text = self.search_lineEdit.text()

        if search_text:  # 如果搜索框不为空
            query = ("SELECT name, gender, student_id, type, email, team, phone, college, grade, inviter "
                     "FROM user_data "
                     "WHERE student_id = %s OR name LIKE %s")
            params = (search_text, '%' + search_text + '%')
        else:
            query = "SELECT name, gender, student_id, type, email, team, phone, college, grade, inviter FROM user_data"
            params = None

        try:
            cnx, cursor = self.connect_to_database()

            cursor.execute(query, params)
            rows = cursor.fetchall()

            if rows:
                self.initialize_table(rows)
            else:
                QMessageBox.information(self, "提示", f"没有找到与'{search_text}'相关的用户信息" if search_text else "数据库中没有用户信息")

        except Exception as e:
            print("An error occurred:", e)
        finally:
            self.close_database_connection(cnx, cursor)

    def construct_query(self, user_type):
        if user_type == '全部':
            return "SELECT name, gender, student_id, type, email, team, phone, college, grade, inviter FROM user_data"
        else:
            return f"SELECT name, gender, student_id, type, email, team, phone, college, grade, inviter FROM user_data WHERE type = '{user_type}'"

    def connect_to_database(self):
        cnx = mysql.connector.connect(user='root', password='123456',
                                      host='localhost',
                                      database='user_database')
        cursor = cnx.cursor()
        return cnx, cursor

    def close_database_connection(self, cnx, cursor):
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()

    def initialize_table(self, rows):
        self.tableWidget.setRowCount(len(rows))
        self.tableWidget.setColumnCount(len(rows[0]) + 1)  # 添加一个新的列来存放选中框
        self.tableWidget.setHorizontalHeaderLabels(
            ['', '姓名', '性别', '学号', '类型', '邮箱', '团队', '手机', '学院', '年级', '邀请人'])

        for i, row in enumerate(rows):
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            self.tableWidget.setItem(i, 0, checkbox)  # 在新的列中添加选中框

            for j, value in enumerate(row):
                self.tableWidget.setItem(i, j + 1, QTableWidgetItem(str(value)))  # 注意这里的列索引需要加1

    def gotohomepage(self):
        mainwindow = MainWindow(self.widget, self.user_data)
        self.widget.addWidget(mainwindow)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotomanagementpage(self):
        managementpage = ManagementPage(self.widget, self.user_data)
        self.widget.addWidget(managementpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserpage(self):
        userpage = UserPage(self.widget, self.user_data)
        self.widget.addWidget(userpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotofaceimport(self):
        faceimport = FaceImport(self.widget, self.user_data)
        self.widget.addWidget(faceimport)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotoreportpage(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotousersdeletewindow(self):
        self.usersdeletewindow = UsersDeleteWindow(self.widget, self)
        self.usersdeletewindow.show()

    def gotosettingpage(self):
        settingpage = SettingPage(self.widget, self.user_data)
        self.widget.addWidget(settingpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def get_selected_rows(self):
        # 获取选中的行
        selected_rows = []
        for i in range(self.tableWidget.rowCount()):
            checkbox = self.tableWidget.item(i, 0)
            if checkbox.checkState() == Qt.Checked:
                selected_rows.append(i)
        return selected_rows


class ReportTables(QDialog):
    def __init__(self, widget, user_data):
        super(ReportTables, self).__init__()
        loadUi("reporttables.ui", self)
        self.widget = widget
        self.user_data = user_data  # 保存用户的信息
        self.dateEdit.setDate(QDate.currentDate())
        self.user_page_button.clicked.connect(self.gotouserpage)
        self.user_page_button_2.clicked.connect(self.gotouserpage)
        self.home_page_button.clicked.connect(self.gotohomepage)
        self.management_button.clicked.connect(self.gotomanagementpage)
        self.users_page_button.clicked.connect(self.gotouserspage)
        self.setting_button.clicked.connect(self.gotosettingpage)
        today_count_buttons = [self.today_count_button, self.today_count_button_2, self.today_count_button_3,
                               self.today_count_button_4]
        breach_event_buttons = [self.breach_event_button, self.breach_event_button_2, self.breach_event_button_3,
                                self.breach_event_button_4]
        attendance_buttons = [self.attendance_button, self.attendance_button_2, self.attendance_button_3,
                              self.attendance_button_4]
        visitors_buttons = [self.visitors_button, self.visitors_button_2, self.visitors_button_3,
                            self.visitors_button_4]
        for today_count_button in today_count_buttons:
            today_count_button.clicked.connect(self.goto_page)

        for breach_event_button in breach_event_buttons:
            breach_event_button.clicked.connect(self.goto_page_2)

        for attendance_button in attendance_buttons:
            attendance_button.clicked.connect(self.goto_page_3)

        for visitors_button in visitors_buttons:
            visitors_button.clicked.connect(self.goto_page_4)

        # 将导出按钮连接到导出方法
        self.export_button.clicked.connect(self.export_table)
        self.export_button_2.clicked.connect(self.export_table_2)
        self.export_button_3.clicked.connect(self.export_table_3)
        self.export_button_4.clicked.connect(self.export_table_4)

        self.conn = None
        self.cursor = None
        self.load_data()

    def export_table(self):
        self.export_table_to_excel(self.tableWidget)

    def export_table_2(self):
        self.export_table_to_excel(self.tableWidget_2)

    def export_table_3(self):
        self.export_table_to_excel(self.tableWidget_3)

    def export_table_4(self):
        self.export_table_to_excel(self.tableWidget_4)

    def export_table_to_excel(self, table_widget):
        # 获取用户选择的文件名和文件类型
        fileName, _ = QFileDialog.getSaveFileName(self, "导出到Excel", "", "Excel Files (*.xlsx)")

        if fileName:
            workbook = openpyxl.Workbook()
            sheet = workbook.active

            # 写入表头
            for col in range(1, table_widget.columnCount() + 1):
                sheet.cell(row=1, column=col, value=table_widget.horizontalHeaderItem(col - 1).text())

            # 写入表格内容
            for row in range(table_widget.rowCount()):
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    if item is not None:
                        sheet.cell(row=row + 2, column=col + 1, value=item.text())
                    else:
                        sheet.cell(row=row + 2, column=col + 1, value='')

            # 保存 Excel 文件
            workbook.save(fileName)

    def connect_to_database(self):
        # 连接到数据库
        db_connection = mysql.connector.connect(
            host='localhost',
            database='user_database',
            user='root',
            password='123456'
        )
        return db_connection

    def load_data(self):
        # 如果数据库连接为空，建立连接
        if self.conn is None:
            self.conn = self.connect_to_database()  # 连接数据库
            self.cursor = self.conn.cursor()  # 创建游标

        # 修改加载 pass_users 数据的部分
        query = "SELECT pass_time, leave_time, stay_time, name, gender, student_id, type, email, team, phone, college, grade, inviter FROM pass_users ORDER BY pass_time DESC"
        self.cursor.execute(query)
        data = self.cursor.fetchall()  # 获取查询结果

        # 将查询结果加载到表格中
        self.tableWidget.setRowCount(len(data))  # 设置表格行数
        for row_index, row_data in enumerate(data):
            for col_index, col_data in enumerate(row_data):
                if col_data is None and (col_index == 1 or col_index == 2):  # 检查 leave_time 和 stay_time 是否为 None
                    col_data = "未离开"  # 设置默认值为 "未离开"
                item = QTableWidgetItem(str(col_data))  # 将数据转换为字符串，并创建表格项
                self.tableWidget.setItem(row_index, col_index, item)  # 设置表格项

        # 查询数据库中的数据
        query = "SELECT time, picture_path FROM violation_events"
        self.cursor.execute(query)
        data = self.cursor.fetchall()  # 获取查询结果

        # 将查询结果加载到表格中
        self.tableWidget_2.setRowCount(len(data))  # 设置表格行数
        for row_index, row_data in enumerate(data):
            time, picture_path = row_data
            item = QTableWidgetItem()
            pixmap = QPixmap(picture_path)
            # 缩放图片以适应表格大小
            scaled_pixmap = pixmap.scaled(240, 180, Qt.KeepAspectRatio)
            item.setData(Qt.DecorationRole, scaled_pixmap)
            # 在表格中设置时间和图片
            self.tableWidget_2.setItem(row_index, 0, item)
            self.tableWidget_2.setItem(row_index, 1, QTableWidgetItem(time))

        # 进行排序，按时间排序
        self.tableWidget_2.sortItems(1, Qt.DescendingOrder)

        # 查询数据库中的数据，选取type为学生的记录
        query_student = "SELECT pass_time, leave_time, stay_time, name, inviter, gender, student_id, type, email, team, phone, college, grade FROM pass_users WHERE type = '学生' ORDER BY pass_time DESC"
        self.cursor.execute(query_student)
        data_student = self.cursor.fetchall()  # 获取查询结果

        # 将查询结果加载到表格中
        self.tableWidget_3.setRowCount(len(data_student))  # 设置表格行数
        for row_index, row_data in enumerate(data_student):
            for col_index, col_data in enumerate(row_data):
                if col_data is None and (col_index == 1 or col_index == 2):  # 检查 leave_time 和 stay_time 是否为 None
                    col_data = "未离开"  # 设置默认值为 "未离开"
                item = QTableWidgetItem(str(col_data))  # 将数据转换为字符串，并创建表格项
                self.tableWidget_3.setItem(row_index, col_index, item)  # 设置表格项

        # 查询数据库中的数据，选取type为访客的记录
        query_guest = "SELECT pass_time, leave_time, stay_time, name, inviter, gender, student_id, type, email, team, phone, college, grade FROM pass_users WHERE type = '访客' ORDER BY pass_time DESC"
        self.cursor.execute(query_guest)
        data_guest = self.cursor.fetchall()  # 获取查询结果

        # 将查询结果加载到表格中
        self.tableWidget_4.setRowCount(len(data_guest))  # 设置表格行数
        for row_index, row_data in enumerate(data_guest):
            for col_index, col_data in enumerate(row_data):
                if col_data is None and (col_index == 1 or col_index == 2):  # 检查 leave_time 和 stay_time 是否为 None
                    col_data = "未离开"  # 设置默认值为 "未离开"
                item = QTableWidgetItem(str(col_data))  # 将数据转换为字符串，并创建表格项
                self.tableWidget_4.setItem(row_index, col_index, item)  # 设置表格项

        # 启用表头排序
        self.tableWidget_2.horizontalHeader().setSectionsClickable(True)
        self.tableWidget_2.horizontalHeader().sectionClicked.connect(self.sort_table_by_time)

    def sort_table_by_time(self, logical_index):
        current_order = self.tableWidget_2.horizontalHeader().sortIndicatorOrder()  # 获取当前排序状态
        self.tableWidget_2.sortItems(logical_index, current_order)  # 执行排序操作

    def gotohomepage(self):
        mainwindow = MainWindow(self.widget, self.user_data)
        self.widget.addWidget(mainwindow)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserpage(self):
        userpage = UserPage(self.widget, self.user_data)
        self.widget.addWidget(userpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserspage(self):
        userspage = UsersPage(self.widget, self.user_data)
        self.widget.addWidget(userspage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotomanagementpage(self):
        managementpage = ManagementPage(self.widget, self.user_data)
        self.widget.addWidget(managementpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotosettingpage(self):
        settingpage = SettingPage(self.widget, self.user_data)
        self.widget.addWidget(settingpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def goto_page(self):
        self.stackedWidget.setCurrentIndex(0)

    def goto_page_2(self):
        self.stackedWidget.setCurrentIndex(1)

    def goto_page_3(self):
        self.stackedWidget.setCurrentIndex(2)

    def goto_page_4(self):
        self.stackedWidget.setCurrentIndex(3)


class SettingPage(QDialog):
    def __init__(self, widget, user_data):
        super(SettingPage, self).__init__()
        loadUi("settingpage.ui", self)
        self.widget = widget
        self.user_data = user_data  # 保存用户的信息
        self.user_page_button.clicked.connect(self.gotouserpage)
        self.user_page_button_2.clicked.connect(self.gotouserpage)
        self.home_page_button.clicked.connect(self.gotohomepage)
        self.management_button.clicked.connect(self.gotomanagementpage)
        self.report_page_button.clicked.connect(self.gotoreportpage)
        self.users_page_button.clicked.connect(self.gotouserspage)

    def gotohomepage(self):
        mainwindow = MainWindow(self.widget, self.user_data)
        self.widget.addWidget(mainwindow)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserpage(self):
        userpage = UserPage(self.widget, self.user_data)
        self.widget.addWidget(userpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserspage(self):
        userspage = UsersPage(self.widget, self.user_data)
        self.widget.addWidget(userspage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotomanagementpage(self):
        managementpage = ManagementPage(self.widget, self.user_data)
        self.widget.addWidget(managementpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotoreportpage(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)


class UserPage(QDialog):
    def __init__(self, widget, user_data):
        super(UserPage, self).__init__()
        loadUi("userepage.ui", self)
        self.widget = widget
        self.user_data = user_data  # 保存用户的信息
        self.dateEdit.setDate(QDate.currentDate())
        self.user_page_button.clicked.connect(self.gotouserpage)
        self.user_page_button_2.clicked.connect(self.gotouserpage)
        self.home_page_button.clicked.connect(self.gotohomepage)
        self.management_button.clicked.connect(self.gotomanagementpage)
        self.users_page_button.clicked.connect(self.gotouserspage)
        self.setting_button.clicked.connect(self.gotosettingpage)
        self.report_page_button.clicked.connect(self.gotoreportpage)
        self.change_password_Button.clicked.connect(self.goto_page_2)
        self.add_account_Button.clicked.connect(self.goto_page_3)
        self.admin_accounts_Button.clicked.connect(self.goto_page_4)
        self.confirm_Button_2.clicked.connect(self.save_to_database)
        self.change_password_Button_2.clicked.connect(self.change_password)
        self.confirm_Button.clicked.connect(self.update_user_info)

        self.modify_name_Button.clicked.connect(self.enable_name_edit)
        self.modify_email_Button.clicked.connect(self.enable_email_edit)
        self.modify_phone_number_Button.clicked.connect(self.enable_phone_number_edit)

        self.current_password_lineEdit.textChanged.connect(self.clearErrorMessage_2)
        self.new_password_lineEdit.textChanged.connect(self.clearErrorMessage_3)
        self.confirm_new_password_lineEdit.textChanged.connect(self.clearErrorMessage_3)

        self.load_user_data()
        self.load_all_user_data()

        # 在tableWidget的第五列添加按钮
        self.add_button_to_table()

    def gotohomepage(self):
        mainwindow = MainWindow(self.widget, self.user_data)
        self.widget.addWidget(mainwindow)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotomanagementpage(self):
        managementpage = ManagementPage(self.widget, self.user_data)
        self.widget.addWidget(managementpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserpage(self):
        userpage = UserPage(self.widget, self.user_data)
        self.widget.addWidget(userpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserspage(self):
        userspage = UsersPage(self.widget, self.user_data)
        self.widget.addWidget(userspage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotoreportpage(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotosettingpage(self):
        settingpage = SettingPage(self.widget, self.user_data)
        self.widget.addWidget(settingpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def load_user_data(self):
        cnx = None
        cursor = None
        try:
            cnx = mysql.connector.connect(user='root', password='123456',
                                          host='localhost',
                                          database='user_database')
            cursor = cnx.cursor()

            # 从数据库中获取用户信息
            query = "SELECT account, password, name, email, phone_number FROM users WHERE account = %s"
            cursor.execute(query, (self.user_data[0],))
            user_info = cursor.fetchone()

            if user_info:
                account, password, name, email, phone_number = user_info
                self.modify_name_lineEdit.setText(name)
                self.modify_email_lineEdit.setText(email)
                self.modify_phone_number_lineEdit.setText(phone_number)
                self.current_account_label.setText(account)
                self.user_name_label.setText(name)
                self.user_name_label_2.setText(name)
                self.user_name_label_3.setText(name)
                self.email_label.setText(email)
                self.email_label_2.setText(email)
                self.email_label_3.setText(email)
            else:
                print("User data not found.")
        except mysql.connector.Error as err:
            print("MySQL Error:", err)
        finally:
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()

    def update_user_info(self):
        # 获取修改后的姓名、邮箱和手机号码
        name = self.modify_name_lineEdit.text()
        email = self.modify_email_lineEdit.text()
        phone_number = self.modify_phone_number_lineEdit.text()

        # 连接到数据库
        try:
            cnx = mysql.connector.connect(user='root', password='123456',
                                          host='localhost',
                                          database='user_database')
            cursor = cnx.cursor()

            # 更新用户信息
            account, _, _, _, _ = self.user_data
            update_query = "UPDATE users SET name = %s, email = %s, phone_number = %s WHERE account = %s"
            cursor.execute(update_query, (name, email, phone_number, account))
            cnx.commit()
        except mysql.connector.Error as err:
            print("MySQL错误：", err)
        finally:
            # 关闭连接
            try:
                cursor.close()
            except NameError:
                pass
            try:
                cnx.close()
            except NameError:
                pass

    def change_password(self):
        # 获取当前密码、新密码和确认新密码
        current_password = self.current_password_lineEdit.text()
        new_password = self.new_password_lineEdit.text()
        confirm_new_password = self.confirm_new_password_lineEdit.text()

        # 验证新密码
        if new_password != confirm_new_password:
            self.error_message_label_3.setText("两次密码输入不一致")
            return

        # 连接到数据库
        try:
            cnx = mysql.connector.connect(user='root', password='123456',
                                          host='localhost',
                                          database='user_database')
            cursor = cnx.cursor()

            # 检查当前密码是否正确
            account, current_db_password, _, _, _ = self.user_data
            query = "SELECT password FROM users WHERE account = %s"
            cursor.execute(query, (account,))
            result = cursor.fetchone()
            if result and result[0] == current_password:
                # 更新密码
                update_query = "UPDATE users SET password = %s WHERE account = %s"
                cursor.execute(update_query, (new_password, account))
                cnx.commit()
                self.error_message_label_4.setText("密码修改成功")
            else:
                self.error_message_label_2.setText("当前密码不正确")
        except mysql.connector.Error as err:
            print("MySQL错误：", err)
        finally:
            # 关闭连接
            try:
                cursor.close()
            except NameError:
                pass
            try:
                cnx.close()
            except NameError:
                pass

    def clearErrorMessage_2(self):
        self.error_message_label_2.setText("")  # 清除错误消息
        self.error_message_label_4.setText("")  # 清除错误消息

    def clearErrorMessage_3(self):
        self.error_message_label_3.setText("")  # 清除错误消息
        self.error_message_label_4.setText("")  # 清除错误消息

    #page_3
    def save_to_database(self):
        try:
            account = self.account_lineEdit.text()
            password = self.password_lineEdit.text()
            confirm_password = self.confirm_password_lineEdit.text()
            name = self.name_lineEdit.text()
            email = self.email_lineEdit.text()
            phone_number = self.phone_number_lineEdit.text()

            # 检查密码是否相同
            if password == confirm_password:
                # 连接到数据库
                cnx = mysql.connector.connect(user='root', password='123456',
                                              host='localhost',
                                              database='user_database')
                cursor = cnx.cursor()

                # 插入数据到user_data表
                query = ("INSERT INTO users "
                         "(account, password, name, email, phone_number) "
                         "VALUES (%s, %s, %s, %s, %s)")
                cursor.execute(query, (account, password, name, email, phone_number))

                # 提交事务
                cnx.commit()
            else:
                self.error_message_label.setText("两次密码不一致")
                print("Passwords do not match. Database not updated.")

        except mysql.connector.Error as err:
            print("MySQL Error:", err)
        finally:
        # 关闭连接
            try:
                cursor.close()
            except NameError:
                pass
            try:
                cnx.close()
            except NameError:
                pass
    #page_4
    def add_button_to_table(self):
        num_rows = self.tableWidget.rowCount()
        for row in range(num_rows):
            button = QPushButton('删除')
            button.clicked.connect(self.handleButtonClicked)
            self.tableWidget.setCellWidget(row, 4, button)  # 在第五列（索引为4）添加按钮

    def handleButtonClicked(self):
        button = self.sender()
        index = self.tableWidget.indexAt(button.pos())

        if index.isValid():
            row = index.row()
            name = self.tableWidget.item(row, 0).text()  # 获取要删除的管理员姓名

            # 显示提示窗口，询问是否删除管理员信息
            reply = QMessageBox.question(self, '删除管理员信息', f"确认删除管理员 {name} 的信息吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                # 用户选择确认删除，执行删除操作
                self.delete_administrator(row)

    def delete_administrator(self, row):
        # 获取要删除的管理员姓名
        name = self.tableWidget.item(row, 0).text()

        # 连接到数据库
        try:
            cnx = mysql.connector.connect(user='root', password='123456',
                                          host='localhost',
                                          database='user_database')
            cursor = cnx.cursor()

            # 根据管理员姓名删除管理员信息
            delete_query = "DELETE FROM users WHERE name = %s"
            cursor.execute(delete_query, (name,))
            cnx.commit()

            # 从表格中删除对应行
            self.tableWidget.removeRow(row)

        except mysql.connector.Error as err:
            print("MySQL错误：", err)
        finally:
            # 关闭连接
            try:
                cursor.close()
            except NameError:
                pass
            try:
                cnx.close()
            except NameError:
                pass

    def load_all_user_data(self):
        cnx = None
        cursor = None
        try:
            cnx = mysql.connector.connect(user='root', password='123456',
                                          host='localhost',
                                          database='user_database')
            cursor = cnx.cursor()

            # 从数据库中获取所有用户信息
            query = "SELECT account, password, name, email, phone_number FROM users"
            cursor.execute(query)
            all_user_info = cursor.fetchall()

            if all_user_info:
                for row_number, user_info in enumerate(all_user_info):
                    account, password, name, email, phone_number = user_info
                    self.tableWidget.insertRow(row_number)
                    self.tableWidget.setItem(row_number, 0, QTableWidgetItem(name))
                    self.tableWidget.setItem(row_number, 1, QTableWidgetItem(email))
                    self.tableWidget.setItem(row_number, 2, QTableWidgetItem(phone_number))
                    self.tableWidget.setItem(row_number, 3, QTableWidgetItem(account))
                    button = QPushButton('删除')
                    button.clicked.connect(self.handleButtonClicked)
                    self.tableWidget.setCellWidget(row_number, 4, button)  # 在第五列（索引为4）添加按钮
        except mysql.connector.Error as err:
            print("MySQL Error:", err)
        finally:
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()

    def goto_page_2(self):
        self.stackedWidget.setCurrentIndex(1)

    def goto_page_3(self):
        self.stackedWidget.setCurrentIndex(2)

    def goto_page_4(self):
        self.stackedWidget.setCurrentIndex(3)

    def enable_name_edit(self):
        self.modify_name_lineEdit.setReadOnly(False)
        self.modify_name_lineEdit.setFocus()

    def enable_email_edit(self):
        self.modify_email_lineEdit.setReadOnly(False)
        self.modify_email_lineEdit.setFocus()

    def enable_phone_number_edit(self):
        self.modify_phone_number_lineEdit.setReadOnly(False)
        self.modify_phone_number_lineEdit.setFocus()


class UsersDeleteWindow(QDialog):
    def __init__(self, widget, parent):
        super(UsersDeleteWindow, self).__init__()
        loadUi("usersdeletewindow.ui", self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # 设置无边框和置顶
        self.setModal(True)  # 设置为模态窗口，防止点击其他窗口
        self.widget = widget
        self.parent = parent  # 添加对父窗口的引用

        self.draggable = True
        self.offset = QPoint()

        # 连接按钮点击事件到关闭窗口的方法
        self.close_button.clicked.connect(self.close_window)
        self.cancel_button.clicked.connect(self.close_window)
        self.confirm_button.clicked.connect(self.delete_selected_rows)  # 连接confirm_button的点击事件到delete_selected_rows方法

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.draggable:
            self.offset = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.draggable:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = QPoint()

    def close_window(self):
        self.close()

    def delete_selected_rows(self):
        # 获取选中的行
        selected_rows = self.parent.get_selected_rows()

        try:
            # 连接到数据库
            cnx = mysql.connector.connect(user='root', password='123456',
                                          host='localhost',
                                          database='user_database')
            cursor = cnx.cursor()

            # 从数据库中删除选中的行
            for row in selected_rows:
                student_id_item = self.parent.tableWidget.item(row, 3)  # 获取学号项
                name_item = self.parent.tableWidget.item(row, 1)  # 获取姓名项
                type_item = self.parent.tableWidget.item(row, 4)  # 获取类型项
                inviter_item = self.parent.tableWidget.item(row, 10)  # 获取邀请人项
                if student_id_item is not None and name_item is not None:
                    student_id = student_id_item.text()  # 获取学号文本
                    name = name_item.text()  # 获取姓名文本
                    type = type_item.text() if type_item else ""  # 获取类型文本
                    inviter = inviter_item.text() if inviter_item else ""  # 获取邀请人文本

                    # 构建头像文件路径
                    avatar_filename = f"{name}_{student_id}.jpg"
                    current_dir = os.getcwd()
                    avatar_path = os.path.join(current_dir, "avatars", avatar_filename)

                    # 删除头像文件
                    if os.path.exists(avatar_path):
                        os.remove(avatar_path)

                    # 删除数据库中的用户信息
                    query = "DELETE FROM user_data WHERE student_id = %s"
                    cursor.execute(query, (student_id,))  # 执行删除查询
                    print(f"Deleted user: {name}, ID: {student_id}, Avatar: {avatar_filename}")

            # 提交更改
            cnx.commit()
        except Exception as e:
            print("An error occurred:", e)
        finally:
            # 关闭游标和数据库连接
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()

            # 更新父窗口的表格
            self.parent.update_table()

            # 关闭删除窗口
            self.close()


class FaceImport(QDialog):
    def __init__(self, widget, user_data):
        super(FaceImport, self).__init__()
        loadUi("faceimport.ui", self)
        self.widget = widget
        self.user_data = user_data  # 保存用户的信息
        self.dateEdit.setDate(QDate.currentDate())
        self.user_page_button.clicked.connect(self.gotouserpage)
        self.user_page_button_2.clicked.connect(self.gotouserpage)
        self.home_page_button.clicked.connect(self.gotohomepage)
        self.management_button.clicked.connect(self.gotomanagementpage)
        self.users_page_button.clicked.connect(self.gotouserspage)
        self.setting_button.clicked.connect(self.gotosettingpage)
        self.report_page_button.clicked.connect(self.gotoreportpage)
        self.confirm_button.clicked.connect(self.save_user_data)
        # 连接modify_avatar_button的点击事件到modify_avatar方法
        self.modify_avatar_button.clicked.connect(self.modify_avatar)
        self.avatar_path = None  # 新增实例变量来保存头像路径

    def gotohomepage(self):
        mainwindow = MainWindow(self.widget, self.user_data)
        self.widget.addWidget(mainwindow)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotomanagementpage(self):
        managementpage = ManagementPage(self.widget, self.user_data)
        self.widget.addWidget(managementpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserpage(self):
        userpage = UserPage(self.widget, self.user_data)
        self.widget.addWidget(userpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotouserspage(self):
        userspage = UsersPage(self.widget, self.user_data)
        self.widget.addWidget(userspage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotoreportpage(self):
        reportpage = ReportTables(self.widget, self.user_data)
        self.widget.addWidget(reportpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def gotosettingpage(self):
        settingpage = SettingPage(self.widget, self.user_data)
        self.widget.addWidget(settingpage)
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)

    def modify_avatar(self):
        # 打开文件选择对话框，让用户选择一个图片文件
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        name = self.name_lineEdit.text()
        if file_name:
            # 加载图片
            pixmap = QPixmap(file_name)
            # 裁剪图片为圆形并调整大小以适配avatar_label
            rounded_pixmap = self.make_rounded_pixmap(pixmap)
            # 将圆形图片显示在avatar_label中
            self.avatar_label.setPixmap(rounded_pixmap)

            # 获取姓名和学生ID
            name = self.name_lineEdit.text()
            student_id = self.student_id_lineEdit.text()
            type = self.type_comboBox.currentText()

            # 构建图片文件名
            avatar_filename = f"{name}_{student_id}.jpg"

            # 保存图片到文件系统中
            current_dir = os.getcwd()
            avatar_dir = os.path.join(current_dir, "avatars")
            if not os.path.exists(avatar_dir):
                os.makedirs(avatar_dir)
            avatar_path = os.path.join(avatar_dir, avatar_filename)
            shutil.copy(file_name, avatar_path)
            self.avatar_path = avatar_path  # 保存头像路径到实例变量中

    def save_user_data(self):
        try:
            # 获取所有文本框和下拉框的值
            name = self.name_lineEdit.text()
            gender = self.gender_comboBox.currentText()
            student_id = self.student_id_lineEdit.text()
            type = self.type_comboBox.currentText()
            email = self.email_lineEdit.text()
            team = self.team_lineEdit.text()
            phone = self.phone_lineEdit.text()
            college = self.college_comboBox.currentText()
            grade = self.grade_comboBox.currentText()
            inviter = self.inviter_lineEdit.text()

            # 连接到数据库
            cnx = mysql.connector.connect(user='root', password='123456',
                                          host='localhost',
                                          database='user_database')
            cursor = cnx.cursor()

            # 插入数据到user_data表
            query = ("INSERT INTO user_data "
                     "(avatar_path, name, gender, student_id, type, email, team, phone, college, grade, inviter) "
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
            cursor.execute(query, (
                self.avatar_path, name, gender, student_id, type, email, team, phone, college, grade, inviter))

            # 提交事务
            cnx.commit()

        except mysql.connector.Error as err:
            print("MySQL Error:", err)

        finally:
            # 关闭连接
            try:
                cursor.close()
            except NameError:
                pass
            try:
                cnx.close()
            except NameError:
                pass

    def make_rounded_pixmap(self, pixmap):
        # 创建一个空的图片，用于绘制圆形图片
        rounded_pixmap = QPixmap(120, 120)
        rounded_pixmap.fill(Qt.transparent)

        # 使用 QPainter 绘制圆形图片
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
        painter.setPen(QPen(Qt.transparent))
        path = QPainterPath()
        path.addEllipse(0, 0, 120, 120)
        painter.drawPath(path)
        painter.end()

        return rounded_pixmap


app = QApplication(sys.argv)
widget = QStackedWidget()
login = LoginWindow(widget)
login.setFixedSize(1280, 720)
widget.addWidget(login)
widget.show()
sys.exit(app.exec_())
