import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import shutil

from ds.stack import Stack
from ds.treenode import TreeNode
import tkinter.simpledialog as tk_simpledialog
tk.simpledialog = tk_simpledialog

class NoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Greatest Of One's Notes - .goon")
        self.root.geometry("1000x600")
        
        self.undo_stack = Stack()
        self.redo_stack = Stack()
        
        self.root_node = TreeNode("Root", is_folder=True)
        self.current_node = None
        self.project_folder = None
        
        self.current_file = None
        self.is_modified = False
        
        self.setup_ui()
        self.bind_shortcuts()
        
    def setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="New Note", command=self.new_note)
        file_menu.add_command(label="New Folder", command=self.new_folder)
        file_menu.add_command(label="Save", command=self.save_note)
        file_menu.add_command(label="Save As...", command=self.save_note_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(toolbar, text="New Note", command=self.new_note).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="New Folder", command=self.new_folder).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Delete", command=self.delete_item).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Save", command=self.save_note).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        tk.Button(toolbar, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Redo", command=self.redo).pack(side=tk.LEFT, padx=2, pady=2)
        
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(main_container, width=250)
        main_container.add(left_frame)
        
        tk.Label(left_frame, text="Notes Structure", font=("Arial", 10, "bold")).pack(pady=5)
        
        tree_scroll = tk.Scrollbar(left_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_view = ttk.Treeview(left_frame, yscrollcommand=tree_scroll.set)
        self.tree_view.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree_view.yview)
        
        self.tree_view.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        self.refresh_tree()
        
        right_frame = tk.Frame(main_container)
        main_container.add(right_frame)
        
        title_frame = tk.Frame(right_frame)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(title_frame, text="Title:").pack(side=tk.LEFT)
        self.title_entry = tk.Entry(title_frame, font=("Arial", 12))
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.title_entry.bind('<KeyRelease>', self.on_content_change)
        
        self.text_editor = tk.Text(right_frame, wrap=tk.WORD, font=("Arial", 11), undo=False)
        self.text_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text_editor.bind('<KeyRelease>', self.on_text_change)
        
        self.last_saved_content = ""
        self.typing_timer = None
        
        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def bind_shortcuts(self):
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<Control-s>', lambda e: self.save_note())
        
    def refresh_tree(self):
        self.tree_view.delete(*self.tree_view.get_children())
        self._build_tree("", self.root_node)
    
    def _build_tree(self, parent_id, node):
        if node == self.root_node:
            for child in node.children:
                self._build_tree(parent_id, child)
        else:
            icon = "📁" if node.is_folder else "📄"
            display = f"{icon} {node.name}"
            node.tree_id = self.tree_view.insert(parent_id, 'end', text=display, open=True)
            
            if node.is_folder:
                for child in node.children:
                    self._build_tree(node.tree_id, child)
    
    def find_node_by_tree_id(self, tree_id, node=None):
        if node is None:
            node = self.root_node
        
        if node.tree_id == tree_id:
            return node
        
        for child in node.children:
            result = self.find_node_by_tree_id(tree_id, child)
            if result:
                return result
        return None
    
    def on_tree_select(self, event):
        selection = self.tree_view.selection()
        if selection:
            tree_id = selection[0]
            node = self.find_node_by_tree_id(tree_id)
            
            if node and not node.is_folder:
                self.load_note(node)
    
    def load_note(self, node):
        if self.current_node and self.is_modified:
            response = messagebox.askyesnocancel("Save?", "Save changes to current note?")
            if response is True:
                self.save_note()
            elif response is None:
                return
        
        if not self.project_folder:
            return
        
        file_path = self._get_node_path(node)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            node.content = content
        else:
            node.content = ""
        
        self.current_node = node
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, node.name.replace('.goon', ''))
        self.text_editor.delete('1.0', tk.END)
        self.text_editor.insert('1.0', node.content)
        self.is_modified = False
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.last_saved_content = node.content
        self.status_bar.config(text=f"Loaded: {node.get_path()}")
    
    def new_note(self):
        if not self.project_folder:
            messagebox.showwarning("No Project", "Please create or open a project first")
            return
        
        selection = self.tree_view.selection()
        parent_node = self.root_node
        
        if selection:
            tree_id = selection[0]
            selected_node = self.find_node_by_tree_id(tree_id)
            if selected_node:
                parent_node = selected_node if selected_node.is_folder else selected_node.parent
        
        name = tk.simpledialog.askstring("New Note", "Enter note name:")
        if name:
            if not name.endswith('.goon'):
                name += '.goon'
            new_note = TreeNode(name, is_folder=False, content="")
            parent_node.add_child(new_note)
            
            file_path = self._get_node_path(new_note)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("")
            
            self.refresh_tree()
            self.status_bar.config(text=f"Created: {name}")
    
    def new_folder(self):
        if not self.project_folder:
            messagebox.showwarning("No Project", "Please create or open a project first")
            return
        
        selection = self.tree_view.selection()
        parent_node = self.root_node
        
        if selection:
            tree_id = selection[0]
            selected_node = self.find_node_by_tree_id(tree_id)
            if selected_node and selected_node.is_folder:
                parent_node = selected_node
        
        name = tk.simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            new_folder = TreeNode(name, is_folder=True)
            parent_node.add_child(new_folder)
            
            folder_path = self._get_node_path(new_folder)
            os.makedirs(folder_path, exist_ok=True)
            
            self.refresh_tree()
            self.status_bar.config(text=f"Created folder: {name}")
    
    def delete_item(self):
        if not self.project_folder:
            return
        
        selection = self.tree_view.selection()
        if selection:
            tree_id = selection[0]
            node = self.find_node_by_tree_id(tree_id)
            if node and node.parent:
                response = messagebox.askyesno("Delete", f"Delete '{node.name}'?")
                if response:
                    item_path = self._get_node_path(node)
                    try:
                        if node.is_folder:
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to delete: {e}")
                        return
                    
                    node.parent.remove_child(node)
                    if self.current_node == node:
                        self.current_node = None
                        self.text_editor.delete('1.0', tk.END)
                        self.title_entry.delete(0, tk.END)
                    self.refresh_tree()
                    self.status_bar.config(text=f"Deleted: {node.name}")
    
    def save_note(self):
        if not self.project_folder:
            messagebox.showwarning("No Project", "Please create or open a project first")
            return
        
        if self.current_node and not self.current_node.is_folder:
            content = self.text_editor.get('1.0', tk.END).strip()
            self.current_node.content = content
            
            new_name = self.title_entry.get().strip()
            if new_name and not new_name.endswith('.goon'):
                new_name += '.goon'
            
            old_path = self._get_node_path(self.current_node)
            
            if new_name and new_name != self.current_node.name:
                self.current_node.name = new_name
                new_path = self._get_node_path(self.current_node)
                try:
                    os.rename(old_path, new_path)
                    old_path = new_path
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename: {e}")
                    return
            
            try:
                with open(old_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.is_modified = False
                self.refresh_tree()
                self.status_bar.config(text=f"Saved: {self.current_node.name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
        else:
            messagebox.showwarning("No Note", "No note selected to save")
    
    def save_note_as(self):
        content = self.text_editor.get('1.0', tk.END).strip()
        if content:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".goon",
                filetypes=[("Goon files", "*.goon"), ("All files", "*.*")]
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_bar.config(text=f"Saved to: {filepath}")
    
    def new_project(self):
        folder_path = filedialog.askdirectory(title="Select folder for new project")
        if folder_path:
            self.project_folder = folder_path
            self.root_node = TreeNode("Root", is_folder=True)
            self.current_node = None
            self.text_editor.delete('1.0', tk.END)
            self.title_entry.delete(0, tk.END)
            self.refresh_tree()
            self.status_bar.config(text=f"New project: {folder_path}")
    
    def open_project(self):
        folder_path = filedialog.askdirectory(title="Select project folder")
        if folder_path:
            self.project_folder = folder_path
            self.root_node = TreeNode("Root", is_folder=True)
            self._scan_folder(folder_path, self.root_node)
            self.current_node = None
            self.text_editor.delete('1.0', tk.END)
            self.title_entry.delete(0, tk.END)
            self.refresh_tree()
            self.status_bar.config(text=f"Project opened: {folder_path}")
    
    def _scan_folder(self, folder_path, parent_node):
        try:
            items = sorted(os.listdir(folder_path))
            for item in items:
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    folder_node = TreeNode(item, is_folder=True)
                    parent_node.add_child(folder_node)
                    self._scan_folder(item_path, folder_node)
                elif item.endswith('.goon'):
                    note_node = TreeNode(item, is_folder=False)
                    parent_node.add_child(note_node)
        except Exception as e:
            self.status_bar.config(text=f"Error scanning folder: {e}")
    
    def _get_node_path(self, node):
        path_parts = []
        current = node
        while current and current != self.root_node:
            path_parts.insert(0, current.name)
            current = current.parent
        return os.path.join(self.project_folder, *path_parts)
    

    
    def on_text_change(self, event):
        if self.current_node and not self.is_modified:
            self.is_modified = True
        
        if self.typing_timer:
            self.root.after_cancel(self.typing_timer)
        
        self.typing_timer = self.root.after(500, self.save_to_undo_stack)
    
    def save_to_undo_stack(self):
        current_content = self.text_editor.get('1.0', tk.END).strip()
        
        if current_content != self.last_saved_content:
            self.undo_stack.push(self.last_saved_content)
            self.last_saved_content = current_content
            self.redo_stack.clear()
    
    def on_content_change(self, event):
        if self.current_node:
            self.is_modified = True
    
    def undo(self):
        if not self.undo_stack.is_empty():
            current_content = self.text_editor.get('1.0', tk.END).strip()
            self.redo_stack.push(current_content)
            
            previous_content = self.undo_stack.pop()
            
            self.text_editor.delete('1.0', tk.END)
            self.text_editor.insert('1.0', previous_content)
            
            self.last_saved_content = previous_content
            self.is_modified = True
            
            self.status_bar.config(text=f"Undo (Stack: {len(self.undo_stack.items)})")
        else:
            self.status_bar.config(text="Nothing to undo")
    
    def redo(self):
        if not self.redo_stack.is_empty():
            current_content = self.text_editor.get('1.0', tk.END).strip()
            self.undo_stack.push(current_content)
            
            next_content = self.redo_stack.pop()
            
            self.text_editor.delete('1.0', tk.END)
            self.text_editor.insert('1.0', next_content)
            
            self.last_saved_content = next_content
            self.is_modified = True
            
            self.status_bar.config(text=f"Redo (Stack: {len(self.redo_stack.items)})")
        else:
            self.status_bar.config(text="Nothing to redo")