import os
import shutil
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# 尝试导入拖拽支持
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_SUPPORT = True
except ImportError:
    DRAG_SUPPORT = False

class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能文件分类整理器")
        self.root.geometry("700x600")
        
        self.folder_path = ""       # 待整理的文件夹
        self.rules = self.load_rules()  # 分类规则
        self.preview_data = []       # 预览结果 (源路径, 目标路径)
        
        # 界面组件
        self.create_widgets()
        self.update_rule_display()
    
    def create_widgets(self):
        # 选择文件夹区域
        frame_select = tk.Frame(self.root, padx=10, pady=10)
        frame_select.pack(fill=tk.X)
        
        tk.Button(frame_select, text="📂 选择文件夹", command=self.select_folder).pack(side=tk.LEFT)
        self.folder_label = tk.Label(frame_select, text="未选择文件夹", fg="gray")
        self.folder_label.pack(side=tk.LEFT, padx=10)
        
        if DRAG_SUPPORT:
            self.drop_label = tk.Label(self.root, text="✨ 也可将文件夹拖拽至此 ✨", 
                                       relief="sunken", bg="lightyellow", height=2)
            self.drop_label.pack(fill=tk.X, padx=10, pady=5)
            self.drop_label.drop_target_register(DND_FILES)
            self.drop_label.dnd_bind('<<Drop>>', self.on_drop)
        
        # 规则编辑区域
        rule_frame = tk.LabelFrame(self.root, text="分类规则设置", padx=10, pady=5)
        rule_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(rule_frame, text="规则格式：文件扩展名 -> 目标文件夹名称（多个扩展名用逗号分隔）").pack(anchor=tk.W)
        
        self.rule_text = tk.Text(rule_frame, height=8, width=80)
        self.rule_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        btn_rule_frame = tk.Frame(rule_frame)
        btn_rule_frame.pack(fill=tk.X)
        tk.Button(btn_rule_frame, text="保存规则", command=self.save_rules).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_rule_frame, text="重置默认规则", command=self.reset_rules).pack(side=tk.LEFT, padx=5)
        
        # 操作按钮区域
        action_frame = tk.Frame(self.root, padx=10, pady=5)
        action_frame.pack(fill=tk.X)
        
        self.preview_btn = tk.Button(action_frame, text="👁️ 预览分类结果", command=self.preview, bg="lightblue")
        self.preview_btn.pack(side=tk.LEFT, padx=5)
        
        self.execute_btn = tk.Button(action_frame, text="🚀 开始整理", command=self.execute, bg="lightgreen", state=tk.DISABLED)
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = tk.LabelFrame(self.root, text="运行日志", padx=10, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
    
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.folder_label.config(text=folder, fg="black")
            self.log(f"已选择文件夹：{folder}")
            self.preview_btn.config(state=tk.NORMAL)
        else:
            self.folder_path = ""
            self.folder_label.config(text="未选择文件夹", fg="gray")
    
    def on_drop(self, event):
        raw = event.data
        folder = raw.strip('{}')
        if os.path.isdir(folder):
            self.folder_path = folder
            self.folder_label.config(text=folder, fg="black")
            self.log(f"拖拽选择文件夹：{folder}")
            self.preview_btn.config(state=tk.NORMAL)
        else:
            self.log("请拖拽文件夹，不是单个文件")
    
    def load_rules(self):
        """加载规则，如果文件不存在则使用默认规则"""
        default_rules = {
            "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "文档": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
            "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "视频": [".mp4", ".avi", ".mov", ".mkv", ".flv"],
            "音频": [".mp3", ".wav", ".flac", ".aac"],
            "程序": [".exe", ".msi", ".apk", ".sh", ".bat"],
            "代码": [".py", ".java", ".c", ".cpp", ".js", ".html", ".css", ".json"]
        }
        try:
            with open("organizer_rules.json", "r", encoding="utf-8") as f:
                saved = json.load(f)
                # 简单合并：保留保存的规则，但确保格式正确
                if isinstance(saved, dict):
                    return saved
                else:
                    return default_rules
        except FileNotFoundError:
            return default_rules
    
    def save_rules(self):
        """保存用户编辑的规则"""
        content = self.rule_text.get("1.0", tk.END).strip()
        new_rules = {}
        for line in content.splitlines():
            if ':' not in line:
                continue
            folder_name, ext_str = line.split(':', 1)
            folder_name = folder_name.strip()
            exts = [e.strip() for e in ext_str.split(',') if e.strip()]
            if folder_name and exts:
                new_rules[folder_name] = exts
        if new_rules:
            self.rules = new_rules
            with open("organizer_rules.json", "w", encoding="utf-8") as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=2)
            self.log("规则已保存")
            self.update_rule_display()
        else:
            messagebox.showwarning("警告", "规则格式错误，请使用 文件夹名: .ext1, .ext2 格式")
    
    def reset_rules(self):
        """重置为默认规则"""
        self.rules = self.load_rules()  # 重新加载默认
        with open("organizer_rules.json", "w", encoding="utf-8") as f:
            json.dump(self.rules, f, ensure_ascii=False, indent=2)
        self.update_rule_display()
        self.log("已重置为默认规则")
    
    def update_rule_display(self):
        """在文本框中显示当前规则"""
        content = ""
        for folder, exts in self.rules.items():
            content += f"{folder}: {', '.join(exts)}\n"
        self.rule_text.delete("1.0", tk.END)
        self.rule_text.insert("1.0", content)
    
    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def preview(self):
        """预览分类结果（不实际移动文件）"""
        if not self.folder_path:
            messagebox.showwarning("警告", "请先选择文件夹")
            return
        
        self.preview_data = []
        self.log("========== 预览分类结果 ==========")
        
        # 扫描文件夹内所有文件（不处理子文件夹）
        files = [f for f in os.listdir(self.folder_path) 
                 if os.path.isfile(os.path.join(self.folder_path, f))]
        
        # 构建扩展名到目标文件夹的映射
        ext_to_folder = {}
        for folder, exts in self.rules.items():
            for ext in exts:
                ext_to_folder[ext.lower()] = folder
        
        # 未匹配的扩展名放到“其他”文件夹
        unmatched_count = 0
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            target_folder = ext_to_folder.get(ext, "其他")
            src = os.path.join(self.folder_path, filename)
            dst_folder = os.path.join(self.folder_path, target_folder)
            dst = os.path.join(dst_folder, filename)
            self.preview_data.append((src, dst, target_folder))
            self.log(f"{filename} → {target_folder}/")
        
        self.log(f"预览完成，共 {len(files)} 个文件。")
        self.execute_btn.config(state=tk.NORMAL)
        messagebox.showinfo("预览完成", f"共 {len(files)} 个文件，将按以上规则分类。点击「开始整理」执行移动。")
    
    def execute(self):
        """实际移动文件（使用线程防止界面卡顿）"""
        if not self.preview_data:
            messagebox.showwarning("警告", "请先点击「预览分类结果」")
            return
        
        # 确认移动
        if not messagebox.askyesno("确认", "文件将被移动到对应子文件夹中。\n此操作不可撤销，是否继续？"):
            return
        
        # 禁用按钮，显示进度条
        self.preview_btn.config(state=tk.DISABLED)
        self.execute_btn.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        self.progress.start()
        
        def move_worker():
            moved = 0
            errors = []
            # 去重待创建的目标文件夹
            target_folders = set()
            for src, dst, folder_name in self.preview_data:
                target_folders.add(os.path.dirname(dst))
            for folder in target_folders:
                os.makedirs(folder, exist_ok=True)
            
            # 执行移动
            for src, dst, folder_name in self.preview_data:
                try:
                    # 如果目标文件已存在，添加序号避免覆盖
                    counter = 1
                    original_dst = dst
                    while os.path.exists(dst):
                        name, ext = os.path.splitext(original_dst)
                        dst = f"{name}_{counter}{ext}"
                        counter += 1
                    shutil.move(src, dst)
                    self.log(f"✅ 移动成功：{os.path.basename(src)} → {folder_name}/")
                    moved += 1
                except Exception as e:
                    errors.append(f"{src}: {str(e)}")
                    self.log(f"❌ 移动失败：{os.path.basename(src)} - {str(e)}")
            
            self.root.after(0, lambda: self.finish_moving(moved, errors))
        
        threading.Thread(target=move_worker, daemon=True).start()
    
    def finish_moving(self, moved, errors):
        self.progress.stop()
        self.progress.pack_forget()
        self.log(f"========== 整理完成 ==========")
        self.log(f"成功移动 {moved} 个文件。")
        if errors:
            self.log(f"发生 {len(errors)} 个错误，请查看日志。")
        self.preview_btn.config(state=tk.NORMAL)
        self.execute_btn.config(state=tk.DISABLED)
        self.preview_data = []
        messagebox.showinfo("完成", f"整理完成！成功移动 {moved} 个文件。")

def main():
    if DRAG_SUPPORT:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = FileOrganizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()