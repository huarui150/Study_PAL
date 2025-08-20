-- 课程知识库数据库表结构

-- 课程表
CREATE TABLE IF NOT EXISTS courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    color VARCHAR(7) DEFAULT '#3498db',
    exam_ratio DECIMAL(3,2) DEFAULT 0.6,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
);

-- 学习资料表
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
);

-- 知识卡片表
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
);

-- 向量嵌入表
CREATE TABLE IF NOT EXISTS embeddings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    material_id INT NOT NULL,
    chunk_idx INT NOT NULL,
    text TEXT NOT NULL,
    vector BLOB,
    INDEX idx_material_chunk (material_id, chunk_idx),
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
);

-- 学习事件表
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
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
);
