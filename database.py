import yaml
import pymysql
from contextlib import contextmanager
import pandas as pd
import re

class Database:
    """
    数据库操作类，封装所有与 MySQL 交互的逻辑。

    功能包括：
    - 用户登录验证与日志记录
    - 部门、角色、权限管理
    - 重点工作指标（zdgz）和满意度（myd）评分管理
    - 登录码生成与清理
    - 评分结果汇总与导出
    """

    def __init__(self):
        """
        初始化数据库配置

        功能:
        - 从 config.yaml 加载 MySQL 连接参数
        """
        with open('config.yaml', 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)['database']['mysql']

    @contextmanager
    def get_connection(self):
        """
        数据库连接上下文管理器

        功能:
        - 自动建立并关闭数据库连接
        - 使用 DictCursor 返回字典格式结果
        """
        conn = pymysql.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            yield conn
        finally:
            conn.close()

    def clean_text(self, value):
        """
        清洗 Excel 中常见的不可见/特殊空白字符
        """
        if not value:
            return ""

        text = str(value)

        # 常见不可见字符 & 特殊空白
        invisible_chars = [
            '\u00A0',  # 不间断空格
            '\u200B', '\u200C', '\u200D',  # 零宽字符
            '\ufeff',  # BOM
            '\u3000',  # 全角空格
        ]

        for ch in invisible_chars:
            text = text.replace(ch, '')

        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 去掉首尾空白
        text = text.strip()

        # 合并多余空行（防止展示很“高”）
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    # ==================== 用户登录相关 ====================

    def yz_user(self, login_code):
        """
        校验登录码是否存在

        Args:
            login_code: 登录码字符串

        Returns:
            dict or None: 用户信息字典或 None
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM login_no WHERE account=%s"
                cursor.execute(sql, (login_code,))
                return cursor.fetchone()

    def set_used(self, login_code):
        """
        标记登录码为已使用

        Args:
            login_code: 登录码字符串
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "UPDATE login_no SET used=1 WHERE account=%s"
                cursor.execute(sql, (login_code,))
                conn.commit()

    def get_branch(self, login_code):
        """
        获取用户所属分支机构

        Args:
            login_code: 登录码字符串

        Returns:
            str or None: 分支机构名称或 None
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT branch FROM login_no WHERE account=%s"
                cursor.execute(sql, (login_code,))
                result = cursor.fetchone()
                return result['branch'] if result else None

    def login_rec(self, ip, login_code):
        """
        记录用户登录日志

        Args:
            ip: 客户端 IP 地址
            login_code: 登录码字符串
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO login_rec(ip, account) VALUES(%s, %s)"
                cursor.execute(sql, (ip, login_code))
                conn.commit()

    def get_user_by_login_code(self, login_code):
        """
        根据登录码获取完整用户角色信息

        Args:
            login_code: 登录码字符串

        Returns:
            dict or None: 包含登录码、角色ID、角色名、权重的字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT
                    l.account AS login_code,
                    l.role_id,
                    r.role_name,
                    r.weight
                FROM login_no l
                JOIN evaluator_role r ON l.role_id = r.id
                WHERE l.account = %s
            """, (login_code,))
            return cursor.fetchone()

    def create_login_code(self, role_id, login_code, password):
        """
        创建新的登录码

        Args:
            role_id: 角色ID
            login_code: 登录码
            password: 密码
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO login_no(role_id, account, password)
                VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (role_id, login_code, password))
            conn.commit()

    def clear_all_scores(self):
        """
        清空所有评分记录（重点工作指标 + 满意度）
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM zdgz_score")
                cursor.execute("DELETE FROM myd_score")
            conn.commit()

    def clear_login_codes(self):
        """
        清空所有登录码
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM login_no")
            conn.commit()

    # ==================== 管理员相关 ====================

    def admin_login(self, username, password):
        """
        管理员登录校验

        Args:
            username: 管理员用户名
            password: 管理员密码

        Returns:
            dict or None: 管理员信息或 None
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM admin_user WHERE username=%s AND password=%s"
                cursor.execute(sql, (username, password))
                return cursor.fetchone()

    # ==================== 部门管理 ====================

    def get_departments(self):
        """
        获取所有启用的部门列表

        Returns:
            list: 部门信息列表，按类型和ID排序
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT * FROM department
                WHERE enable = 1
                ORDER BY dept_type, id
            """)
            return cursor.fetchall()

    def add_department(self, dept_name):
        """
        新增部门

        Args:
            dept_name: 部门名称
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO department(dept_name) VALUES(%s)",
                    (dept_name,)
                )
                conn.commit()

    def delete_department(self, dept_id):
        """
        删除部门

        Args:
            dept_id: 部门ID
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM department WHERE id=%s",
                    (dept_id,)
                )
                conn.commit()

    # ==================== 角色管理 ====================

    def get_roles(self):
        """
        获取所有角色信息

        Returns:
            list: 角色信息列表，按ID排序
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM evaluator_role ORDER BY id")
            return cursor.fetchall()

    def create_role(self, role_name, zdgz_weight=0):
        """
        新增角色

        Args:
            role_name: 角色名称
            zdgz_weight: 重点工作指标权重（默认0）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evaluator_role (role_name, zdgz_weight)
                VALUES (%s, %s)
                """,
                (role_name, zdgz_weight)
            )
            conn.commit()

    # ==================== 满意度权限管理 ====================

    def get_myd_permissions(self):
        """
        获取满意度 角色-部门-权重 映射关系

        Returns:
            dict: {
                role_id: {
                    dept_id: myd_weight
                }
            }
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT role_id, dept_id, myd_weight
                FROM role_dept_permission
            """)
            rows = cursor.fetchall()

            result = {}
            for r in rows:
                role_id = r['role_id']
                dept_id = r['dept_id']
                weight = float(r['myd_weight'])

                result.setdefault(role_id, {})[dept_id] = weight

            return result

    def save_myd_permissions(self, data):
        """
        保存满意度配置：
        - 角色-部门权限
        - 角色-部门满意度权重

        前端格式：
        [
            { "role_id": 1, "dept_id": 2, "weight": 0.7 },
            { "role_id": 1, "dept_id": 5, "weight": 0.3 },
            ...
        ]
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # 按角色分组
                role_map = {}
                for item in data:
                    role_id = int(item['role_id'])
                    dept_id = int(item['dept_id'])
                    weight = float(item.get('weight', 1.0))
                    role_map.setdefault(role_id, {})[dept_id] = weight

                for role_id, dept_weights in role_map.items():
                    # 1. 删除该角色原有配置
                    cursor.execute(
                        "DELETE FROM role_dept_permission WHERE role_id=%s",
                        (role_id,)
                    )

                    # 2. 插入新的
                    for dept_id, weight in dept_weights.items():
                        cursor.execute(
                            """
                            INSERT INTO role_dept_permission (role_id, dept_id, myd_weight)
                            VALUES (%s, %s, %s)
                            """,
                            (role_id, dept_id, weight)
                        )

                conn.commit()
            except Exception:
                conn.rollback()
                raise

    # ==================== 重点工作指标管理 ====================

    def get_zdgz(self):
        """
        获取所有重点工作指标

        Returns:
            list: 重点工作指标列表，按部门和ID排序
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT id,
                       department,
                       indicator_name,
                       work_desc,
                       description,
                       evidence_path
                FROM zdgz
                ORDER BY department, id
            """)
            return cursor.fetchall()

    def clear_zdgz(self):
        """
        删除所有重点工作指标
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM zdgz")
            conn.commit()

    def get_zdgz_by_id(self, zdgz_id):
        """
        根据ID获取重点工作指标名称

        Args:
            zdgz_id: 指标ID

        Returns:
            dict or None: 包含 indicator_name 的字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(
                "SELECT indicator_name FROM zdgz WHERE id=%s",
                (zdgz_id,)
            )
            return cursor.fetchone()

    def update_zdgz_evidence(self, zdgz_id, evidence_path):
        """
        更新佐证材料文件路径

        Args:
            zdgz_id: 指标ID
            evidence_path: 相对文件路径
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE zdgz
                    SET evidence_path = %s
                    WHERE id = %s
                """, (evidence_path, zdgz_id))
            conn.commit()

    def get_zdgz_evidence_path(self, zdgz_id):
        """
        查询佐证材料文件路径

        Args:
            zdgz_id: 指标ID

        Returns:
            str or None: 文件相对路径或 None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT evidence_path
                FROM zdgz
                WHERE id = %s
            """, (zdgz_id,))
            row = cursor.fetchone()

        if not row:
            return None

        return row.get('evidence_path')

    def get_role_zdgz_permissions(self):
        """
        获取角色-部门权限映射（用于重点工作指标）

        Returns:
            dict: {role_id: [department_name, ...]}
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT role_id, department FROM role_zdgz_permission ORDER BY role_id")
            rows = cursor.fetchall()

        result = {}
        for r in rows:
            role_id = r['role_id']
            department = r['department']
            result.setdefault(role_id, []).append(department)

        return result

    def get_zdgz_departments(self):
        """
        获取所有不同的重点工作指标部门名称

        Returns:
            list: 部门名称列表，去重并排序
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT DISTINCT department
                FROM zdgz
                WHERE department IS NOT NULL
                  AND department <> ''
                ORDER BY department
            """)
            return cursor.fetchall()

    def save_role_zdgz_permissions(self, data):
        """
        保存角色-部门权限关系（重点工作指标）
        Args:
            data: [
                {
                    'role_id': int,
                    'departments': [str],
                    'zdgz_weight': float   # 存在，但此方法不处理
                }
            ]
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for item in data:
                    role_id = int(item['role_id'])
                    departments = item.get('departments', [])

                    # 删除旧权限
                    cursor.execute(
                        "DELETE FROM role_zdgz_permission WHERE role_id = %s",
                        (role_id,)
                    )

                    # 插入新权限
                    for dept in departments:
                        cursor.execute("""
                            INSERT INTO role_zdgz_permission (role_id, department)
                            VALUES (%s, %s)
                        """, (role_id, dept))

                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def update_role_zdgz_weights(self, data):
        """
        更新 evaluator_role 中的 zdgz_weight
        Args:
            data: [
                {
                    'role_id': int,
                    'zdgz_weight': float
                }
            ]
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for item in data:
                    role_id = int(item['role_id'])
                    zdgz_weight = item.get('zdgz_weight', 0)

                    cursor.execute("""
                        UPDATE evaluator_role
                        SET zdgz_weight = %s
                        WHERE id = %s
                    """, (zdgz_weight, role_id))

                conn.commit()
            except Exception:
                conn.rollback()
                raise

    # ==================== 评分保存 ====================

    def save_zdgz_score(self, login_code, role_id, zdgz_id, score):
        """
        保存重点工作指标评分

        Args:
            login_code: 登录码
            role_id: 角色ID
            zdgz_id: 指标ID
            score: 评分值
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO zdgz_score(login_code, role_id, zdgz_id, score)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    score = VALUES(score),
                    create_time = CURRENT_TIMESTAMP
            """, (login_code, role_id, zdgz_id, score))
            conn.commit()

    def save_myd_score(self, login_code, role_id, dept_id, score):
        """
        保存满意度评分

        Args:
            login_code: 登录码
            role_id: 角色ID
            dept_id: 部门ID
            score: 评分值
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO myd_score(login_code, role_id, dept_id, score)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    score = VALUES(score),
                    create_time = CURRENT_TIMESTAMP
            """, (login_code, role_id, dept_id, score))
            conn.commit()

    # ==================== 统计与汇总 ====================

    def get_login_code_stats_by_role(self):
        """
        获取登录账号统计信息（按角色）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # 全局统计
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_count,
                    SUM(CASE WHEN used = 1 THEN 1 ELSE 0 END) AS used_count
                FROM login_no
            """)
            summary = cursor.fetchone()

            # 按角色统计（JOIN evaluator_role）
            cursor.execute("""
                SELECT
                    r.id AS role_id,
                    r.role_name,
                    COUNT(l.account) AS total,
                    SUM(CASE WHEN l.used = 1 THEN 1 ELSE 0 END) AS used
                FROM evaluator_role r
                LEFT JOIN login_no l ON l.role_id = r.id
                GROUP BY r.id, r.role_name
                ORDER BY r.id
            """)
            role_stats = cursor.fetchall()

            # 各角色未使用账号列表
            cursor.execute("""
                SELECT
                    r.id AS role_id,
                    r.role_name,
                    l.account
                FROM login_no l
                JOIN evaluator_role r ON l.role_id = r.id
                WHERE l.used = 0
                ORDER BY r.id, l.account
            """)
            unused_rows = cursor.fetchall()

            # 整理未使用账号
            unused_map = {}
            for row in unused_rows:
                unused_map.setdefault(row['role_id'], []).append(row['account'])

            roles = []
            for r in role_stats:
                role_id = r['role_id']
                total = r['total'] or 0
                used = r['used'] or 0

                roles.append({
                    'role_id': role_id,
                    'role_name': r['role_name'],
                    'total': total,
                    'used': used,
                    'unused': total - used,
                    'unused_codes': unused_map.get(role_id, [])
                })

            return {
                'total_count': summary['total_count'],
                'used_count': summary['used_count'],
                'roles': roles
            }

    def get_all_zdgz_scores(self):
        """
        获取所有重点工作指标原始评分数据

        Returns:
            list: 评分详情列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT l.account AS login_code,
                       z.department AS dept_name,
                       z.indicator_name,
                       s.score
                FROM zdgz_score s
                JOIN login_no l ON s.role_id = l.role_id
                JOIN zdgz z ON s.zdgz_id = z.id
                ORDER BY l.account, z.department, z.id
            """)
            return cursor.fetchall()

    def get_all_myd_scores(self):
        """
        获取所有满意度原始评分数据

        Returns:
            list: 评分详情列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT l.account AS login_code,
                       d.dept_name,
                       s.score
                FROM myd_score s
                JOIN login_no l ON s.role_id = l.role_id
                JOIN department d ON s.dept_id = d.id
                ORDER BY l.account, d.id
            """)
            return cursor.fetchall()

    def get_zdgz_score_summary(self):
        """
        获取重点工作指标评分汇总
        - 使用 evaluator_role.zdgz_weight
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT
                    z.department AS dept_name,
                    z.id AS zdgz_id,
                    z.indicator_name,
                    z.description,
                    r.role_name,
                    r.zdgz_weight,
                    ROUND(AVG(s.score), 2) AS avg_score,
                    ROUND(AVG(s.score) * r.zdgz_weight, 4) AS weighted_score
                FROM zdgz_score s
                JOIN zdgz z ON s.zdgz_id = z.id
                JOIN evaluator_role r ON s.role_id = r.id
                GROUP BY
                    z.department,
                    z.id,
                    z.indicator_name,
                    z.description,
                    r.id,
                    r.role_name,
                    r.zdgz_weight
                ORDER BY
                    z.department,
                    z.id,
                    r.id
            """)
            return cursor.fetchall()

    def get_myd_score_summary(self):
        """
        获取满意度评分汇总（按 角色-部门 权重）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT
                    d.id           AS dept_id,
                    d.dept_name,
                    r.id           AS role_id,
                    r.role_name,

                    p.myd_weight,
                    ROUND(AVG(s.score), 2) AS avg_score,
                    ROUND(AVG(s.score) * p.myd_weight, 4) AS weighted_score
                FROM myd_score s
                JOIN department d
                    ON s.dept_id = d.id
                JOIN evaluator_role r
                    ON s.role_id = r.id
                JOIN role_dept_permission p
                    ON p.role_id = s.role_id
                   AND p.dept_id = s.dept_id
                GROUP BY
                    d.id, d.dept_name,
                    r.id, r.role_name,
                    p.myd_weight
                ORDER BY
                    d.id, r.id
            """)
            return cursor.fetchall()

    # ==================== Excel 导出 ====================

    def export_zdgz_score_excel(self):
        """
        导出重点工作指标评分汇总为 DataFrame

        Returns:
            pd.DataFrame: 适合导出到 Excel 的数据框
        """
        summary = self.get_zdgz_score_summary()

        role_columns = sorted({
            f"{row['role_name']}评价得分系数"
            for row in summary
        })

        rows = {}

        for row in summary:
            key = (row['dept_name'], row['zdgz_id'])

            if key not in rows:
                rows[key] = {
                    "部门": row['dept_name'],
                    "绩效指标": row['indicator_name'],
                    "指标含义/具体任务": row['description'],
                }
                for col in role_columns:
                    rows[key][col] = None

            col_name = f"{row['role_name']}评价得分系数"
            rows[key][col_name] = row['weighted_score']

        df = pd.DataFrame(rows.values())

        columns = ["部门", "绩效指标", "指标含义/具体任务"] + role_columns
        df = df[columns]

        return df

    def export_myd_score_excel(self):
        """
        导出满意度评分汇总为 DataFrame

        Returns:
            pd.DataFrame: 适合导出到 Excel 的数据框
        """
        summary = self.get_myd_score_summary()

        role_columns = sorted({
            f"{row['role_name']}评价得分系数"
            for row in summary
        })

        rows = {}

        for row in summary:
            dept = row['dept_name']

            if dept not in rows:
                rows[dept] = {
                    "部门": dept
                }
                for col in role_columns:
                    rows[dept][col] = None

            col_name = f"{row['role_name']}评价得分系数"
            rows[dept][col_name] = row['weighted_score']

        df = pd.DataFrame(rows.values())

        columns = ["部门"] + role_columns
        df = df[columns]

        return df


# 全局数据库实例
db = Database()