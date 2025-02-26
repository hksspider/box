import json
import os

DATA_FILE = "accounting_data.json"

def clear_invoices():
    try:
        # تحميل البيانات الحالية (إذا كانت موجودة)
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        # إذا لم يتم العثور على الملف، فلا حاجة لعمل أي شيء
        print("ملف البيانات غير موجود. لا يوجد فواتير للمسح.")
        return
    except json.JSONDecodeError:
        # إذا كان هناك خطأ في قراءة JSON، فسيتم إنشاء بيانات جديدة
        print("خطأ في قراءة ملف البيانات. سيتم إنشاء بيانات جديدة.")
        data = {}

    # مسح قائمة الفواتير
    data["invoice_items"] = []

    # حفظ البيانات المحدثة في الملف
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("تم مسح جميع الفواتير بنجاح.")
    except Exception as e:
        print(f"خطأ في حفظ البيانات: {e}")

# تشغيل الدالة لمسح الفواتير
clear_invoices()