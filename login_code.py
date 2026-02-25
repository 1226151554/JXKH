import random
import string
import secrets
from io import BytesIO
import pandas as pd
from database import db


def generate_random_code(length=10):
    """生成包含字母、数字和至少一位特殊字符的随机代码"""
    letters_digits = string.ascii_letters + string.digits
    special_chars = "!@#$%&*_"

    code = [
        secrets.choice(special_chars),
        *[secrets.choice(letters_digits) for _ in range(length - 1)]
    ]
    random.shuffle(code)
    return ''.join(code)


def generate_login_codes_by_role(role_count_map):
    """
    按角色生成登录码并写入数据库
    role_count_map: { role_id: 数量 }
    """
    # 清空旧登录码
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM login_no")
        conn.commit()

    for role_id, count in role_count_map.items():
        for _ in range(count):
            account = generate_random_code()
            password = generate_random_code()
            db.create_login_code(role_id, account, password)


def export_login_codes():
    """
    从数据库读取登录码并生成 Excel（内存方式）
    """
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT r.role_name, l.account, l.password
                FROM login_no l
                LEFT JOIN evaluator_role r ON l.role_id = r.id
                ORDER BY r.id
            """)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

    df = pd.DataFrame(rows, columns=columns)

    # 修改表头名称
    df.rename(columns={
        'role_name': '角色',
        'account': '账号',
        'password': '密码'
    }, inplace=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='登录码')
    output.seek(0)
    return output

