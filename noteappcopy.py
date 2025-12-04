import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import tkinter.simpledialog as tk_simpledialog

from ds.stack import Stack
from ds.treenode import TreeNode
from ds.gapbuffer import GapBuffer
import ds.converter as conv

tk.simpledialog = tk_simpledialog

class NoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Greatest Of One's Notes - .goon")
        self.root.geometry("1000x600")
        
        self.undo_stack = Stack()
        self.redo_stack = Stack()
        
        self.root_node = TreeNode("Root", is_folder=False)
        self.current_node = None
        self.project_path = None
        
        self.is_modified = False
        self.project_modified = False
        
        self.gap_buffer = GapBuffer()
        self.editing_item = None
        self.edit_entry = None
        self.rename_gap_buffer = None
        self.editing_node = None
        
        self.setup_ui()
        self.bind_shortcuts()
        
    def setup_ui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="New Note", command=self.new_note)
        file_menu.add_command(label="New Child Note", command=self.new_child_note)
        file_menu.add_command(label="Save Note", command=self.save_note)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        file_menu.add_command(label="Rename", command=self.rename_item)
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Rename", command=self.rename_item)
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(toolbar, text="New Note", command=self.new_note).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="New Child Note", command=self.new_child_note).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Rename", command=self.rename_item).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Delete", command=self.delete_item).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Save Note", command=self.save_note).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Save Project", command=self.save_project).pack(side=tk.LEFT, padx=2, pady=2)
        
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
        self.tree_view.bind('<Button-3>', self.show_context_menu)
        self.tree_view.bind('<Double-Button-1>', lambda e: self.rename_item())
        
        self.context_menu = tk.Menu(self.tree_view, tearoff=0)
        self.context_menu.add_command(label="Rename", command=self.rename_item)
        self.context_menu.add_command(label="Delete", command=self.delete_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="New Note", command=self.new_note)
        self.context_menu.add_command(label="New Child Note", command=self.new_child_note)
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
        self.root.bind('<Control-Shift-s>', lambda e: self.save_project())
        self.root.bind('<F2>', lambda e: self.rename_item())
        self.root.bind('<Escape>', lambda e: self.cancel_inline_edit())
        
        
    def show_context_menu(self, event):
        item = self.tree_view.identify_row(event.y)
        if item:
            self.tree_view.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
        
    def refresh_tree(self):
        self.tree_view.delete(*self.tree_view.get_children())
        self._build_tree("", self.root_node)
    
    def _build_tree(self, parent_id, node):
        if node == self.root_node:
            # Root node - display its children
            for child in node.children:
                self._build_tree(parent_id, child)
        else:
            # All nodes are notes (no folders)
            icon = "📄"
            display = f"{icon} {node.name}"
            node.tree_id = self.tree_view.insert(parent_id, 'end', text=display, open=True)
            
            # Recursively add children
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
            
            if node:
                self.load_note(node)
    
    def load_note(self, node):
        if self.current_node and self.is_modified:
            response = messagebox.askyesnocancel("Save?", "Save changes to current note?")
            if response is True:
                self.save_note()
            elif response is None:
                return
        
        self.current_node = node
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, node.name)
        
        self.text_editor.delete('1.0', tk.END)
        self.text_editor.insert('1.0', node.content)
        
        self.gap_buffer.set_text(node.content)
        
        self.is_modified = False
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.last_saved_content = node.content
        self.status_bar.config(text=f"Loaded: {node.get_path()} [GapBuffer: {self.gap_buffer.get_gap_info()['text_length']} chars]")
    
    def new_note(self):
        """Create a new note as a sibling of the selected note, or as a root child if none selected"""
        if not self.project_path:
            messagebox.showwarning("No Project", "Please create or open a project first")
            return
        
        selection = self.tree_view.selection()
        parent_node = self.root_node
        
        if selection:
            tree_id = selection[0]
            selected_node = self.find_node_by_tree_id(tree_id)
            if selected_node and selected_node.parent:
                # Add as sibling (same parent as selected node)
                parent_node = selected_node.parent
        
        name = tk.simpledialog.askstring("New Note", "Enter note name:")
        if name:
            # Create new note (is_folder=False)
            new_note = TreeNode(name, is_folder=False, content="")
            parent_node.add_child(new_note)
            
            self.project_modified = True
            self.refresh_tree()
            self.status_bar.config(text=f"Created note: {name}")
    
    def new_child_note(self):
        """Create a new note as a child of the selected note"""
        if not self.project_path:
            messagebox.showwarning("No Project", "Please create or open a project first")
            return
        
        selection = self.tree_view.selection()
        parent_node = self.root_node
        
        if selection:
            tree_id = selection[0]
            selected_node = self.find_node_by_tree_id(tree_id)
            if selected_node:
                # Add as child of selected node
                parent_node = selected_node
        
        name = tk.simpledialog.askstring("New Child Note", "Enter note name:")
        if name:
            # Create new note (is_folder=False)
            new_note = TreeNode(name, is_folder=False, content="")
            parent_node.add_child(new_note)
            
            self.project_modified = True
            self.refresh_tree()
            self.status_bar.config(text=f"Created child note: {name} under {parent_node.name}")
    
    def delete_item(self):
        if not self.project_path:
            return
        
        selection = self.tree_view.selection()
        if selection:
            tree_id = selection[0]
            node = self.find_node_by_tree_id(tree_id)
            if node and node.parent:
                response = messagebox.askyesno("Delete", f"Delete '{node.name}'?")
                if response:
                    node.parent.remove_child(node)
                    if self.current_node == node:
                        self.current_node = None
                        self.text_editor.delete('1.0', tk.END)
                        self.title_entry.delete(0, tk.END)
                    
                    self.project_modified = True
                    self.refresh_tree()
                    self.status_bar.config(text=f"Deleted: {node.name}")
    
    def save_note(self):
        if not self.project_path:
            messagebox.showwarning("No Project", "Please create or open a project first")
            return
        
        if self.current_node:
            content = self.gap_buffer.get_text()
            self.current_node.content = content
            
            new_name = self.title_entry.get().strip()
            
            if new_name and new_name != self.current_node.name:
                self.current_node.name = new_name
                self.project_modified = True
            
            self.is_modified = False
            self.project_modified = True
            self.refresh_tree()
            
            gap_info = self.gap_buffer.get_gap_info()
            self.status_bar.config(text=f"Saved note: {self.current_node.name} [GapBuffer: {gap_info['text_length']} chars, gap size: {gap_info['gap_size']}]")
        else:
            messagebox.showwarning("No Note", "No note selected to save")
    
    def save_project(self):
        if not self.project_path:
            messagebox.showwarning("No Project", "No project to save")
            return
        
        try:
            conv.save_tree_to_my(self.project_path, self.root_node)
            self.project_modified = False
            self.status_bar.config(text=f"Project saved: {self.project_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {e}")
    
    def new_project(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".goon",
            filetypes=[("GOON files", "*.goon")],
            title="Create a new project"
        )
        if filepath:
            self.project_path = filepath
            self.root_node = TreeNode("Root", is_folder=False)
            self.current_node = None
            self.text_editor.delete('1.0', tk.END)
            self.title_entry.delete(0, tk.END)
            self.refresh_tree()
            
            # Save empty project
            conv.save_tree_to_my(self.project_path, self.root_node)
            self.project_modified = False
            
            self.status_bar.config(text=f"New project created: {filepath}")
    
    def open_project(self):
        filepath = filedialog.askopenfilename(
            initialdir="/",
            title="Select a GOON project file",
            filetypes=[("GOON files", "*.goon")]
        )
        if filepath:
            try:
                self.project_path = filepath
                self.root_node = conv.load_tree_from_my(filepath)
                self.current_node = None
                self.text_editor.delete('1.0', tk.END)
                self.title_entry.delete(0, tk.END)
                self.refresh_tree()
                self.project_modified = False
                self.status_bar.config(text=f"Project opened: {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open project: {e}")
    
    def exit_app(self):
        if self.project_modified or self.is_modified:
            response = messagebox.askyesnocancel("Save?", "Save changes before exit?")
            if response is True:
                self.save_note()
                self.save_project()
            elif response is None:
                return
        
        self.root.quit()
    
    def on_text_change(self, event):
        if self.current_node and not self.is_modified:
            self.is_modified = True
        
        current_text = self.text_editor.get('1.0', tk.END).strip()
        self.gap_buffer.set_text(current_text)
        
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
            
    def rename_item(self):
        if not self.project_path:
            messagebox.showwarning("No Project", "Please create or open a project first")
            return
            
        selection = self.tree_view.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an item to rename")
            return
        
        self.cancel_inline_edit()
        
        tree_id = selection[0]
        node = self.find_node_by_tree_id(tree_id)
        
        if not node:
            return
        
        self.editing_item = tree_id
        self.editing_node = node
        
        bbox = self.tree_view.bbox(tree_id)
        if not bbox:
            return
        
        x, y, width, height = bbox
        
        current_name = node.name
        
        self.rename_gap_buffer = GapBuffer()
        self.rename_gap_buffer.set_text(current_name)
        
        self.edit_entry = tk.Entry(self.tree_view, font=("Arial", 9))
        self.edit_entry.place(x=x + 20, y=y, width=width - 20, height=height)
        
        self.edit_entry.insert(0, current_name)
        self.edit_entry.selection_range(0, tk.END)
        self.edit_entry.focus_set()
        
        self.edit_entry.bind('<Return>', self.finish_inline_edit)
        self.edit_entry.bind('<Escape>', lambda e: self.cancel_inline_edit())
        self.edit_entry.bind('<FocusOut>', lambda e: self.finish_inline_edit(None))
        self.edit_entry.bind('<KeyRelease>', self.on_inline_edit_key)
        
        gap_info = self.rename_gap_buffer.get_gap_info()
        self.status_bar.config(text=f"Renaming with GapBuffer [Length: {gap_info['text_length']}, Gap: {gap_info['gap_size']}] - Press Enter to save, Esc to cancel")

    def on_inline_edit_key(self, event):
        if not self.edit_entry or not self.rename_gap_buffer:
            return
        
        current_text = self.edit_entry.get()
        cursor_pos = self.edit_entry.index(tk.INSERT)
        
        self.rename_gap_buffer.set_text(current_text)
        self.rename_gap_buffer.move_cursor(cursor_pos)
        
        gap_info = self.rename_gap_buffer.get_gap_info()
        self.status_bar.config(text=f"Editing: '{gap_info['text'][:30]}...' [Len: {gap_info['text_length']}, Gap: [{gap_info['gap_start']}:{gap_info['gap_end']}], Size: {gap_info['gap_size']}]")

    def finish_inline_edit(self, event):
        if not self.edit_entry or not self.editing_node:
            return
        
        new_name = self.rename_gap_buffer.get_text().strip()
        
        if new_name:
            if self.editing_node.parent:
                for sibling in self.editing_node.parent.children:
                    if sibling != self.editing_node and sibling.name == new_name:
                        messagebox.showerror("Error", f"An item with name '{new_name}' already exists!")
                        self.cancel_inline_edit()
                        return
            
            old_name = self.editing_node.name
            self.editing_node.name = new_name
            
            if self.current_node == self.editing_node:
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, new_name)
            
            self.project_modified = True
            self.status_bar.config(text=f"Renamed: '{old_name}' → '{new_name}' [GapBuffer used]")
        
        self.cancel_inline_edit()
        self.refresh_tree()

    def cancel_inline_edit(self):
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        
        self.editing_item = None
        self.editing_node = None
        self.rename_gap_buffer = None
        
        if self.status_bar.cget('text').startswith(('Editing', 'Renaming')):
            self.status_bar.config(text="Ready")
if __name__ == "__main__":
    root = tk.Tk()
    app = NoteApp(root)
    root.mainloop()