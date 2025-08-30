import os

def merge_chapters(input_folder, output_file):
    merged_content = []
    chapter_files = []

    # 遍历输入文件夹，收集所有txt文件
    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            try:
                # 提取文件名中的数字作为章节号
                chapter_num = int(filename.replace('chapter_', '').replace('.txt', ''))
                chapter_files.append((chapter_num, filename))
            except ValueError:
                # 忽略不符合命名规范的文件
                continue

    # 按章节号排序文件
    chapter_files.sort()

    for i, (chapter_num, filename) in enumerate(chapter_files):
        file_path = os.path.join(input_folder, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 添加章节标题
            merged_content.append(f"第{chapter_num}章\n")
            merged_content.append(content)
            merged_content.append("\n\n") # 在章节之间添加空行以便阅读

    # 将合并后的内容写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(merged_content))

    print(f"所有章节已成功合并到 {output_file}")

if __name__ == "__main__":
    input_folder = 'Novel_Output/chapters'
    output_file = 'Novel_Output/merged_novel.txt'
    merge_chapters(input_folder, output_file)