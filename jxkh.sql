/*
 Navicat Premium Dump SQL

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 80041 (8.0.41)
 Source Host           : localhost:3306
 Source Schema         : jxkh

 Target Server Type    : MySQL
 Target Server Version : 80041 (8.0.41)
 File Encoding         : 65001

 Date: 15/01/2026 16:32:29
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for admin_user
-- ----------------------------
DROP TABLE IF EXISTS `admin_user`;
CREATE TABLE `admin_user`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户名',
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '管理员表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of admin_user
-- ----------------------------
INSERT INTO `admin_user` VALUES (1, 'admin', 'admin123');

-- ----------------------------
-- Table structure for department
-- ----------------------------
DROP TABLE IF EXISTS `department`;
CREATE TABLE `department`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `dept_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '部门名称',
  `dept_type` enum('front','middle') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '部门类型，‘front=前台，middle=中后台’',
  `enable` tinyint(1) NOT NULL COMMENT '是否启用',
  `work_desc` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '部门工作完成情况说明（300-1000字）',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '部门表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of department
-- ----------------------------
INSERT INTO `department` VALUES (1, '纪委办公室', 'middle', 1, NULL);
INSERT INTO `department` VALUES (2, '内控保卫部', 'middle', 1, NULL);
INSERT INTO `department` VALUES (3, '党群工作部', 'middle', 1, NULL);
INSERT INTO `department` VALUES (4, '财务运营部', 'middle', 1, NULL);
INSERT INTO `department` VALUES (5, '风险管理部', 'middle', 1, NULL);
INSERT INTO `department` VALUES (6, '行政事业机构部', 'front', 1, '');
INSERT INTO `department` VALUES (7, '普惠金融事业部', 'front', 1, '');
INSERT INTO `department` VALUES (8, '交易银行部', 'front', 1, '');
INSERT INTO `department` VALUES (9, '个人金融部', 'front', 1, NULL);
INSERT INTO `department` VALUES (10, '公司金融部', 'front', 1, NULL);

-- ----------------------------
-- Table structure for evaluator_role
-- ----------------------------
DROP TABLE IF EXISTS `evaluator_role`;
CREATE TABLE `evaluator_role`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `role_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色名称',
  `myd_weight` decimal(5, 2) NOT NULL DEFAULT 1.00 COMMENT '满意度权重',
  `zdgz_weight` decimal(5, 2) NOT NULL DEFAULT 1.00 COMMENT '重点工作指标权重',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_role_name`(`role_name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '打分角色表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of evaluator_role
-- ----------------------------

-- ----------------------------
-- Table structure for login_no
-- ----------------------------
DROP TABLE IF EXISTS `login_no`;
CREATE TABLE `login_no`  (
  `role_id` int NOT NULL COMMENT '角色ID',
  `account` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '账号',
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码',
  `used` int NULL DEFAULT 0 COMMENT '是否已使用'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '匿名账号信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of login_no
-- ----------------------------

-- ----------------------------
-- Table structure for login_rec
-- ----------------------------
DROP TABLE IF EXISTS `login_rec`;
CREATE TABLE `login_rec`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `account` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `login_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of login_rec
-- ----------------------------

-- ----------------------------
-- Table structure for myd_score
-- ----------------------------
DROP TABLE IF EXISTS `myd_score`;
CREATE TABLE `myd_score`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键',
  `role_id` int NOT NULL COMMENT '评分角色ID',
  `login_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `dept_id` int NOT NULL COMMENT '被评价部门ID',
  `score` decimal(5, 2) NOT NULL COMMENT '评分',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评分时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_login_role_dept`(`login_code` ASC, `role_id` ASC, `dept_id` ASC) USING BTREE,
  INDEX `idx_role`(`role_id` ASC) USING BTREE,
  INDEX `idx_dept`(`dept_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '部门满意度评分表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of myd_score
-- ----------------------------

-- ----------------------------
-- Table structure for role_dept_permission
-- ----------------------------
DROP TABLE IF EXISTS `role_dept_permission`;
CREATE TABLE `role_dept_permission`  (
  `role_id` int NOT NULL COMMENT '角色ID',
  `dept_id` int NOT NULL COMMENT '\r\n部门ID',
  PRIMARY KEY (`role_id`, `dept_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '角色-部门关系表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of role_dept_permission
-- ----------------------------

-- ----------------------------
-- Table structure for role_zdgz_permission
-- ----------------------------
DROP TABLE IF EXISTS `role_zdgz_permission`;
CREATE TABLE `role_zdgz_permission`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键',
  `role_id` int NOT NULL COMMENT '角色ID',
  `department` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '部门名称（对应 zdgz.department）',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_role_department`(`role_id` ASC, `department` ASC) USING BTREE,
  INDEX `idx_role_id`(`role_id` ASC) USING BTREE,
  INDEX `idx_department`(`department` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '角色-重点工作指标关系表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of role_zdgz_permission
-- ----------------------------

-- ----------------------------
-- Table structure for zdgz
-- ----------------------------
DROP TABLE IF EXISTS `zdgz`;
CREATE TABLE `zdgz`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键',
  `department` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '部门',
  `indicator_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '绩效指标名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '指标含义',
  `work_desc` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '工作完成情况（300-1000字）',
  `is_enabled` tinyint NULL DEFAULT 1 COMMENT '是否启用 1=启用 0=停用',
  `sort_order` int NULL DEFAULT 0 COMMENT '排序号',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `evidence_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '佐证材料相对路径',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 101 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '重点工作指标信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of zdgz
-- ----------------------------

-- ----------------------------
-- Table structure for zdgz_score
-- ----------------------------
DROP TABLE IF EXISTS `zdgz_score`;
CREATE TABLE `zdgz_score`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键',
  `role_id` int NOT NULL COMMENT '评分角色ID',
  `login_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '登录码',
  `zdgz_id` int NOT NULL COMMENT '重点工作指标ID',
  `score` decimal(5, 2) NOT NULL COMMENT '评分',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评分时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_login_role_zdgz`(`login_code` ASC, `role_id` ASC, `zdgz_id` ASC) USING BTREE,
  INDEX `idx_role`(`role_id` ASC) USING BTREE,
  INDEX `idx_zdgz`(`zdgz_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 26 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '重点工作指标评分表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of zdgz_score
-- ----------------------------

SET FOREIGN_KEY_CHECKS = 1;
