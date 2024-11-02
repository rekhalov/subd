import os
import shutil
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QStackedWidget, QLineEdit, QFileDialog, QMessageBox, QWidget, QVBoxLayout, QDialog, \
    QToolTip, QTextBrowser
from PyQt6.QtSql import QSqlDatabase
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QTableView, QPushButton, QComboBox, QApplication
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from natsort import natsorted
import pandas as pd
import sqlite3
import sys
import time

app = QApplication(sys.argv)
window = uic.loadUi("MainForm.ui")  # Загружаем форму

# Путь к исходной базе данных
db_file = "Vyst_mo.db"
temp_db_file = "temp_files/Vyst_mo_temp.db"

def create_db_copy():
    """Создает временную копию базы данных, если она еще не существует."""
    if not os.path.exists('temp_files'):
        os.makedirs('temp_files')  # Создаем папку, если она не существует
    if not os.path.exists(temp_db_file):
        shutil.copy(db_file, temp_db_file)  # Копируем оригинальный файл в временный
        print("Новый временный файл успешно создан!")
    else:
        print("Временный файл уже существует, создание нового файла отменено.")

def restore_db_copy():
    """Восстанавливает оригинальную базу данных, удаляя временную копию."""
    if os.path.exists(temp_db_file):
        try:
            disconnect_db()  # Закрываем все соединения с базой данных
            os.remove(temp_db_file)  # Удаляем временный файл
            print("Файл успешно удален!")
        except PermissionError:
            time.sleep(1)  # Ждем 1 секунду
            disconnect_db()  # Закрываем все соединения с базой данных
            try:
                os.remove(temp_db_file)  # Пробуем снова
                print("Файл успешно удален после повторной попытки!")
            except PermissionError:
                print("Не удалось удалить файл после повторной попытки.")

    # Измененное место, чтобы не создавать новый временный файл, если он уже есть
    create_db_copy()  # Создаем новую временную копию из оригинала

    show_table(combobox.currentText())

# Функция для подключения к базе данных
def connect_db(db_file):
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(db_file)
    if not db.open():
        print(f"Cannot establish a database connection to {db_file}!")
        return False
    return db

# Функция для отключения от базы данных
def disconnect_db():
    db = QSqlDatabase.database()
    if db.isOpen():
        db.close()
    QSqlDatabase.removeDatabase(db.connectionName())  # Удаляем соединение из списка соединений

# Создание копии базы данных при запуске программы
create_db_copy()

# Подключение к временной базе данных
connect_db(temp_db_file)

# Настройка кнопки undo_table
undo_table_button = window.findChild(QPushButton, "undo_table_button")
undo_table_button.clicked.connect(restore_db_copy)

# Проверка наличия QTableView в форме
table = window.findChild(QTableView, "main_table")
table.setSortingEnabled(True)

if table is None:
    print("QTableView 'main_table' not found in the UI file.")
    sys.exit(1)

combobox = window.findChild(QComboBox, "comboBoxTablitsi")

# Создание копии базы данных при запуске программы
create_db_copy()

# Функция, которая покажет что-то после действия
def on_action_happened(elem, index):

    if combobox.currentText() == "Vyst_mo":
        elem.setCurrentIndex(index)
        elem.setVisible(True)
def hide(elem):
    elem.setVisible(False)

# основной виджет делается невидимым
stackedWidget = window.findChild(QStackedWidget, "stackedWidget")
rubrics_widget = window.findChild(QWidget, "rubrics_widget")
stackedWidget.setVisible(False)
rubrics_widget.setVisible(False)

question_button = window.findChild(QPushButton, "question_button")
question_button.clicked.connect(lambda index: rubrics_widget.setVisible(True))

close_button = window.findChild(QPushButton, "close_button")
close_button.clicked.connect(lambda index: hide(stackedWidget))

close_button_2 = window.findChild(QPushButton, "close_button_2")
close_button_2.clicked.connect(lambda index: hide(stackedWidget))

close_button_3 = window.findChild(QPushButton, "close_button_3")
close_button_3.clicked.connect(lambda index: hide(stackedWidget))

close_button_4 = window.findChild(QPushButton, "close_button_4")
close_button_4.clicked.connect(lambda index: hide(rubrics_widget))

param_filtr = window.findChild(QAction, "param_filtr")
param_filtr.triggered.connect(lambda index: on_action_happened(stackedWidget, 0))

add_str_button_2 = window.findChild(QPushButton, "add_str_button_2")
edit_str_button_2 = window.findChild(QPushButton, "edit_str_button_2")

add_str_button_2.clicked.connect(lambda index: on_action_happened(stackedWidget, 1))
edit_str_button_2.clicked.connect(lambda index: on_action_happened(stackedWidget, 2))


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        if isinstance(data, pd.DataFrame):
            self._data = data.reset_index(drop=True)  # Сброс индекса, чтобы убрать его из данных.
        else:
            raise ValueError("Data must be a pandas DataFrame.")

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data.columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.iat[index.row(), index.column()])
        return None

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                column_names = {
                    'codvuz': 'Код ВУЗа',
                    'type': 'Тем.план',
                    'regnumber': 'Рег.№',
                    'z2': 'ВУЗ/Организация',
                    'grnti': 'Коды ГРНТИ',
                    'exhitype': 'Тип эксп.',
                    'vystavki': 'Выставки',
                    'exponat': 'Название выставочноко экспоната',
                    'bossname': 'Руководитель НИР',
                    'bosstitle': 'Должность рук.НИР',
                    'subject': 'Наименование проекта',
                    'z1': 'ВУЗ/Организация',
                    'z1full': 'Полное наименование ВУЗа/Организации',
                    'region': 'Федеральный округ',
                    'city': 'Город',
                    'status': 'Статус',
                    'obl': 'Номер области',
                    'oblname': 'Область',
                    'gr_ved': 'Группа ВЭД',
                    'prof': 'Профессия',
                    'codrub': 'Код',
                    'rubrika': 'Наименование рубрики',
                }
                return column_names.get(self._data.columns[section], self._data.columns[section])
            # Убираем отображение вертикального индекса
            if orientation == Qt.Orientation.Vertical:
                return None  # Не возвращаем номера строк
        return None

    def sort1(self, column: int, order: Qt.SortOrder):

        self.beginResetModel()
        sort_order_config = {
            Qt.SortOrder.AscendingOrder: True,
            Qt.SortOrder.DescendingOrder: False
        }
        self._data.sort_values(by=self._data.columns.tolist()[:3], ascending=True, inplace=True)
        self._data.sort_values(by=self._data.columns.tolist()[:column + 1],
                               ascending=sort_order_config[order], inplace=True)
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder):
        if column < 3:
            return
        self.beginResetModel()
        sort_order_config = {
            Qt.SortOrder.AscendingOrder: True,
            Qt.SortOrder.DescendingOrder: False
        }
        column_name = self._data.columns[column]
        if self._data[column_name].dtype == 'object':
            self._data[column_name] = self._data[column_name].astype(str)
        self._data.sort_values(by=column_name, ascending=sort_order_config[order], inplace=True)
        self.endResetModel()


    # Функция для получения значений выбранной строки
    def get_selected_row_data(self):
        selected_indexes = table.selectionModel().selectedRows()
        if selected_indexes:
            row_index = selected_indexes[0].row()
            row_data = []
            for col in range(self.columnCount()):
                index = self.index(row_index, col)
                value = self.data(index, Qt.ItemDataRole.DisplayRole)
                row_data.append(value)
            return row_data
        else:
            return None

    def get_data_by_vuz(self, vuz_value: str) -> list:
        """
        Возвращает список значений строки, соответствующей выбранному ВУЗу (z2) в таблице.
        """
        filtered_data = self._data[self._data["z2"] == vuz_value]
        if not filtered_data.empty:
            return filtered_data.iloc[0].tolist()
        return None


# Найдите элемент QTextBrowser в вашем интерфейсе
current_table_text = window.findChild(QTextBrowser, "current_table_text")

# Функция для обновления содержимого QTextBrowser
def update_current_table_text(current_table_name):
    if current_table_name.endswith(".csv") or current_table_name.endswith(".xlsx"):
        current_table_text.setPlainText(f"Загруженная таблица: {current_table_name}")
    else:
        current_table_text.setPlainText(f"Текущая таблица: {current_table_name}")


# Найдите элемент QTextBrowser в вашем интерфейсе
amount_str_text = window.findChild(QTextBrowser, "amount_str_text")

# Функция для обновления содержимого QTextBrowser с количеством строк
def update_amount_str_text():
    model = table.model()
    if model:
        row_count = model.rowCount()
        amount_str_text.setPlainText(f"Количество строк: {row_count}")
    else:
        amount_str_text.setPlainText("Количество строк: 0")

# Функция для загрузки таблицы
def show_table(table_name):
    current_table_name = table_name

    with sqlite3.connect(temp_db_file) as con:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {table_name}")
        col = cur.description
        data = pd.DataFrame(cur.fetchall(), columns=[col[0] for col in col])
    con.close()  # Добавлено закрытие соединения

    if table_name != "Vyst_mo":
        stackedWidget.setVisible(False)

    global model
    # Создаем модель PandasModel
    model = PandasModel(data)

    # Устанавливаем модель для QTableView
    table.setModel(model)

    table.resizeColumnsToContents()

    # Подключение к модели выбора таблицы
    selection_model = table.selectionModel()
    if selection_model:
        selection_model.selectionChanged.connect(lambda index: update_current_table_text(current_table_name))

    # Настройка выбора строки
    table.setSelectionMode(QTableView.SelectionMode.SingleSelection)  # Устанавливаем свойство
    table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    edit_str_button_2.setEnabled(True)
    add_str_button_2.setEnabled(True)
    del_str_button_2.setEnabled(True)
    disconnect_db()

    # Обновите содержимое QTextBrowser при загрузке таблицы
    update_current_table_text(current_table_name)
    update_amount_str_text()


combox_region = window.findChild(QComboBox, "combox_region")
combox_city = window.findChild(QComboBox, "combox_city")
combox_rubrica = window.findChild(QComboBox, "combox_rubrica")
combox_rubrica.currentIndexChanged.connect(lambda index: hide(rubrics_widget))
combox_vuz = window.findChild(QComboBox, "combox_vuz")
combox_vistexp = window.findChild(QComboBox, "combox_vistexp")

# Заполнение combox_vistexp значениями "Есть", "Нет", "Планируется"
combox_vistexp.addItem("")
combox_vistexp.addItem("Есть")
combox_vistexp.addItem("Нет")
combox_vistexp.addItem("Планируется")

def fill_combox(combox_name: QComboBox, stolb: str, table: str, flag: int = 1):
    with sqlite3.connect(temp_db_file) as con:
        cur = con.cursor()
        if flag:
            cur.execute(f"SELECT DISTINCT {stolb} FROM {table} ORDER BY {stolb} ASC")
            items = [row[0] for row in cur.fetchall()]
            combox_name.clear()  # Очистка combobox
            combox_name.addItem("")
            for item in items:
                # Приведите item к строковому типу
                combox_name.addItem(str(item))  # Приведем item к строке
        else:
            selected_region = combox_region.currentText()  # Получаем выбранный регион
            if selected_region:
                cur.execute(f"SELECT DISTINCT city FROM VUZ WHERE region = '{selected_region}' ORDER BY city ASC")
                items = [row[0] for row in cur.fetchall()]
                combox_name.clear()
                combox_name.addItem("")
                for item in items:
                    combox_name.addItem(str(item))  # Приведем item к строке
    con.close()  # Добавлено закрытие соединения
    disconnect_db()

def fill_combox_vuz():
    selected_region = combox_region.currentText()
    selected_city = combox_city.currentText()
    with sqlite3.connect(temp_db_file) as con:
        cur = con.cursor()
        if selected_region and selected_city:
            cur.execute(
                f"SELECT DISTINCT z2 FROM VUZ WHERE region = '{selected_region}' AND city = '{selected_city}' ORDER BY z2 ASC")
        elif selected_region:
            cur.execute(f"SELECT DISTINCT z2 FROM VUZ WHERE region = '{selected_region}' ORDER BY z2 ASC")
        else:
            cur.execute(f"SELECT DISTINCT z2 FROM VUZ ORDER BY z2 ASC")

        items = [row[0] for row in cur.fetchall()]
        combox_vuz.clear()
        combox_vuz.addItem("")
        for item in items:
            combox_vuz.addItem(item)
    con.close()  # Добавлено закрытие соединения
    disconnect_db()

def fill_comboxes_by_vuz(vuz_value):
    with sqlite3.connect(temp_db_file) as con:
        cur = con.cursor()
        cur.execute(f"SELECT region, city FROM VUZ WHERE z2 = '{vuz_value}'")
        row = cur.fetchone()
        if row:
            combox_region.setCurrentText(row[0])
            combox_city.setCurrentText(row[1])
            # Устанавливаем текущее значение combox_vuz
            combox_vuz.setCurrentText(vuz_value)
        else:
            # Если значение не найдено, сбрасываем combox_vuz
            combox_vuz.setCurrentIndex(0)
    con.close()  # Добавлено закрытие соединения

# Подключение к сигналу изменения выбранного ВУЗа
combox_vuz.currentIndexChanged.connect(lambda index: fill_comboxes_by_vuz(combox_vuz.currentText()))

# Заполняем комбобоксы
fill_combox(combox_region, "region", "VUZ")  # Заполнение комбобокса регионов
fill_combox(combox_city, "city", "VUZ")  # Заполнение комбобокса городов (используем flag=0 для фильтрации)
fill_combox_vuz()  # Заполнение комбобокса ВУЗов

# Подключение к сигналу изменения выбранного региона
combox_region.currentIndexChanged.connect(lambda index: fill_combox(combox_city, "city", "VUZ", flag=0))
combox_region.currentIndexChanged.connect(lambda index: fill_combox_vuz())

# Подключение к сигналу изменения выбранного города
combox_city.currentIndexChanged.connect(lambda index: fill_combox_vuz())

# Подключение к сигналу изменения выбранного ВУЗа
combox_vuz.currentIndexChanged.connect(lambda index: fill_comboxes_by_vuz(combox_vuz.currentText()))

fill_combox(combox_rubrica, "rubrika", "grntirub")


def string_for_filter():
    region_value = combox_region.currentText()
    city_value = combox_city.currentText()
    rubrica_value = combox_rubrica.currentText()
    vuz_value = combox_vuz.currentText()
    vistexp_value = combox_vistexp.currentText()

    base_query = """SELECT * FROM (
                        SELECT 
                            Vyst_mo.*, 
                            ROW_NUMBER() OVER (PARTITION BY Vyst_mo.codvuz, Vyst_mo.type, Vyst_mo.regnumber ORDER BY Vyst_mo.codvuz) as rn
                        FROM Vyst_mo"""

    join_clause = """INNER JOIN VUZ ON Vyst_mo.codvuz = VUZ.codvuz
                     INNER JOIN grntirub ON SUBSTR(Vyst_mo.grnti, 1, 2) = grntirub.codrub 
                     OR SUBSTR(Vyst_mo.grnti, INSTR(Vyst_mo.grnti, ',') + 1, 2) = grntirub.codrub"""

    where_clause = []

    if region_value:
        where_clause.append(f"VUZ.region = '{region_value}'")

    if city_value:
        where_clause.append(f"VUZ.city = '{city_value}'")

    if rubrica_value:
        with sqlite3.connect(temp_db_file) as con:
            cur = con.cursor()
            cur.execute(f"SELECT codrub FROM grntirub WHERE rubrika = '{rubrica_value}'")
            codrub_value = cur.fetchone()
            if codrub_value:
                codrub_value = codrub_value[0]
                where_clause.append(
                    f"(SUBSTR(Vyst_mo.grnti, 1, 2) = '{codrub_value}' OR SUBSTR(Vyst_mo.grnti, INSTR(Vyst_mo.grnti, ',') + 1, 2) = '{codrub_value}')")

    if vuz_value:
        where_clause.append(f"VUZ.z2 = '{vuz_value}'")

    if vistexp_value:
        if vistexp_value == "Есть":
            vistexp_value = "Е"
        elif vistexp_value == "Нет":
            vistexp_value = "Н"
        elif vistexp_value == "Планируется":
            vistexp_value = "П"
        where_clause.append(f"Vyst_mo.exhitype = '{vistexp_value}'")

    query = f"{base_query} {join_clause}"

    # Если есть условия, добавляем их
    if where_clause:
        query += " WHERE " + " AND ".join(where_clause)

    query += ") as filtered WHERE rn = 1"  # добавляем фильтрацию по rn

    print(f"Запрос фильтрации: {query}")  # для проверки
    disconnect_db()
    return query

# Функция для фильтрации таблицы
def show_filtered_table(table_name):
    current_table_name = table_name

    with sqlite3.connect(temp_db_file) as con:
        cur = con.cursor()

        cur.execute(f"{string_for_filter()}")
        col = cur.description
        data = pd.DataFrame(cur.fetchall(), columns=[col[0] for col in col])
    con.close()  # Добавлено закрытие соединения
    # Создаем модель PandasModel
    model = PandasModel(data)

    # Устанавливаем модель для QTableView
    table.setModel(model)

    table.resizeColumnsToContents()

    # Подключение к модели выбора таблицы
    selection_model = table.selectionModel()
    if selection_model:
        selection_model.selectionChanged.connect(lambda index: update_current_table_text(current_table_name))

    # Настройка выбора строки
    table.setSelectionMode(QTableView.SelectionMode.SingleSelection) # Устанавливаем свойство
    table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    disconnect_db()

    # Обновите содержимое QTextBrowser при фильтрации таблицы
    update_current_table_text(current_table_name)
    update_amount_str_text()

up_down_sort_box = window.findChild(QComboBox, "up_down_sort_box")

def sort_table():
    # Получаем модель, связанную с QTableView
    model = table.model()
    if model is None:
        print("No model found!")
        return
    # Включаем сортировку по нажатию на заголовок столбца

    # Определяем список сортируемых столбцов
    sort_columns = [0,1,2]

    # Сортировка по выбранным столбцам
    if sort_columns:
        print(f"Sorting by columns: {sort_columns}")  # Отладочная информация

        for col in sort_columns:
            # Сортировка по каждому выбранному столбцу
            # Передаем порядок сортировки - по возрастанию (AscendingOrder)
            if (up_down_sort_box.currentText() == "Возрастанию"):
                model.sort1(col, Qt.SortOrder.AscendingOrder)
            else: model.sort1(col, Qt.SortOrder.DescendingOrder)
    else:
        print("No columns selected for sorting.")
    disconnect_db()

# Подключение функции к кнопке "Сортировать"
sort_button = window.findChild(QPushButton, "sort_button")
sort_button.clicked.connect(lambda: sort_table())

def filter_comboxes_sbros():
    # Отключаем сигналы изменения индекса комбобоксов
    combox_region.blockSignals(True)
    combox_city.blockSignals(True)
    combox_vuz.blockSignals(True)
    combox_rubrica.blockSignals(True)
    combox_vistexp.blockSignals(True)

    # Заполняем комбобоксы
    fill_combox(combox_region, "region", "VUZ")  # Заполнение комбобокса регионов
    fill_combox(combox_city, "city", "VUZ")  # Заполнение комбобокса городов (используем flag=0 для фильтрации)
    fill_combox_vuz()  # Заполнение комбобокса ВУЗов
    fill_combox(combox_rubrica, "rubrika", "grntirub")
    combox_vistexp.setCurrentText("")

    # Включаем сигналы изменения индекса комбобоксов
    combox_region.blockSignals(False)
    combox_city.blockSignals(False)
    combox_vuz.blockSignals(False)
    combox_rubrica.blockSignals(False)
    combox_vistexp.blockSignals(False)

    # Обновляем таблицу
    show_table(combobox.currentText())

# Подключение кнопки filter_sbros_button к функции сброса фильтров
filter_sbros_button = window.findChild(QPushButton, "filter_sbros_button")
filter_sbros_button.clicked.connect(filter_comboxes_sbros)

# Подключение сигналов изменения индекса комбобоксов к функции фильтрации таблицы
combox_region.currentIndexChanged.connect(lambda: show_filtered_table(combobox.currentText()))
combox_city.currentIndexChanged.connect(lambda: show_filtered_table(combobox.currentText()))
combox_vuz.currentIndexChanged.connect(lambda: show_filtered_table(combobox.currentText()))
combox_rubrica.currentIndexChanged.connect(lambda: show_filtered_table(combobox.currentText()))
combox_vistexp.currentIndexChanged.connect(lambda: show_filtered_table(combobox.currentText()))

vystavki_text = window.findChild(QLineEdit, "vystavki_text")
exponat_text = window.findChild(QLineEdit, "exponat_text")
bossname_text = window.findChild(QLineEdit, "bossname_text")
bosstitle_text = window.findChild(QLineEdit, "bosstitle_text")
subject_text = window.findChild(QLineEdit, "subject_text")


combox_codvuz = window.findChild(QComboBox, "combox_codvuz")
combox_type = window.findChild(QComboBox, "combox_type")
# combox_regnumber = window.findChild(QComboBox, "combox_regnumber")
combox_vuz_2 = window.findChild(QComboBox, "combox_vuz_2")
combox_vistexp_2 = window.findChild(QComboBox, "combox_vistexp_2")

regnumber_text = window.findChild(QLineEdit, "regnumber_text")
grnti_text = window.findChild(QLineEdit, "grnti_text")
grnti_text = window.findChild(QLineEdit, "grnti_text")
# Устанавливаем маску для ввода
grnti_text.setInputMask("00.00.00,00.00.00")

# Устанавливаем валидатор для ограничения ввода только цифрами

table_view = window.findChild(QTableView, "tableView")
update_button = window.findChild(QPushButton, "pushButtonUpdateTable")

combobox = window.findChild(QtWidgets.QComboBox, "comboBoxTablitsi")
# Подключаем функцию update_table к сигналу изменения значения combobox
combobox.currentIndexChanged.connect(lambda index: show_table(combobox.currentText()))

update_button.clicked.connect(lambda index: show_table(combobox.currentText()))

updatetable = window.findChild(QAction, "action3_updatetable")
updatetable.triggered.connect(lambda index: show_table(combobox.currentText()))
def populate_comboboxes(combox_codvuz, combox_type, combox_vuz_2, combox_vistexp_2):
    """
    Заполняет комбобоксы данными из базы данных.
    """
    conn = sqlite3.connect("Vyst_mo.db")
    cursor = conn.cursor()

    # Очищаем комбобоксы перед заполнением
    combox_codvuz.clear()
    combox_type.clear()
    combox_vuz_2.clear()
    combox_vistexp_2.clear()

    # Получаем уникальные значения из столбцов, преобразуя их в строки и сортируя
    cursor.execute("SELECT DISTINCT codvuz FROM Vyst_mo ORDER BY codvuz")
    codvuz_values = [str(row[0]) for row in cursor.fetchall()]
    combox_codvuz.addItem("")  # Добавляем пустой начальный элемент
    combox_codvuz.addItems(codvuz_values)

    cursor.execute("SELECT DISTINCT type FROM Vyst_mo ORDER BY type")
    type_values = [row[0] for row in cursor.fetchall()]
    combox_type.addItem("")  # Добавляем пустой начальный элемент
    combox_type.addItems(type_values)

    cursor.execute("SELECT DISTINCT z2 FROM Vyst_mo ORDER BY z2")
    z2_values = [row[0] for row in cursor.fetchall()]
    combox_vuz_2.addItem("")  # Добавляем пустой начальный элемент
    combox_vuz_2.addItems(z2_values)

    cursor.execute("SELECT DISTINCT exhitype FROM Vyst_mo ORDER BY exhitype")
    exhitype_values = [row[0] for row in cursor.fetchall()]
    combox_vistexp_2.addItem("")  # Добавляем пустой начальный элемент

    # Преобразуем значения "Е", "Н", "П" в "Есть", "Нет", "Планируется"
    for value in exhitype_values:
        if value == "Е":
            combox_vistexp_2.addItem("Есть")
        elif value == "Н":
            combox_vistexp_2.addItem("Нет")
        elif value == "П":
            combox_vistexp_2.addItem("Планируется")

    conn.close()

def fill_comboxes_by_vuz_2(vuz_value):
    with sqlite3.connect("Vyst_mo.db") as con:
        cur = con.cursor()
        cur.execute(f"SELECT codvuz FROM Vyst_mo WHERE z2 = '{vuz_value}'")
        row = cur.fetchone()  # Получаем первую строку, соответствующую запросу

        if row:  # Если строка найдена
            combox_codvuz.setCurrentText(str(row[0]))  # Устанавливаем codvuz в combox_codvuz

def fill_comboxes_by_codvuz(codvuz_value):
    with sqlite3.connect("Vyst_mo.db") as con:
        cur = con.cursor()
        cur.execute(f"SELECT z2 FROM Vyst_mo WHERE codvuz = '{codvuz_value}'")
        row = cur.fetchone()  # Получаем первую строку, соответствующую запросу

        if row:  # Если строка найдена
            combox_vuz_2.setCurrentText(str(row[0]))  # Устанавливаем z2 в combox_vuz_2
        else:
            combox_vuz_2.setCurrentIndex(0)  # Сбрасываем combox_vuz_2 на первый элемент (пустой)

# Подключение сигнала изменения индекса combox_codvuz к функции fill_comboxes_by_codvuz
combox_codvuz.currentIndexChanged.connect(lambda index: fill_comboxes_by_codvuz(combox_codvuz.currentText()))

# Запускаем функцию заполнения комбобоксов
populate_comboboxes(combox_codvuz, combox_type, combox_vuz_2, combox_vistexp_2)

# Подключение к сигналу изменения выбранного ВУЗа
combox_vuz_2.currentIndexChanged.connect(lambda index: fill_comboxes_by_vuz_2(combox_vuz_2.currentText()))

sbros_str_button = window.findChild(QPushButton, "sbros_str_button")
sbros_str_button.clicked.connect(lambda index: populate_comboboxes(combox_codvuz, combox_type, combox_vuz_2, combox_vistexp_2))

def string_for_add():
    """
    Формирует строку SQL-запроса для добавления строки в таблицу Vyst_mo.
    """
    # Получаем значения из элементов интерфейса
    codvuz_val = combox_codvuz.currentText()
    type_val = combox_type.currentText()
    z2_val = combox_vuz_2.currentText()
    exhitype_val = combox_vistexp_2.currentText()

    regnumber_val = regnumber_text.text()
    grnti_val = grnti_text.text()
    vystavki_val = vystavki_text.text()
    exponat_val = exponat_text.text()
    bossname_val = bossname_text.text()
    bosstitle_val = bosstitle_text.text()
    subject_val = subject_text.text()

    # Проверка на корректность кода ВУЗа
    if codvuz_val:
        try:
            codvuz_val = int(codvuz_val)
        except ValueError:
            show_error_message("Некорректный код ВУЗа.")
            return None

    # Преобразуем значения "Есть", "Нет", "Планируется" в "Е", "Н", "П"
    if exhitype_val == "Есть":
        exhitype_val = "Е"
    elif exhitype_val == "Нет":
        exhitype_val = "Н"
    elif exhitype_val == "Планируется":
        exhitype_val = "П"

    # Проверка на наличия экспоната в случае определенного условия
    if exhitype_val == "Н" and (exponat_val or vystavki_val or subject_val):
        show_error_message("Экспоната нет!")
        return None  # Прерываем формирование запроса

    # Список значений для запроса INSERT
    values = [
        codvuz_val,
        type_val,
        regnumber_val,
        z2_val,
        grnti_val,
        exhitype_val,
        vystavki_val,
        exponat_val,
        bossname_val,
        bosstitle_val,
        subject_val
    ]

    # SQL-запрос
    query = "INSERT INTO Vyst_mo VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    print(f"Сформированный запрос: {query}")
    disconnect_db()
    return query, values

def add_str():
    """
    Добавляет строку в таблицу Vyst_mo и выделяет её.
    """
    try:

        with sqlite3.connect(temp_db_file) as con:
            cur = con.cursor()
            query, values = string_for_add()

            if query is None:
                con.close()
                return

            # Проверка на уникальность записи
            check_query = """
            SELECT COUNT(*) FROM Vyst_mo
            WHERE codvuz = ? AND type = ? AND regnumber = ?
            """
            cur.execute(check_query, (values[0], values[1], values[2]))
            exists = cur.fetchone()[0]

            if exists > 0:
                show_error_message("Ошибка: Запись с такими значениями уже существует.")
                return

            # Выполнение вставки
            cur.execute(query, values)
            con.commit()
            print(f"Запрос выполнен: {query}, БД ЗАКРЫТА")

            clear_checkbox()
            # Обновление таблицы
            show_table(combobox.currentText())

            # Выделение последней добавленной строки
            model = table.model()
            if model is not None:
                last_row = model.rowCount() - 1
                table.selectRow(last_row)
            else:
                show_error_message("Ошибка: модель таблицы не задана!")
    except sqlite3.Error as e:
        show_error_message(f"Ошибка базы данных: {e}")
        con.close()
    except Exception as e:
        # show_error_message(f"Произошла ошибка: {e}")
        con.close()
    finally:
        con.close()
def clear_checkbox():
    """
    Очищает поля и сбрасывает состояния комбобоксов.
    """
    populate_comboboxes(combox_codvuz, combox_type, combox_vuz_2, combox_vistexp_2)
    bossname_text.clear()
    bosstitle_text.clear()
    grnti_text.clear()
    vystavki_text.clear()
    exponat_text.clear()
    subject_text.clear()
    regnumber_text.clear()

def show_error_message(message):
    """
    Отображает сообщение об ошибке в отдельном окне.
    """
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)  # Используем Icon.Critical
    msg_box.setText("Ошибка")
    msg_box.setInformativeText(message)
    msg_box.setWindowTitle("Ошибка")
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)  # Используем StandardButton.Ok
    msg_box.exec()

del_str_button = window.findChild(QPushButton, "del_str_button")
# del_str_button.clicked.connect(lambda: del_str())

add_str_button = window.findChild(QPushButton, "add_str_button")
add_str_button.clicked.connect(lambda: add_str())

vystavki_text_2 = window.findChild(QLineEdit, "vystavki_text_2")
exponat_text_2 = window.findChild(QLineEdit, "exponat_text_2")
bosstitle_text_2 = window.findChild(QLineEdit, "bosstitle_text_2")
bossname_text_2 = window.findChild(QLineEdit, "bossname_text_2")
subject_text_2 = window.findChild(QLineEdit, "subject_text_2")

combox_codvuz_2 = window.findChild(QComboBox, "combox_codvuz_2")
combox_type_2 = window.findChild(QComboBox, "combox_type_2")
combox_regnumber_2 = window.findChild(QComboBox, "combox_regnumber_2")
combox_vuz_3 = window.findChild(QComboBox, "combox_vuz_3")
combox_vistexp_3 = window.findChild(QComboBox, "combox_vistexp_3")

grnti_text_2 = window.findChild(QLineEdit, "grnti_text_2")
# Устанавливаем маску для ввода
grnti_text_2.setInputMask("00.00.00,00.00.00")

fill_combox(combox_codvuz_2,"codvuz","Vyst_mo")
fill_combox(combox_type_2,"type","Vyst_mo")
fill_combox(combox_regnumber_2,"regnumber","Vyst_mo")
fill_combox(combox_vuz_3,"z2","Vyst_mo")
fill_combox(combox_vistexp_3,"exhitype","Vyst_mo")

def populate_comboboxes_2(combox_codvuz, combox_type, combox_regnumber, combox_vuz_2, combox_vistexp_2):
    """
    Заполняет комбобоксы данными из базы данных.
    """

    conn = sqlite3.connect("Vyst_mo.db")
    cursor = conn.cursor()

    # Очищаем комбобоксы перед заполнением
    combox_codvuz.clear()
    combox_type.clear()
    combox_regnumber.clear()
    combox_vuz_2.clear()
    combox_vistexp_2.clear()

    # Получаем уникальные значения из столбцов, преобразуя их в строки и сортируя
    cursor.execute("SELECT DISTINCT codvuz FROM Vyst_mo ORDER BY codvuz")
    codvuz_values = [str(row[0]) for row in cursor.fetchall()]
    combox_codvuz.addItem("")  # Добавляем пустой начальный элемент
    combox_codvuz.addItems(codvuz_values)

    cursor.execute("SELECT DISTINCT type FROM Vyst_mo ORDER BY type")
    type_values = [row[0] for row in cursor.fetchall()]
    combox_type.addItem("")  # Добавляем пустой начальный элемент
    combox_type.addItems(type_values)

    cursor.execute("SELECT DISTINCT regnumber FROM Vyst_mo ORDER BY regnumber")
    regnumber_values = [str(row[0]) for row in cursor.fetchall()]
    combox_regnumber.addItem("")  # Добавляем пустой начальный элемент
    combox_regnumber.addItems(regnumber_values)

    cursor.execute("SELECT DISTINCT z2 FROM Vyst_mo ORDER BY z2")
    z2_values = [row[0] for row in cursor.fetchall()]
    combox_vuz_2.addItem("")  # Добавляем пустой начальный элемент
    combox_vuz_2.addItems(z2_values)

    cursor.execute("SELECT DISTINCT exhitype FROM Vyst_mo ORDER BY exhitype")
    exhitype_values = [row[0] for row in cursor.fetchall()]
    combox_vistexp_2.addItem("")  # Добавляем пустой начальный элемент
    combox_vistexp_2.addItems(exhitype_values)

    conn.close()
def handle_table_selection(selected):
    # Получение индексов выбранных строк
    row_indices = selected.indexes()
    if row_indices:
        selected_row_index = row_indices[0].row()
        print(f"Индекс выбранной строки: {selected_row_index}")

        # Получаем данные из выбранной строки
        model = table.model()
        if model:
            selected_row_data = [
                model.data(model.index(selected_row_index, col), Qt.ItemDataRole.DisplayRole)
                for col in range(model.columnCount())
            ]
            print(f"Данные выбранной строки: {selected_row_data}")

            # Предполагаем, что порядок данных в selected_row_data соответствует порядку полей
            if len(selected_row_data) >= 10:  # Проверяем, достаточно ли данных
                combox_codvuz_2.setCurrentText(selected_row_data[0])  # Пример: 1-й столбец
                combox_type_2.setCurrentText(selected_row_data[1])    # Пример: 2-й столбец
                combox_regnumber_2.setCurrentText(selected_row_data[2])  # Пример: 3-й столбец
                combox_vuz_3.setCurrentText(selected_row_data[3])       # Пример: 4-й столбец
                bossname_text_2.setText(selected_row_data[4])          # Пример: 5-й столбец
                bosstitle_text_2.setText(selected_row_data[5])         # Пример: 6-й столбец
                grnti_text_2.setText(selected_row_data[6])             # Пример: 7-й столбец
                combox_vistexp_3.setCurrentText(selected_row_data[7])  # Пример: 8-й столбец
                vystavki_text_2.setText(selected_row_data[8])          # Пример: 9-й столбец
                exponat_text_2.setText(selected_row_data[9])           # Пример: 10-й столбец
                subject_text_2.setText(selected_row_data[10])
            else:
                print("Недостаточно данных в выбранной строке.")

def handle_edit_row():
    selected = table.selectionModel().selectedRows()
    if selected:
        selected_row_index = selected[0].row()
        print(f"Индекс редактируемой строки: {selected_row_index}")

        # Получаем данные из выделенной строки
        model = table.model()
        if model:
            selected_row_data = [
                model.data(model.index(selected_row_index, col), Qt.ItemDataRole.DisplayRole)
                for col in range(model.columnCount())
            ]
            print(f"Данные редактируемой строки: {selected_row_data}")

            # Получаем новые данные из полей ввода
            new_codvuz = combox_codvuz_2.currentText()
            new_type = combox_type_2.currentText()
            new_regnumber = combox_regnumber_2.currentText()
            new_vuz = combox_vuz_3.currentText()
            new_bossname = bossname_text_2.text()
            new_bosstitle = bosstitle_text_2.text()
            new_grnti = grnti_text_2.text()
            new_vistexp = combox_vistexp_3.currentText()
            new_vystavki = vystavki_text_2.text()
            new_exponat = exponat_text_2.text()
            new_subject = subject_text_2.text()

            # Обновляем данные в базе данных
            if len(selected_row_data) >= 3:  # Достаточно данных для идентификации строки
                codvuz = selected_row_data[0]
                type = selected_row_data[1]
                regnumber = selected_row_data[2]

                with sqlite3.connect(temp_db_file) as con:
                    cur = con.cursor()
                    cur.execute(
                        """
                        UPDATE Vyst_mo
                        SET codvuz=?, type=?, regnumber=?, z2=?, bossname=?, bosstitle=?, grnti=?, exhitype=?, vystavki=?, exponat=?, subject=?
                        WHERE codvuz=? AND type=? AND regnumber=?
                        """,
                        (new_codvuz, new_type, new_regnumber, new_vuz, new_bossname, new_bosstitle, new_grnti,
                         new_vistexp, new_vystavki, new_exponat, new_subject, codvuz, type, regnumber)
                    )
                    con.commit()
                con.close()  # Добавлено закрытие соединения
                disconnect_db()

                # Обновляем таблицу
                show_table(combobox.currentText())

                fill_combox(combox_codvuz_2, "codvuz", "Vyst_mo")
                fill_combox(combox_type_2, "type", "Vyst_mo")
                fill_combox(combox_regnumber_2, "regnumber", "Vyst_mo")
                fill_combox(combox_vuz_3, "z2", "Vyst_mo")
                fill_combox(combox_vistexp_3, "exhitype", "Vyst_mo")

                grnti_text_2.clear()
                vystavki_text_2.clear()
                exponat_text_2.clear()
                bossname_text_2.clear()
                bosstitle_text_2.clear()
                subject_text_2.clear()
            else:
                print("Недостаточно данных в выбранной строке для редактирования.")
    else:
        print("Нет выбранных строк для редактирования.")


# В функции handle_delete_row
def handle_delete_row():

    selected = table.selectionModel().selectedRows()
    if selected:
        selected_row_index = selected[0].row()
        print(f"Индекс удаляемой строки: {selected_row_index}")

        # Получаем данные из выбранной строки
        model = table.model()
        if model:
            selected_row_data = [
                model.data(model.index(selected_row_index, col), Qt.ItemDataRole.DisplayRole)
                for col in range(model.columnCount())
            ]
            print(f"Данные удаляемой строки: {selected_row_data}")

            # Удаляем запись из базы данных (например, по первым нескольким столбцам)
            if len(selected_row_data) >= 3:  # Достаточно данных для идентификации строки
                codvuz = selected_row_data[0]
                type = selected_row_data[1]
                regnumber = selected_row_data[2]

                msg_box = QMessageBox(window)
                msg_box.setIcon(QMessageBox.Icon.Question)
                msg_box.setWindowTitle("Подтверждение удаления")
                msg_box.setText("Вы действительно хотите удалить выбранную строку?")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
                no_button = msg_box.button(QMessageBox.StandardButton.No)

                yes_button.setText("Да")
                no_button.setText("Нет")

                reply = msg_box.exec()
                if reply == QMessageBox.StandardButton.Yes:

                    with sqlite3.connect(temp_db_file) as con:
                        cur = con.cursor()
                        cur.execute(
                            "DELETE FROM Vyst_mo WHERE codvuz=? AND type=? AND regnumber=?",
                            (codvuz, type, regnumber)
                        )
                        con.commit()
                    con.close()  # Добавлено закрытие соединения
                    disconnect_db()

                    # Удаляем строку из таблицы
                    model.removeRow(selected_row_index)
                    show_table(combobox.currentText())

                    fill_combox(combox_codvuz_2, "codvuz", "Vyst_mo")
                    fill_combox(combox_type_2, "type", "Vyst_mo")
                    fill_combox(combox_regnumber_2, "regnumber", "Vyst_mo")
                    fill_combox(combox_vuz_3, "z2", "Vyst_mo")
                    fill_combox(combox_vistexp_3, "exhitype", "Vyst_mo")

                    grnti_text_2.clear()
                    vystavki_text_2.clear()
                    exponat_text_2.clear()
                    bossname_text_2.clear()
                    bosstitle_text_2.clear()
                    subject_text_2.clear()

                    populate_comboboxes_2(combox_codvuz_2, combox_type_2, combox_regnumber_2, combox_vuz_3, combox_vistexp_3)
                else:
                    return

            else:
                print("Недостаточно данных в выбранной строке для удаления.")
    else:
        print("Нет выбранных строк для удаления.")


# Привязываем обработчик к кнопке
del_str_button_2 = window.findChild(QPushButton, "del_str_button_2")
del_str_button_2.clicked.connect(handle_delete_row)


def keyPressEvent(event):
    if event.key() == Qt.Key.Key_Delete:  # Проверка нажатия клавиши Delete
        handle_delete_row()

# Подключаем обработчик событий клавиатуры к окну
window.keyPressEvent = keyPressEvent

# Функция для удаления строки и добавления новой

edit_str_button = window.findChild(QPushButton, "edit_str_button")
edit_str_button.clicked.connect(handle_edit_row)

# Функция для сохранения таблицы в файл
def save_table_to_file():
    folder_path = "saved_tables"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Устанавливаем имя файла по умолчанию
    default_file_name = "groupe"
    file_path, _ = QFileDialog.getSaveFileName(window, "Сохранить таблицу",
                                                 os.path.join(folder_path, default_file_name),
                                                 "CSV Files (*.csv);;Excel Files (*.xlsx)")
    if file_path:
        model = table.model()  # Получение модели таблицы
        data = model._data  # Получение данных из модели
        if file_path.endswith(".csv"):
            data.to_csv(file_path, index=False)
        elif file_path.endswith(".xlsx"):
            data.to_excel(file_path, index=False)

# Функция для заполнения QComboBox названиями файлов из папки
def fill_groupe_to_load_cbox(combo_box):
    folder_path = "saved_tables"
    if os.path.exists(folder_path):
        files = [f for f in os.listdir(folder_path) if f.endswith(".csv") or f.endswith(".xlsx")]
        combo_box.clear()
        combo_box.addItem("")
        combo_box.addItems(files)

# Функция для открытия нового окна add_groupe.ui
def open_add_groupe():
    add_groupe_dialog = QDialog(window)  # Создаем QDialog
    add_groupe_window = uic.loadUi("add_groupe.ui", add_groupe_dialog)  # Загружаем форму add_groupe.ui в QDialog
    add_groupe_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)  # Устанавливаем модальность окна
    add_groupe_dialog.show()

    main_table = add_groupe_window.findChild(QTableView, "main_table")
    load_groupe_button = add_groupe_window.findChild(QPushButton, "load_groupe_button")
    groupe_to_load_cbox = add_groupe_window.findChild(QComboBox, "groupe_to_load_cbox")

    fill_groupe_to_load_cbox(groupe_to_load_cbox)

    groupe_to_load_cbox.currentIndexChanged.connect(lambda index: load_table_from_file(os.path.join("saved_tables", groupe_to_load_cbox.currentText()), main_table))

    load_groupe_button.clicked.connect(lambda: load_and_close(add_groupe_dialog, groupe_to_load_cbox.currentText()))

def load_and_close(dialog, file_name):
    file_path = os.path.join("saved_tables", file_name)
    current_table_name = file_name
    if not file_name or not os.path.exists(file_path):
        show_error_message("Пожалуйста, выберите файл для загрузки.")
        return
    load_table_from_file(file_path, table)
    dialog.close()

    # Обновите содержимое QTextBrowser при загрузке таблицы из файла
    update_current_table_text(current_table_name)
    update_amount_str_text()

# Функция для загрузки таблицы из файла
def load_table_from_file(file_path, table_view):

    if not file_path:
        return

    if file_path.endswith(".csv"):
        data = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        data = pd.read_excel(file_path)
    else:
        return

    model = PandasModel(data)  # Создание модели для загруженных данных
    table_view.setModel(model)  # Установка модели в таблицу
    table_view.resizeColumnsToContents()  # Автоматическое изменение размера столбцов
    table_view.horizontalHeader().setStretchLastSection(True)  # Растягивание последнего столбца
    edit_str_button_2.setEnabled(False)
    add_str_button_2.setEnabled(False)
    del_str_button_2.setEnabled(False)

# Функция для отображения сообщения об ошибке
def show_error_message(message):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)  # Используем Icon.Critical
    msg_box.setText("Ошибка")
    msg_box.setInformativeText(message)
    msg_box.setWindowTitle("Ошибка")
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)  # Используем StandardButton.Ok
    msg_box.exec()

# Подключение кнопки load_button к функции открытия нового окна
load_button = window.findChild(QPushButton, "load_button")
load_button.clicked.connect(open_add_groupe)

# Подключение кнопки save_table_act к функции сохранения таблицы
save_table_act = window.findChild(QAction, "save_table_act")
save_table_act.triggered.connect(save_table_to_file)

save_button = window.findChild(QPushButton, "save_button")
save_button.clicked.connect(save_table_to_file)

rubriks_table = window.findChild(QTableView, "rubriks_table")
def load_grntirub_table():
    """
    Загружает данные из таблицы grntirub и устанавливает их в rubrics_table.
    """
    with sqlite3.connect(temp_db_file) as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM grntirub")
        col = cur.description
        data = pd.DataFrame(cur.fetchall(), columns=[col[0] for col in col])
    con.close()  # Добавлено закрытие соединения

    # Создаем модель PandasModel
    model = PandasModel(data)

    # Устанавливаем модель для QTableView
    rubriks_table.setModel(model)

    # Настройка QTableView
    rubriks_table.setSortingEnabled(True)
    rubriks_table.resizeColumnsToContents()
    rubriks_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
    rubriks_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)


# Загрузите данные в rubrics_table при запуске программы
load_grntirub_table()

question_button.setToolTip("Показать рубрики")

# Функция для открытия нового окна join_2_groupes.ui
def open_join_2_groupes():
    join_2_groupes_dialog = QDialog(window)  # Создаем QDialog
    join_2_groupes_window = uic.loadUi("join_2_groupes.ui", join_2_groupes_dialog)  # Загружаем форму join_2_groupes.ui в QDialog
    join_2_groupes_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)  # Устанавливаем модальность окна
    join_2_groupes_dialog.show()

    main_table = join_2_groupes_window.findChild(QTableView, "main_table")
    groupe_to_join_cbox = join_2_groupes_window.findChild(QComboBox, "groupe_to_join_cbox")
    groupe_to_join_cbox_2 = join_2_groupes_window.findChild(QComboBox, "groupe_to_join_cbox_2")
    join_groupe_button = join_2_groupes_window.findChild(QPushButton, "join_groupe_button")

    fill_groupe_to_load_cbox(groupe_to_join_cbox)
    fill_groupe_to_load_cbox(groupe_to_join_cbox_2)

    groupe_to_join_cbox.currentIndexChanged.connect(lambda index: load_table_from_file(os.path.join("saved_tables", groupe_to_join_cbox.currentText()), main_table))
    groupe_to_join_cbox_2.currentIndexChanged.connect(lambda index: load_table_from_file(os.path.join("saved_tables", groupe_to_join_cbox_2.currentText()), main_table))

    join_groupe_button.clicked.connect(lambda: join_and_save(join_2_groupes_dialog, groupe_to_join_cbox.currentText(), groupe_to_join_cbox_2.currentText(), main_table))

# Функция для объединения и сохранения таблиц
def join_and_save(dialog, file_name1, file_name2, table_view):
    file_path1 = os.path.join("saved_tables", file_name1)
    file_path2 = os.path.join("saved_tables", file_name2)

    if not file_name1 or not os.path.exists(file_path1) or not file_name2 or not os.path.exists(file_path2):
        show_error_message("Пожалуйста, выберите оба файла для объединения.")
        return

    data1 = pd.read_csv(file_path1) if file_path1.endswith(".csv") else pd.read_excel(file_path1)
    data2 = pd.read_csv(file_path2) if file_path2.endswith(".csv") else pd.read_excel(file_path2)

    joined_data = pd.concat([data1, data2], ignore_index=True)

    # Удаление дубликатов по первым 3 элементам!!!
    unique_data = joined_data.drop_duplicates(subset=joined_data.columns[:3], keep='first')

    folder_path = "saved_tables"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    default_file_name = "joined_groupe.csv"
    file_path, _ = QFileDialog.getSaveFileName(window, "Сохранить объединенную таблицу",
                                                 os.path.join(folder_path, default_file_name),
                                                 "CSV Files (*.csv);;Excel Files (*.xlsx)")

    #ЕСЛИ НАМ НЕ ВСЕ РАВНО НА СТРОКИ С ОДИНАКОВЫМ КЛЮЧЕМ
    if file_path:
        if file_path.endswith(".csv"):
            unique_data.to_csv(file_path, index=False)
        elif file_path.endswith(".xlsx"):
            unique_data.to_excel(file_path, index=False)

    # #ЕСЛИ НАМ ВСЕ РАВНО НА СТРОКИ С ОДИНАКОВЫМ КЛЮЧЕМ
    # if file_path:
    #     if file_path.endswith(".csv"):
    #         joined_data.to_csv(file_path, index=False)
    #     elif file_path.endswith(".xlsx"):
    #         joined_data.to_excel(file_path, index=False)

        model = PandasModel(joined_data)  # Создание модели для объединенных данных
        table_view.setModel(model)  # Установка модели в таблицу
        table_view.resizeColumnsToContents()  # Автоматическое изменение размера столбцов
        table_view.horizontalHeader().setStretchLastSection(True)  # Растягивание последнего столбца

        # dialog.close()

# Подключение кнопки для открытия нового окна join_2_groupes.ui
join_2_groupes_button = window.findChild(QPushButton, "join_2_groupes_button")
join_2_groupes_button.clicked.connect(open_join_2_groupes)

window.show()
app.exec()
