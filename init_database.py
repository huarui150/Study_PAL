"""
数据库初始化脚本
连接远程数据库并创建课程知识库相关表
"""
import pymysql
from auth import get_db_connection

def create_tables():
    """创建课程知识库所需的表"""
    
    # SQL语句
    create_tables_sql = [
        # 课程表（关联users表）
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            weight DECIMAL(3,2) DEFAULT 1.0,
            color VARCHAR(7) DEFAULT '#3498db',
            exam_ratio DECIMAL(3,2) DEFAULT 0.6,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        
        # 学习资料表
        """
        CREATE TABLE IF NOT EXISTS materials (
            id INT PRIMARY KEY AUTO_INCREMENT,
            course_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            type ENUM('pdf', 'ppt', 'doc', 'image') NOT NULL,
            url VARCHAR(500) NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_course_id (course_id),
            INDEX idx_hash (file_hash),
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        
        # 知识卡片表
        """
        CREATE TABLE IF NOT EXISTS cards (
            id INT PRIMARY KEY AUTO_INCREMENT,
            material_id INT NOT NULL,
            summary TEXT NOT NULL,
            key_points JSON,
            terms JSON,
            examples JSON,
            quiz JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_material_id (material_id),
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        
        # 向量嵌入表
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            id INT PRIMARY KEY AUTO_INCREMENT,
            material_id INT NOT NULL,
            chunk_idx INT NOT NULL,
            text TEXT NOT NULL,
            vector LONGTEXT,
            INDEX idx_material_chunk (material_id, chunk_idx),
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        
        # 学习事件表（关联users表和courses表）
        """
        CREATE TABLE IF NOT EXISTS events (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            course_id INT,
            title VARCHAR(255) NOT NULL,
            due DATETIME NOT NULL,
            type ENUM('exam', 'ddl', 'study') NOT NULL,
            priority INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_due (user_id, due),
            INDEX idx_course_id (course_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    ]
    
    try:
        print("正在连接数据库...")
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            print("开始创建表...")
            
            for i, sql in enumerate(create_tables_sql, 1):
                table_name = ["courses", "materials", "cards", "embeddings", "events"][i-1]
                try:
                    cursor.execute(sql)
                    print(f"✅ 表 {table_name} 创建成功")
                except Exception as e:
                    print(f"❌ 表 {table_name} 创建失败: {e}")
            
            connection.commit()
            print("✅ 所有表创建完成！")
        
        connection.close()
        print("数据库连接已关闭")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    return True

def check_tables():
    """检查表是否存在"""
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print("\n当前数据库中的表:")
            existing_tables = []
            for table in tables:
                table_name = table[0]
                existing_tables.append(table_name)
                print(f"  - {table_name}")
            
            # 检查是否已有users表
            if 'users' not in existing_tables:
                print("\n⚠️  警告: 未找到users表，请确保用户注册功能正常工作")
            else:
                print("\n✅ users表存在，可以正常关联用户数据")
        
        connection.close()
        return existing_tables
        
    except Exception as e:
        print(f"❌ 检查表失败: {e}")
        return []

if __name__ == "__main__":
    print("=== 课程知识库数据库初始化 ===")
    print("目标数据库: study_pal (远程)")
    print()
    
    # 检查当前表
    print("1. 检查当前数据库表...")
    check_tables()
    
    print("\n2. 创建课程知识库表...")
    success = create_tables()
    
    if success:
        print("\n3. 再次检查表...")
        check_tables()
        print("\n🎉 数据库初始化完成！")
    else:
        print("\n❌ 数据库初始化失败！")
