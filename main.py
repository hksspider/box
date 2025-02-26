import sys
import json
import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QMenuBar, QMenu,
                             QTreeWidget, QTreeWidgetItem, QDialog, QFormLayout, QLineEdit,
                             QDialogButtonBox, QDateEdit, QMessageBox, QComboBox, QHeaderView,
                             QFileDialog, QInputDialog, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QDate, QSize, QSortFilterProxyModel
from PyQt6.QtGui import QIcon, QFont, QKeySequence, QDoubleValidator, QShortcut
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

DATA_FILE = "accounting_data.json"

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("برنامج المحاسبة")
        self.showMaximized()

        self.create_menu()
        self.create_central_widget()

    def create_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("ملف")
        exit_action = file_menu.addAction("خروج")
        exit_action.triggered.connect(self.close)

        invoices_menu = menu_bar.addMenu("الفواتير")
        open_invoices_action = invoices_menu.addAction("فتح الفواتير")
        open_invoices_action.triggered.connect(self.open_invoices_window)

        menu_bar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def create_central_widget(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        self.label = QLabel("هذه هي النافذة الرئيسية")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.label)

        self.setCentralWidget(central_widget)

    def open_invoices_window(self):
        self.invoices_window = InvoicesWindow(self)
        self.invoices_window.show()


class InvoicesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("نافذة الفواتير")
        self.setGeometry(200, 200, 800, 600)

        self.initial_balance = self.load_initial_balance()
        self.invoice_items = self.load_invoice_items()
        self.selected_year = datetime.datetime.now().year
        self.create_widgets()
        self.update_invoice_list()

    def create_widgets(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)  # إضافة هوامش للنافذة
        layout.setSpacing(15)  # المسافة بين العناصر

        # شريط السنة والرصيد
        hbox_top = QHBoxLayout()
        hbox_top.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.update_balance_button = QPushButton("تحديث الرصيد")
        self.update_balance_button.setFixedWidth(100)
        self.update_balance_button.clicked.connect(self.update_initial_balance)
        hbox_top.addWidget(self.update_balance_button)

        self.initial_balance_edit = QLineEdit(str(f"{self.initial_balance:.3f}"))
        self.initial_balance_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.initial_balance_edit.setValidator(QDoubleValidator())
        self.initial_balance_edit.setFixedWidth(100)
        hbox_top.addWidget(self.initial_balance_edit)

        self.initial_balance_label = QLabel("الرصيد الافتتاحي:")
        self.initial_balance_label.setFixedWidth(100)
        self.initial_balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox_top.addWidget(self.initial_balance_label)

        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        hbox_top.addItem(spacer)

        self.year_combo = QComboBox()
        self.year_combo.setFixedWidth(150)  # زيادة العرض لاستيعاب النص الجديد
        self.populate_year_combo()
        self.year_combo.currentIndexChanged.connect(self.update_invoice_list)
        self.year_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 5px;
            }
            QComboBox::down-arrow {
                image: url(arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        hbox_top.addWidget(self.year_combo)

        self.year_label = QLabel("السنة:")
        self.year_label.setFixedWidth(50)
        self.year_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox_top.addWidget(self.year_label)

        layout.addLayout(hbox_top)

        # رصيد الصندوق
        self.cash_balance_label = QLabel("رصيد الصندوق: 0.000")
        self.cash_balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cash_balance_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.cash_balance_label)

        # شجرة الفواتير
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["الرقم", "رقم الفاتورة", "التاريخ", "البيان", "مدين", "دائن", "الرصيد"])
        self.tree.setSortingEnabled(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)  # تلوين الصفوف بالتناوب
        
        # تعيين نمط لرؤوس الأعمدة
        header_style = """
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """
        self.tree.header().setStyleSheet(header_style)
        layout.addWidget(self.tree)

        # تعيين عرض الأعمدة
        self.tree.header().resizeSection(0, 60)    # الرقم
        self.tree.header().resizeSection(1, 70)    # رقم الفاتورة
        self.tree.header().resizeSection(2, 80)    # التاريخ
        self.tree.header().resizeSection(3, 160)   # البيان
        self.tree.header().resizeSection(4, 60)    # مدين
        self.tree.header().resizeSection(5, 60)    # دائن
        self.tree.header().resizeSection(6, 60)    # الرصيد
        
        # جعل عمود البيان قابل للتمدد
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        # إضافة شريط البحث
        search_layout = QHBoxLayout()
        search_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.search_label = QLabel("بحث:")
        self.search_label.setFixedWidth(50)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ابحث في رقم الفاتورة أو الوصف...")
        self.search_edit.textChanged.connect(self.filter_invoices)
        self.search_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_edit.setFixedWidth(150)  # تحديد عرض خانة البحث
        
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_label)
        layout.addLayout(search_layout)

        # إضافة حقول البحث بالتاريخ
        date_search_layout = QHBoxLayout()
        date_search_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.show_all_button = QPushButton("عرض الكل")
        self.show_all_button.clicked.connect(self.show_all_invoices)
        self.show_all_button.setFixedWidth(80)
        date_search_layout.addWidget(self.show_all_button)

        self.search_date_button = QPushButton("بحث")
        self.search_date_button.clicked.connect(self.filter_invoices)
        self.search_date_button.setFixedWidth(80)
        date_search_layout.addWidget(self.search_date_button)

        self.date_to_edit = QDateEdit()
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_to_edit.setFixedWidth(120)
        
        date_search_layout.addWidget(self.date_to_edit)
        
        to_label = QLabel("إلى:")
        to_label.setFixedWidth(30)
        to_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_search_layout.addWidget(to_label)

        self.date_from_edit = QDateEdit()
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self.date_from_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_from_edit.setFixedWidth(120)
        
        date_search_layout.addWidget(self.date_from_edit)
        
        from_label = QLabel("من:")
        from_label.setFixedWidth(30)
        from_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_search_layout.addWidget(from_label)

        layout.addLayout(date_search_layout)

        # أزرار التصدير
        export_layout = QHBoxLayout()
        export_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        export_layout.setSpacing(10)

        self.export_excel_button = QPushButton("تصدير إلى Excel")
        self.export_excel_button.setFixedWidth(120)
        self.export_excel_button.clicked.connect(self.export_to_excel)
        export_layout.addWidget(self.export_excel_button)

        self.export_pdf_button = QPushButton("تصدير إلى PDF")
        self.export_pdf_button.setFixedWidth(120)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        export_layout.addWidget(self.export_pdf_button)

        layout.addLayout(export_layout)

        # أزرار التحكم الرئيسية
        hbox_buttons = QHBoxLayout()
        hbox_buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox_buttons.setSpacing(10)

        button_size = QSize(48, 48)

        exit_button = QPushButton()
        exit_button.setIcon(QIcon("exit.png"))
        exit_button.setIconSize(button_size)
        exit_button.setFixedSize(button_size)
        exit_button.clicked.connect(self.close)
        exit_button.setShortcut(QKeySequence("Ctrl+Q"))
        exit_button.setToolTip("خروج (Ctrl+Q)")
        hbox_buttons.addWidget(exit_button)

        delete_button = QPushButton()
        delete_button.setIcon(QIcon("delete.png"))
        delete_button.setIconSize(button_size)
        delete_button.setFixedSize(button_size)
        delete_button.clicked.connect(self.delete_invoice)
        delete_button.setShortcut(QKeySequence("Delete"))
        delete_button.setToolTip("حذف (Delete)")
        hbox_buttons.addWidget(delete_button)

        edit_button = QPushButton()
        edit_button.setIcon(QIcon("edit.png"))
        edit_button.setIconSize(button_size)
        edit_button.setFixedSize(button_size)
        edit_button.clicked.connect(self.edit_invoice)
        edit_button.setShortcut(QKeySequence("Ctrl+E"))
        edit_button.setToolTip("تعديل (Ctrl+E)")
        hbox_buttons.addWidget(edit_button)

        add_button = QPushButton()
        add_button.setIcon(QIcon("add.png"))
        add_button.setIconSize(button_size)
        add_button.setFixedSize(button_size)
        add_button.clicked.connect(self.open_add_invoice_dialog)
        add_button.setShortcut(QKeySequence("Ctrl+N"))
        add_button.setToolTip("إضافة فاتورة جديدة (Ctrl+N)")
        hbox_buttons.addWidget(add_button)

        layout.addLayout(hbox_buttons)

        self.tree.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def populate_year_combo(self):
        """تعبئة قائمة السنوات"""
        current_year = QDate.currentDate().year()
        years = [str(year) for year in range(current_year - 4, current_year + 2)]
        self.year_combo.clear()
        for year in reversed(years):  # ترتيب تنازلي للسنوات
            self.year_combo.addItem(f"السنة المالية {year}")
        
        # تحديد السنة الحالية كقيمة افتراضية
        current_year_index = years.index(str(current_year))
        self.year_combo.setCurrentIndex(len(years) - 1 - current_year_index)  # تعديل المؤشر بسبب الترتيب العكسي

    def add_invoice_item(self, invoice_number, date, description, debit, credit):
        try:
            debit = float(debit) if debit else 0.0
            credit = float(credit) if credit else 0.0
            self.invoice_items.append({"invoice_number": invoice_number, "date": date, "description": description, "debit": debit, "credit": credit})
            self.save_invoice_items()
            self.update_invoice_list()
        except ValueError as e:
            QMessageBox.critical(self, "خطأ", f"الرجاء إدخال مبلغ صحيح في خانتي مدين أو دائن. {e}")

    def update_invoice_list(self):
        """تحديث قائمة الفواتير بدون تطبيق فلترة"""
        self.tree.clear()
        current_balance = self.initial_balance
        selected_year = int(self.year_combo.currentText().split(" ")[-1])
        serial_number = 1

        filtered_invoices = []
        for invoice in self.invoice_items:
            date_str = invoice["date"]
            try:
                year = int(date_str[:4])
                if year == selected_year:
                    filtered_invoices.append(invoice)
            except ValueError:
                print(f"Invalid date format: {date_str}")
                continue

        filtered_invoices.reverse()  # لعرض البيانات الأحدث أولاً
        
        for invoice in filtered_invoices:
            debit = invoice.get("debit", 0.0)
            credit = invoice.get("credit", 0.0)
            balance_str = f"{current_balance:.3f}"
            debit_str = f"{debit:.3f}"
            credit_str = f"{credit:.3f}"

            item = QTreeWidgetItem([
                str(serial_number),
                invoice["invoice_number"],
                invoice["date"],
                invoice["description"],
                debit_str,
                credit_str,
                balance_str
            ])

            # تطبيق محاذاة للوسط لجميع الأعمدة
            for col in range(self.tree.columnCount()):
                item.setTextAlignment(col, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            self.tree.addTopLevelItem(item)
            current_balance += debit - credit
            serial_number += 1

        # تعيين محاذاة عناوين الأعمدة للوسط
        header = self.tree.header()
        for col in range(self.tree.columnCount()):
            header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cash_balance_label.setText(f"رصيد الصندوق: {current_balance:.3f}")
        self.cash_balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def open_add_invoice_dialog(self):
        dialog = AddInvoiceDialog(self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            invoice_number, date, description, debit, credit = dialog.get_data()
            self.add_invoice_item(invoice_number, date, description, debit, credit)

    def update_initial_balance(self):
        try:
            new_balance = float(self.initial_balance_edit.text())
            self.initial_balance = new_balance
            self.save_initial_balance()
            self.update_invoice_list()
            print(f"تم تحديث الرصيد الافتتاحي إلى: {self.initial_balance}")
            self.initial_balance_edit.setText(str(f"{self.initial_balance:.3f}"))
        except ValueError:
            QMessageBox.critical(self, "خطأ", "الرجاء إدخال رقم صحيح للرصيد الافتتاحي.")

    def edit_invoice(self):
        selected_item = self.tree.currentItem()
        if selected_item is None:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد فاتورة لتعديلها.")
            return

        serial_number = selected_item.text(0)
        invoice_number = selected_item.text(1)
        date = selected_item.text(2)
        description = selected_item.text(3)
        debit = selected_item.text(4)
        credit = selected_item.text(5)
        balance = selected_item.text(6)


        dialog = AddInvoiceDialog(self)
        dialog.setWindowTitle("تعديل الفاتورة")
        dialog.invoice_number_edit.setText(invoice_number)
        try:
           dialog.date_edit.setDate(QDate.fromString(date, "yyyy-MM-dd"))
        except ValueError:
           dialog.date_edit.setDate(QDate.currentDate())
        dialog.description_edit.setText(description)
        dialog.debit_edit.setText(debit)
        dialog.credit_edit.setText(credit)

        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            new_invoice_number, new_date, new_description, new_debit, new_credit = dialog.get_data()
            try:
                new_debit = float(new_debit) if new_debit else 0.0
                new_credit = float(new_credit) if new_credit else 0.0

                for i, invoice in enumerate(self.invoice_items):
                    old_debit = float(debit) if debit else 0.0
                    old_credit = float(credit) if credit else 0.0

                    if (invoice["invoice_number"] == invoice_number and
                        invoice["date"] == date and
                        invoice["description"] == description and
                        invoice["debit"] == old_debit and
                        invoice["credit"] == old_credit):

                        self.invoice_items[i] = {"invoice_number": new_invoice_number, "date": new_date, "description": new_description, "debit": new_debit, "credit": new_credit}
                        break

                self.save_invoice_items()
                self.update_invoice_list()
            except ValueError as e:
                QMessageBox.critical(self, "خطأ", f"الرجاء إدخال مبلغ صحيح في خانتي مدين أو دائن. {e}")

    def delete_invoice(self):
        selected_item = self.tree.currentItem()
        if selected_item is None:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد فاتورة لحذفها.")
            return

        serial_number = selected_item.text(0)
        invoice_number = selected_item.text(1)
        date = selected_item.text(2)
        description = selected_item.text(3)
        debit = selected_item.text(4)
        credit = selected_item.text(5)
        balance = selected_item.text(6)

        confirm = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد من أنك تريد حذف هذه الفاتورة؟",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            debit = float(debit) if debit else 0.0
            credit = float(credit) if credit else 0.0

            self.invoice_items = [
                invoice
                for invoice in self.invoice_items
                if not (
                    invoice["invoice_number"] == invoice_number
                    and invoice["date"] == date
                    and invoice["description"] == description
                    and invoice["debit"] == debit
                    and invoice["credit"] == credit
                )
            ]
            self.save_invoice_items()
            self.update_invoice_list()

    def load_initial_balance(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("initial_balance", 0.0)
        except FileNotFoundError:
            return 0.0
        except json.JSONDecodeError:
            print("خطأ في قراءة ملف البيانات. سيتم استخدام رصيد افتتاحي 0.0")
            return 0.0

    def save_initial_balance(self):
        data = self.load_data()
        data["initial_balance"] = self.initial_balance
        self.save_data(data)

    def load_invoice_items(self):
         try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("invoice_items", [])
         except FileNotFoundError:
            return []
         except json.JSONDecodeError:
            print("خطأ في قراءة ملف البيانات. سيتم تحميل قائمة فواتير فارغة")
            return []

    def save_invoice_items(self):
        data = self.load_data()
        data["invoice_items"] = self.invoice_items
        self.save_data(data)

    def load_data(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print("خطأ في قراءة ملف البيانات. سيتم إنشاء بيانات جديدة")
            return {}

    def save_data(self, data):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"خطأ في حفظ البيانات: {e}")

    def filter_invoices(self):
        search_text = self.search_edit.text().strip()
        date_from = self.date_from_edit.date().toString("yyyy-MM-dd")
        date_to = self.date_to_edit.date().toString("yyyy-MM-dd")
        
        self.tree.clear()
        current_balance = self.initial_balance
        selected_year = int(self.year_combo.currentText().split(" ")[-1])
        serial_number = 1

        filtered_invoices = []
        for invoice in self.invoice_items:
            date_str = invoice["date"]
            try:
                # التحقق من السنة
                year = int(date_str[:4])
                if year != selected_year:
                    continue

                # التحقق من نص البحث
                if search_text and search_text not in invoice["invoice_number"] and search_text not in invoice["description"]:
                    continue

                # التحقق من نطاق التاريخ
                invoice_date = QDate.fromString(date_str, "yyyy-MM-dd")
                from_date = QDate.fromString(date_from, "yyyy-MM-dd")
                to_date = QDate.fromString(date_to, "yyyy-MM-dd")
                
                if invoice_date < from_date or invoice_date > to_date:
                    continue

                filtered_invoices.append(invoice)
            except ValueError:
                print(f"تنسيق تاريخ غير صالح: {date_str}")
                continue

        filtered_invoices.reverse()  # لعرض البيانات الأحدث أولاً
        
        for invoice in filtered_invoices:
            debit = invoice.get("debit", 0.0)
            credit = invoice.get("credit", 0.0)
            balance_str = f"{current_balance:.3f}"
            debit_str = f"{debit:.3f}"
            credit_str = f"{credit:.3f}"

            item = QTreeWidgetItem([
                str(serial_number),
                invoice["invoice_number"],
                invoice["date"],
                invoice["description"],
                debit_str,
                credit_str,
                balance_str
            ])

            # تطبيق محاذاة للوسط لجميع الأعمدة
            for col in range(self.tree.columnCount()):
                item.setTextAlignment(col, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            self.tree.addTopLevelItem(item)
            current_balance += debit - credit
            serial_number += 1

        self.cash_balance_label.setText(f"رصيد الصندوق: {current_balance:.3f}")
        self.cash_balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def show_all_invoices(self):
        """عرض جميع الفواتير للسنة المحددة"""
        # إعادة تعيين حقول البحث
        self.search_edit.clear()
        
        # تعيين نطاق التاريخ للسنة كاملة
        selected_year = int(self.year_combo.currentText().split(" ")[-1])
        self.date_from_edit.setDate(QDate(selected_year, 1, 1))  # 1 يناير
        self.date_to_edit.setDate(QDate(selected_year, 12, 31))  # 31 ديسمبر
        
        # تحديث القائمة
        self.update_invoice_list()

    def export_to_excel(self):
        import xlsxwriter
        workbook = xlsxwriter.Workbook("invoices.xlsx")
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, "رقم الفاتورة")
        worksheet.write(0, 1, "التاريخ")
        worksheet.write(0, 2, "البيان")
        worksheet.write(0, 3, "مدين")
        worksheet.write(0, 4, "دائن")
        worksheet.write(0, 5, "الرصيد")
        row = 1
        for invoice in self.invoice_items:
            worksheet.write(row, 0, invoice["invoice_number"])
            worksheet.write(row, 1, invoice["date"])
            worksheet.write(row, 2, invoice["description"])
            worksheet.write(row, 3, invoice["debit"])
            worksheet.write(row, 4, invoice["credit"])
            worksheet.write(row, 5, invoice["debit"] - invoice["credit"])
            row += 1
        workbook.close()
        QMessageBox.information(self, "تم التصدير", "تم تصدير الفواتير إلى ملف Excel بنجاح.")

    def export_to_pdf(self):
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib import colors
        data = []
        data.append(["رقم الفاتورة", "التاريخ", "البيان", "مدين", "دائن", "الرصيد"])
        for invoice in self.invoice_items:
            data.append([invoice["invoice_number"], invoice["date"], invoice["description"], invoice["debit"], invoice["credit"], invoice["debit"] - invoice["credit"]])
        doc = SimpleDocTemplate("invoices.pdf", pagesize=letter)
        style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ])
        table = Table(data, style=style)
        elements = []
        elements.append(table)
        doc.build(elements)
        QMessageBox.information(self, "تم التصدير", "تم تصدير الفواتير إلى ملف PDF بنجاح.")


class AddInvoiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("إضافة فاتورة جديدة")
        self.setGeometry(300, 300, 400, 250)

        self.create_widgets()
        self.setup_shortcuts()

    def create_widgets(self):
        self.form_layout = QFormLayout(self)

        # رقم الفاتورة
        self.invoice_number_edit = QLineEdit()
        self.invoice_number_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.invoice_number_edit.setPlaceholderText("أدخل رقم الفاتورة")
        self.form_layout.addRow("رقم الفاتورة:", self.invoice_number_edit)

        # التاريخ
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_edit.setCalendarPopup(True)  # إضافة تقويم منبثق
        self.form_layout.addRow("التاريخ:", self.date_edit)

        # الوصف
        self.description_edit = QLineEdit()
        self.description_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_edit.setPlaceholderText("أدخل وصف الفاتورة")
        self.form_layout.addRow("الوصف:", self.description_edit)

        # مدين
        self.debit_edit = QLineEdit()
        self.debit_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.debit_edit.setPlaceholderText("0.000")
        self.debit_edit.setValidator(QDoubleValidator(0, 999999999, 3))
        self.form_layout.addRow("مدين:", self.debit_edit)

        # دائن
        self.credit_edit = QLineEdit()
        self.credit_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.credit_edit.setPlaceholderText("0.000")
        self.credit_edit.setValidator(QDoubleValidator(0, 999999999, 3))
        self.form_layout.addRow("دائن:", self.credit_edit)

        # أزرار
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.form_layout.addRow(self.button_box)

        # تعيين ترتيب التنقل بين الحقول
        self.setTabOrder(self.invoice_number_edit, self.date_edit)
        self.setTabOrder(self.date_edit, self.description_edit)
        self.setTabOrder(self.description_edit, self.debit_edit)
        self.setTabOrder(self.debit_edit, self.credit_edit)

    def setup_shortcuts(self):
        # اختصار للموافقة
        self.shortcut_ok = QShortcut(QKeySequence("Return"), self)
        self.shortcut_ok.activated.connect(self.validate_and_accept)
        
        # اختصار للإلغاء
        self.shortcut_cancel = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_cancel.activated.connect(self.reject)

    def validate_and_accept(self):
        # التحقق من رقم الفاتورة
        if not self.invoice_number_edit.text().strip():
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال رقم الفاتورة")
            self.invoice_number_edit.setFocus()
            return

        # التحقق من الوصف
        if not self.description_edit.text().strip():
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال وصف الفاتورة")
            self.description_edit.setFocus()
            return

        # التحقق من المبالغ
        debit = self.debit_edit.text().strip()
        credit = self.credit_edit.text().strip()
        
        if not debit and not credit:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال قيمة في خانة مدين أو دائن")
            self.debit_edit.setFocus()
            return

        if debit and credit:
            QMessageBox.warning(self, "تنبيه", "لا يمكن إدخال قيم في خانتي مدين ودائن معاً")
            self.debit_edit.setFocus()
            return

        self.accept()

    def get_data(self):
        invoice_number = self.invoice_number_edit.text()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        description = self.description_edit.text()
        debit = self.debit_edit.text()
        credit = self.credit_edit.text()
        return (invoice_number, date, description, debit, credit)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec())