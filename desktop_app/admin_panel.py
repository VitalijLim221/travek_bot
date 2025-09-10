# desktop_app/admin_panel.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys

# Add parent directory to path to import database module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bot.database import (
    get_all_users, get_shop_items, add_shop_item,
    update_shop_item, delete_shop_item
)


class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Панель администратора")
        self.root.geometry("1000x700")

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self.users_tab = ttk.Frame(self.notebook)
        self.shop_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.users_tab, text="Пользователи")
        self.notebook.add(self.shop_tab, text="Магазин")

        # Initialize tabs
        self.setup_users_tab()
        self.setup_shop_tab()

        # Load initial data
        self.load_users()
        self.load_shop_items()

    def setup_users_tab(self):
        # Users frame
        users_frame = ttk.Frame(self.users_tab)
        users_frame.pack(fill=tk.BOTH, expand=True)

        # Users treeview
        columns = ("ID", "Telegram ID", "Имя", "Телефон", "Баллы", "Интересы")
        self.users_tree = ttk.Treeview(users_frame, columns=columns, show="headings")

        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(users_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        h_scrollbar = ttk.Scrollbar(users_frame, orient=tk.HORIZONTAL, command=self.users_tree.xview)
        self.users_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack elements
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Refresh button
        refresh_btn = ttk.Button(self.users_tab, text="Обновить", command=self.load_users)
        refresh_btn.pack(pady=10)

    def setup_shop_tab(self):
        # Shop frame
        shop_frame = ttk.Frame(self.shop_tab)
        shop_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Shop items list
        items_frame = ttk.LabelFrame(shop_frame, text="Товары")
        items_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 10))

        columns = ("ID", "Название", "Цена", "Категория", "Активен")
        self.shop_tree = ttk.Treeview(items_frame, columns=columns, show="headings")

        for col in columns:
            self.shop_tree.heading(col, text=col)
            self.shop_tree.column(col, width=100)

        self.shop_tree.pack(fill=tk.BOTH, expand=True)
        self.shop_tree.bind("<<TreeviewSelect>>", self.on_shop_select)

        # Item details frame
        details_frame = ttk.LabelFrame(shop_frame, text="Детали товара")
        details_frame.pack(fill=tk.Y, side=tk.RIGHT, padx=(10, 0))

        # Form fields
        ttk.Label(details_frame, text="Название:").pack(anchor=tk.W, pady=(5, 0))
        self.name_entry = ttk.Entry(details_frame, width=30)
        self.name_entry.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(details_frame, text="Описание:").pack(anchor=tk.W, pady=(5, 0))
        self.desc_text = tk.Text(details_frame, width=30, height=5)
        self.desc_text.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(details_frame, text="Цена:").pack(anchor=tk.W, pady=(5, 0))
        self.price_entry = ttk.Entry(details_frame, width=30)
        self.price_entry.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(details_frame, text="Категория:").pack(anchor=tk.W, pady=(5, 0))
        self.category_entry = ttk.Entry(details_frame, width=30)
        self.category_entry.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(details_frame, text="URL изображения:").pack(anchor=tk.W, pady=(5, 0))
        self.image_entry = ttk.Entry(details_frame, width=30)
        self.image_entry.pack(fill=tk.X, pady=(0, 5))

        self.active_var = tk.BooleanVar()
        self.active_check = ttk.Checkbutton(details_frame, text="Активен", variable=self.active_var)
        self.active_check.pack(anchor=tk.W, pady=(5, 10))

        # Buttons
        buttons_frame = ttk.Frame(details_frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        self.add_btn = ttk.Button(buttons_frame, text="Добавить", command=self.add_shop_item)
        self.add_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.update_btn = ttk.Button(buttons_frame, text="Обновить", command=self.update_shop_item, state=tk.DISABLED)
        self.update_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_btn = ttk.Button(buttons_frame, text="Удалить", command=self.delete_shop_item, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_btn = ttk.Button(buttons_frame, text="Очистить", command=self.clear_form)
        self.clear_btn.pack(side=tk.LEFT)

        # Refresh button
        refresh_btn = ttk.Button(self.shop_tab, text="Обновить", command=self.load_shop_items)
        refresh_btn.pack(pady=10)

    def load_users(self):
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        # Load users
        users = get_all_users()
        for user in users:
            self.users_tree.insert("", tk.END, values=(
                user[0], user[1], user[2], user[3], user[4], user[5]
            ))

    def load_shop_items(self):
        # Clear existing items
        for item in self.shop_tree.get_children():
            self.shop_tree.delete(item)

        # Load shop items
        items = get_shop_items(active_only=False)
        for item in items:
            self.shop_tree.insert("", tk.END, values=(
                item[0], item[1], item[3], item[4], "Да" if item[6] else "Нет"
            ))

    def on_shop_select(self, event):
        selection = self.shop_tree.selection()
        if selection:
            item = self.shop_tree.item(selection[0])
            values = item['values']

            # Enable buttons
            self.update_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL)

            # Load item data
            items = get_shop_items(active_only=False)
            for shop_item in items:
                if shop_item[0] == values[0]:
                    self.name_entry.delete(0, tk.END)
                    self.name_entry.insert(0, shop_item[1])

                    self.desc_text.delete(1.0, tk.END)
                    self.desc_text.insert(1.0, shop_item[2] or "")

                    self.price_entry.delete(0, tk.END)
                    self.price_entry.insert(0, str(shop_item[3]))

                    self.category_entry.delete(0, tk.END)
                    self.category_entry.insert(0, shop_item[4] or "")

                    self.image_entry.delete(0, tk.END)
                    self.image_entry.insert(0, shop_item[5] or "")

                    self.active_var.set(bool(shop_item[6]))
                    break

    def add_shop_item(self):
        try:
            name = self.name_entry.get()
            description = self.desc_text.get(1.0, tk.END).strip()
            price = int(self.price_entry.get())
            category = self.category_entry.get()
            image_url = self.image_entry.get() or None
            is_active = self.active_var.get()

            if not name or not price:
                messagebox.showerror("Ошибка", "Заполните обязательные поля (название и цена)")
                return

            add_shop_item(name, description, price, category, image_url)
            messagebox.showinfo("Успех", "Товар добавлен")
            self.load_shop_items()
            self.clear_form()
        except ValueError:
            messagebox.showerror("Ошибка", "Цена должна быть числом")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить товар: {str(e)}")

    def update_shop_item(self):
        try:
            selection = self.shop_tree.selection()
            if not selection:
                return

            item = self.shop_tree.item(selection[0])
            item_id = item['values'][0]

            name = self.name_entry.get()
            description = self.desc_text.get(1.0, tk.END).strip()
            price = int(self.price_entry.get())
            category = self.category_entry.get()
            image_url = self.image_entry.get() or None
            is_active = self.active_var.get()

            if not name or not price:
                messagebox.showerror("Ошибка", "Заполните обязательные поля (название и цена)")
                return

            update_shop_item(item_id, name, description, price, category, image_url, is_active)
            messagebox.showinfo("Успех", "Товар обновлен")
            self.load_shop_items()
        except ValueError:
            messagebox.showerror("Ошибка", "Цена должна быть числом")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить товар: {str(e)}")

    def delete_shop_item(self):
        try:
            selection = self.shop_tree.selection()
            if not selection:
                return

            if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот товар?"):
                item = self.shop_tree.item(selection[0])
                item_id = item['values'][0]

                delete_shop_item(item_id)
                messagebox.showinfo("Успех", "Товар удален")
                self.load_shop_items()
                self.clear_form()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить товар: {str(e)}")

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.desc_text.delete(1.0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.image_entry.delete(0, tk.END)
        self.active_var.set(True)

        self.update_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = AdminPanel(root)
    root.mainloop()


if __name__ == "__main__":
    main()