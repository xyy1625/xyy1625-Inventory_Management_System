import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import os
from datetime import datetime
import winsound

# 文件路径
DATA_FILE = 'inventory.json'
ORDER_FILE = 'order_history.json'

# --- 天蓝色配色方案 ---
COLORS = {
    "primary": "#1E90FF",       # 道奇蓝(天蓝)
    "primary_light": "#87CEFA", # 浅天蓝
    "primary_dark": "#0077BE",  # 深天蓝
    "secondary": "#20B2AA",     # 浅海洋绿
    "danger": "#FF6347",        # 番茄红
    "warning": "#FFD700",       # 金色
    "info": "#4682B4",          # 钢蓝
    "light": "#F0F8FF",         # 爱丽丝蓝
    "dark": "#2F4F4F",          # 深石板灰
    "bg": "#E6F2FF",            # 淡天蓝背景
    "card": "#FFFFFF",          # 白色卡片
    "text": "#333333",          # 深灰文字
    "border": "#B0C4DE",        # 浅钢蓝边框
    "success": "#3CB371"        # 中等海洋绿
}

# --- 现代化字体 ---
FONTS = {
    "title": ("Segoe UI", 18, "bold"),
    "subtitle": ("Segoe UI", 14, "bold"),
    "normal": ("Segoe UI", 11),
    "bold": ("Segoe UI", 11, "bold"),
    "small": ("Segoe UI", 10),
    "large": ("Segoe UI", 12)
}

# --- 声音反馈 ---
def play_success_sound():
    winsound.Beep(1000, 200)

def play_error_sound():
    winsound.Beep(500, 300)

# --- 数据操作 ---
def load_inventory():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_inventory():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, ensure_ascii=False, indent=4)

def load_orders():
    if os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_orders():
    with open(ORDER_FILE, 'w', encoding='utf-8') as f:
        json.dump(order_history, f, ensure_ascii=False, indent=4)

# --- 辅助函数 ---
def calculate_total(item):
    try:
        return round(item['quantity'] * item['price'], 2)
    except:
        return 0.0

def update_status(message):
    status_var.set(message)
    root.after(5000, lambda: status_var.set("就绪"))

# --- 库存管理功能 ---
def refresh_tree(filter_keyword=None):
    for i in tree.get_children():
        tree.delete(i)

    def match_filter(item_id, item):
        if not filter_keyword:
            return True
        kw = filter_keyword.lower()
        return kw in item_id.lower() or kw in item['name'].lower()

    filtered_items = {k: v for k, v in inventory.items() if match_filter(k, v)}

    for item_id, item in filtered_items.items():
        total = calculate_total(item)
        tree.insert('', 'end', iid=item_id, 
                   values=(item_id, item['name'], item['quantity'], f"¥{item['price']:.2f}", f"¥{total:.2f}"),
                   tags=('normal_row',))

    if "__new__" not in tree.get_children():
        tree.insert('', 'end', iid="__new__", values=("000000", "", "", "", ""), tags=('placeholder',))
    
    update_status(f"已加载 {len(filtered_items)} 条商品记录")

def add_blank_row():
    if "__new__" not in tree.get_children():
        tree.insert('', 'end', iid="__new__", values=("000000", "", "", "", ""), tags=('placeholder',))
        tree.selection_set("__new__")
        tree.see("__new__")
        update_status("已添加新商品行，请双击编辑")

def on_double_click(event):
    region = tree.identify_region(event.x, event.y)
    if region != "cell":
        return

    row_id = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    col_index = int(column[1:]) - 1
    col_name = columns[col_index]

    if not row_id or col_name == "总价":
        return

    x, y, width, height = tree.bbox(row_id, column)
    value = tree.set(row_id, column)

    entry = tk.Entry(
        tree, 
        font=FONTS["normal"],
        bg=COLORS["light"],
        fg=COLORS["text"],
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightcolor=COLORS["primary"],
        highlightbackground=COLORS["border"]
    )
    entry.insert(0, value)
    if col_name == "编号" and value == "000000":
        entry.config(fg=COLORS["secondary"])
    else:
        entry.config(fg=COLORS["text"])
    entry.place(x=x, y=y, width=width, height=height)

    def on_focus_in(e):
        if col_name == "编号" and entry.get() == "000000":
            entry.delete(0, tk.END)
            entry.config(fg=COLORS["text"])

    def on_focus_out(event, row_id=row_id, col_name=col_name, col_index=col_index):
        new_value = entry.get().strip()
        if new_value == "":
            if col_name == "编号":
                new_value = "000000"
        entry.destroy()

        if row_id == "__new__":
            temp_values = list(tree.item(row_id, 'values'))
            temp_values[col_index] = new_value
            tree.item(row_id, values=temp_values)

            if temp_values[0] == "000000":
                tree.item(row_id, tags=('placeholder',))
            else:
                tree.item(row_id, tags=('normal_row',))

            if col_name == "编号" and new_value != "000000":
                if new_value in inventory:
                    messagebox.showerror("错误", "商品编号已存在")
                    tree.delete("__new__")
                    return
                try:
                    name = temp_values[1]
                    quantity = int(temp_values[2]) if temp_values[2] else 0
                    price = float(temp_values[3].replace("¥", "")) if temp_values[3] else 0.0
                    inventory[new_value] = {
                        'name': name,
                        'quantity': quantity,
                        'price': price
                    }
                    save_inventory()
                    refresh_tree(search_var.get().strip())
                    update_status(f"已添加新商品: {new_value}")
                except ValueError:
                    messagebox.showerror("错误", "数量必须为整数，价格必须为数字")
        else:
            item = inventory[row_id]
            try:
                if col_name == "名称":
                    item["name"] = new_value
                elif col_name == "数量":
                    item["quantity"] = int(new_value) if new_value else 0
                elif col_name == "价格":
                    item["price"] = float(new_value.replace("¥", "")) if new_value else 0.0
                elif col_name == "编号":
                    if new_value == "":
                        messagebox.showerror("错误", "编号不能为空")
                        refresh_tree(search_var.get().strip())
                        return
                    if new_value != row_id:
                        if new_value in inventory:
                            messagebox.showerror("错误", "商品编号已存在")
                            refresh_tree(search_var.get().strip())
                            return
                        inventory[new_value] = item
                        del inventory[row_id]
                        row_id = new_value
                inventory[row_id] = item
                save_inventory()
                refresh_tree(search_var.get().strip())
                update_status(f"已更新商品: {row_id}")
            except ValueError:
                messagebox.showerror("错误", "数量必须为整数，价格必须为数字")

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    entry.bind("<Return>", lambda e: on_focus_out(e))
    entry.focus_set()

# --- 右键菜单 ---
def show_context_menu(event):
    row_id = tree.identify_row(event.y)
    tree.selection_remove(*tree.selection())
    if row_id:
        tree.selection_set(row_id)
        right_click_menu_selected.post(event.x_root, event.y_root)
    else:
        right_click_menu_empty.post(event.x_root, event.y_root)

def delete_item():
    selected = tree.selection()
    if not selected:
        return
    item_id = selected[0]
    if item_id == "__new__":
        tree.delete(item_id)
        return
    if messagebox.askyesno("确认删除", f"确认删除 {item_id} 吗？"):
        del inventory[item_id]
        save_inventory()
        refresh_tree(search_var.get().strip())
        update_status(f"已删除商品: {item_id}")

def query_item():
    selected = tree.selection()
    if not selected:
        return
    item_id = selected[0]
    item = inventory.get(item_id)
    if item:
        total = calculate_total(item)
        messagebox.showinfo("商品信息", 
                          f"编号: {item_id}\n名称: {item['name']}\n数量: {item['quantity']}\n价格: ¥{item['price']:.2f}\n总价: ¥{total:.2f}",
                          parent=root)
    else:
        messagebox.showerror("错误", "未找到该商品", parent=root)

# --- 搜索功能 ---
def search_inventory(event=None):
    keyword = search_var.get().strip()
    refresh_tree(keyword)
    update_status(f"搜索: {keyword}" if keyword else "已重置搜索")

def clear_search():
    search_var.set("")
    refresh_tree()
    update_status("已清除搜索条件")

# --- 收银系统 ---
cart = {}

def focus_barcode_entry():
    cash_code_entry.focus_set()

def handle_barcode_input(event=None):
    code = cash_code_var.get().strip()
    if code:
        if code in inventory:
            add_to_cart(code, 1)
            play_success_sound()
        else:
            messagebox.showerror("错误", "未找到该商品", parent=root)
            play_error_sound()
        cash_code_var.set("")
        focus_barcode_entry()

def add_to_cart(code=None, qty=1):
    if code is None:
        code = cash_code_var.get().strip()
    
    if not code:
        messagebox.showwarning("提示", "请输入商品编号", parent=root)
        return
    
    if code not in inventory:
        messagebox.showerror("错误", "库存中无此商品编号", parent=root)
        return
    
    try:
        qty = int(qty)
        if qty <= 0:
            raise ValueError
    except:
        messagebox.showerror("错误", "数量必须为正整数", parent=root)
        return

    if code in cart:
        cart[code]['quantity'] += qty
    else:
        item = inventory[code]
        cart[code] = {
            'name': item['name'],
            'price': item['price'],
            'quantity': qty
        }
    refresh_cart()
    cash_code_var.set("")
    update_status(f"已添加 {qty} 件商品 {code} 到购物车")
    focus_barcode_entry()

def refresh_cart():
    for i in cart_tree.get_children():
        cart_tree.delete(i)
    total = 0.0
    for code, item in cart.items():
        subtotal = item['price'] * item['quantity']
        cart_tree.insert('', 'end', iid=code, 
                        values=(code, item['name'], item['quantity'], f"¥{item['price']:.2f}", f"¥{subtotal:.2f}"),
                        tags=('normal_row',))
        total += subtotal
    total_var.set(f"¥{total:.2f}")
    total_label.config(text=f"总金额: {total_var.get()}")

def clear_cart():
    if not cart:
        return
    if messagebox.askyesno("确认", "确定清空购物车吗？", parent=root):
        cart.clear()
        refresh_cart()
        update_status("已清空购物车")
        focus_barcode_entry()

def checkout():
    if not cart:
        messagebox.showinfo("提示", "购物车为空", parent=root)
        return
    
    # 检查库存
    out_of_stock = []
    for code, item in cart.items():
        stock_qty = inventory.get(code, {}).get('quantity', 0)
        if item['quantity'] > stock_qty:
            out_of_stock.append(f"{code} (库存: {stock_qty}, 需求: {item['quantity']})")
    
    if out_of_stock:
        messagebox.showerror("库存不足", 
                           f"以下商品库存不足:\n{', '.join(out_of_stock)}", 
                           parent=root)
        return
    
    # 计算总金额
    total_amount = round(sum(
        item['price'] * item['quantity'] 
        for item in cart.values()
    ), 2)
    
    # 扣减库存
    for code, item in cart.items():
        inventory[code]['quantity'] -= item['quantity']
    save_inventory()

    # 构建订单记录
    order = {
        'order_id': datetime.now().strftime("订单%Y%m%d%H%M%S"),
        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'items': [
            {
                'code': code,
                'name': item['name'],
                'quantity': item['quantity'],
                'price': float(item['price'])
            } 
            for code, item in cart.items()
        ],
        'total': total_amount
    }
    order_history.append(order)
    save_orders()

    # 显示收据
    receipt = f"订单号: {order['order_id']}\n时间: {order['time']}\n\n"
    receipt += "商品清单:\n"
    for item in order['items']:
        receipt += f"{item['name']} ×{item['quantity']} @¥{item['price']:.2f}\n"
    receipt += f"\n总金额: ¥{order['total']:.2f}"
    
    messagebox.showinfo("结账成功", receipt, parent=root)
    
    refresh_tree(search_var.get().strip())
    cart.clear()
    refresh_cart()
    update_status(f"结账成功，订单号: {order['order_id']}")
    focus_barcode_entry()

# --- 订单历史 ---
def show_order_history():
    history_win = tk.Toplevel(root)
    history_win.title("历史订单")
    history_win.geometry("900x600")
    history_win.configure(bg=COLORS["bg"])
    
    try:
        history_win.iconbitmap("inventory.ico")
    except:
        pass

    # 标题
    title_frame = tk.Frame(history_win, bg=COLORS["bg"])
    title_frame.pack(fill=tk.X, padx=20, pady=15)
    
    tk.Label(
        title_frame,
        text="📋 历史订单记录",
        font=FONTS["title"],
        fg=COLORS["primary"],
        bg=COLORS["bg"]
    ).pack(side=tk.LEFT)

    # 搜索框
    search_frame = tk.Frame(history_win, bg=COLORS["bg"])
    search_frame.pack(fill=tk.X, padx=20, pady=(0,15))
    
    search_var_hist = tk.StringVar()
    search_entry = ttk.Entry(
        search_frame,
        textvariable=search_var_hist,
        font=FONTS["normal"],
        style="Modern.TEntry"
    )
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
    
    def search_orders():
        keyword = search_var_hist.get().lower()
        for item in tree_orders.get_children():
            values = tree_orders.item(item, 'values')
            if keyword in values[0].lower() or keyword in values[1].lower():
                tree_orders.item(item, tags=('match',))
            else:
                tree_orders.item(item, tags=('no_match',))
    
    search_btn = ttk.Button(
        search_frame,
        text="搜索",
        style="Modern.TButton",
        command=search_orders
    )
    search_btn.pack(side=tk.LEFT, padx=(0,10))
    
    clear_btn = ttk.Button(
        search_frame,
        text="清除",
        style="Modern.TButton",
        command=lambda: [search_var_hist.set(""), search_orders()]
    )
    clear_btn.pack(side=tk.LEFT)

    # 订单表格
    card = tk.Frame(history_win, bg=COLORS["card"], bd=0, highlightthickness=0)
    card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0,20))

    columns = ("订单编号", "时间", "商品数量", "总金额")
    tree_orders = ttk.Treeview(
        card, 
        columns=columns, 
        show='headings', 
        selectmode='browse',
        style="Modern.Treeview"
    )
    
    tree_orders.heading("订单编号", text="订单编号")
    tree_orders.heading("时间", text="时间")
    tree_orders.heading("商品数量", text="商品数量")
    tree_orders.heading("总金额", text="总金额")
    
    tree_orders.column("订单编号", width=200, anchor='w')
    tree_orders.column("时间", width=180, anchor='center')
    tree_orders.column("商品数量", width=100, anchor='center')
    tree_orders.column("总金额", width=120, anchor='e')
    
    scroll_y = ttk.Scrollbar(card, orient=tk.VERTICAL, command=tree_orders.yview)
    tree_orders.configure(yscrollcommand=scroll_y.set)
    
    tree_orders.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 加载数据
    for order in order_history:
        order_id = order.get('order_id', '')
        time = order.get('time', '')
        item_count = len(order.get('items', []))
        total = order.get('total', 0.0)
        tree_orders.insert('', 'end', values=(order_id, time, item_count, f"¥{total:.2f}"))
    
    # 状态栏
    status_bar_hist = tk.Label(
        history_win,
        text=f"共 {len(order_history)} 条订单记录",
        bd=1,
        relief=tk.SUNKEN,
        anchor=tk.W,
        font=FONTS["small"],
        bg=COLORS["light"],
        fg=COLORS["text"]
    )
    status_bar_hist.pack(side=tk.BOTTOM, fill=tk.X)

# --- 测试功能 ---
def add_test_menu():
    menubar = tk.Menu(root)
    
    test_menu = tk.Menu(menubar, tearoff=0)
    test_menu.add_command(label="模拟扫码(001)", command=lambda: simulate_barcode("001"))
    test_menu.add_command(label="模拟扫码(002)", command=lambda: simulate_barcode("002"))
    test_menu.add_separator()
    test_menu.add_command(label="测试声音-成功", command=play_success_sound)
    test_menu.add_command(label="测试声音-错误", command=play_error_sound)
    menubar.add_cascade(label="测试", menu=test_menu)
    
    root.config(menu=menubar)

def simulate_barcode(code):
    cash_code_var.set(code)
    handle_barcode_input()

# --- 主窗口 ---
root = tk.Tk()
root.title("📦 智能库存与收银系统 - 天蓝风格")
root.geometry("1280x800")
root.configure(bg=COLORS["bg"])

try:
    root.iconbitmap("inventory.ico")
except:
    pass

# 自定义样式
style = ttk.Style()
style.theme_use("clam")

# 配置Treeview样式
style.configure("Modern.Treeview",
                font=FONTS["normal"],
                rowheight=32,
                background=COLORS["card"],
                fieldbackground=COLORS["card"],
                foreground=COLORS["text"],
                bordercolor=COLORS["border"],
                borderwidth=0)

style.configure("Modern.Treeview.Heading",
                font=FONTS["bold"],
                background=COLORS["primary"],
                foreground="white",
                relief="flat",
                padding=8)

style.map("Modern.Treeview",
          background=[('selected', COLORS["primary_light"])],
          foreground=[('selected', 'black')])

# 配置按钮样式
style.configure("Modern.TButton",
                font=FONTS["bold"],
                padding=8,
                relief="flat",
                background=COLORS["primary"],
                foreground="white")

style.map("Modern.TButton",
          background=[("active", COLORS["primary_light"]), 
                     ("pressed", COLORS["primary_dark"])],
          foreground=[("active", "black"), 
                     ("pressed", "white")])

# 配置输入框样式
style.configure("Modern.TEntry",
                fieldbackground=COLORS["light"],
                foreground=COLORS["text"],
                bordercolor=COLORS["border"],
                lightcolor=COLORS["primary"],
                darkcolor=COLORS["primary"],
                padding=8,
                insertcolor=COLORS["primary"])

# 配置标签样式
style.configure("Modern.TLabel",
                font=FONTS["normal"],
                background=COLORS["bg"],
                foreground=COLORS["text"])

# 配置标签页样式
style.configure("Modern.TNotebook",
                background=COLORS["bg"],
                borderwidth=0)

style.configure("Modern.TNotebook.Tab",
                font=FONTS["bold"],
                padding=[15, 5],
                background=COLORS["light"],
                foreground=COLORS["text"],
                borderwidth=0)

style.map("Modern.TNotebook.Tab",
          background=[("selected", COLORS["primary"])],
          foreground=[("selected", "white")])

# 顶栏
header = tk.Frame(root, bg=COLORS["primary"], height=60)
header.pack(fill=tk.X)

title_label = tk.Label(
    header,
    text="📦 智能库存与收银系统",
    font=FONTS["title"],
    fg="white",
    bg=COLORS["primary"],
    pady=15
)
title_label.pack(side=tk.LEFT, padx=20)

# 搜索框
search_frame = tk.Frame(header, bg=COLORS["primary"])
search_frame.pack(side=tk.LEFT, padx=20)

search_var = tk.StringVar()
search_entry = ttk.Entry(
    search_frame,
    textvariable=search_var,
    font=FONTS["normal"],
    style="Modern.TEntry",
    width=30
)
search_entry.pack(side=tk.LEFT, padx=(0,10))
search_entry.bind("<Return>", search_inventory)

search_btn = ttk.Button(
    search_frame,
    text="搜索",
    style="Modern.TButton",
    command=search_inventory
)
search_btn.pack(side=tk.LEFT, padx=(0,10))

clear_btn = ttk.Button(
    search_frame,
    text="清除",
    style="Modern.TButton",
    command=clear_search
)
clear_btn.pack(side=tk.LEFT)

# 历史订单按钮
history_btn = ttk.Button(
    header,
    text="历史订单",
    style="Modern.TButton",
    command=show_order_history
)
history_btn.pack(side=tk.RIGHT, padx=20)

# 主内容区域
main_frame = tk.Frame(root, bg=COLORS["bg"])
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

# 左侧库存面板
inventory_frame = tk.Frame(main_frame, bg=COLORS["bg"])
inventory_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,15))

# 库存标题
inventory_header = tk.Frame(inventory_frame, bg=COLORS["bg"])
inventory_header.pack(fill=tk.X, pady=(0,15))

tk.Label(
    inventory_header,
    text="库存管理",
    font=FONTS["subtitle"],
    fg=COLORS["primary"],
    bg=COLORS["bg"]
).pack(side=tk.LEFT)

# 库存表格
tree_frame = tk.Frame(inventory_frame, bg=COLORS["card"], bd=0, highlightthickness=0)
tree_frame.pack(fill=tk.BOTH, expand=True)

columns = ("编号", "名称", "数量", "单价", "总价")
tree = ttk.Treeview(
    tree_frame,
    columns=columns,
    show='headings',
    selectmode='browse',
    style="Modern.Treeview"
)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor='center', width=100)

tree.column("名称", width=180, anchor='c')
tree.column("总价", width=120, anchor='c')

scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscrollcommand=scroll_y.set)

tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

tree.tag_configure('placeholder', foreground=COLORS["secondary"], font=FONTS["small"])
tree.tag_configure('normal_row', font=FONTS["normal"])

# 右侧收银面板
cashier_frame = tk.Frame(main_frame, bg=COLORS["bg"], width=400)
cashier_frame.pack(side=tk.RIGHT, fill=tk.Y)

# 收银标题
cashier_header = tk.Frame(cashier_frame, bg=COLORS["bg"])
cashier_header.pack(fill=tk.X, pady=(0,15))

tk.Label(
    cashier_header,
    text="收银系统",
    font=FONTS["subtitle"],
    fg=COLORS["primary"],
    bg=COLORS["bg"]
).pack(side=tk.LEFT)

# 收银表单
form_card = tk.Frame(cashier_frame, bg=COLORS["card"], padx=15, pady=15)
form_card.pack(fill=tk.X)

tk.Label(
    form_card,
    text="商品编号:",
    font=FONTS["bold"],
    fg=COLORS["text"],
    bg=COLORS["card"],
    anchor='w'
).pack(fill=tk.X, pady=(0,5))

cash_code_var = tk.StringVar()
cash_code_entry = ttk.Entry(
    form_card,
    textvariable=cash_code_var,
    font=FONTS["normal"],
    style="Modern.TEntry"
)
cash_code_entry.pack(fill=tk.X, pady=(0,15))
cash_code_entry.bind("<Return>", handle_barcode_input)

add_cart_btn = ttk.Button(
    form_card,
    text="加入购物车 (数量:1)",
    style="Modern.TButton",
    command=lambda: add_to_cart(qty=1)
)
add_cart_btn.pack(fill=tk.X, pady=(0,15))

# 购物车标题
cart_header = tk.Frame(cashier_frame, bg=COLORS["bg"])
cart_header.pack(fill=tk.X, pady=(15,5))

tk.Label(
    cart_header,
    text="购物车",
    font=FONTS["bold"],
    fg=COLORS["primary"],
    bg=COLORS["bg"]
).pack(side=tk.LEFT)

clear_cart_btn = ttk.Button(
    cart_header,
    text="清空",
    style="Modern.TButton",
    command=clear_cart
)
clear_cart_btn.pack(side=tk.RIGHT)

# 购物车表格
cart_tree_frame = tk.Frame(cashier_frame, bg=COLORS["card"], bd=0, highlightthickness=0)
cart_tree_frame.pack(fill=tk.BOTH, expand=True)

cart_columns = ("编号", "名称", "数量", "单价", "小计")
cart_tree = ttk.Treeview(
    cart_tree_frame,
    columns=cart_columns,
    show="headings",
    height=8,
    selectmode='browse',
    style="Modern.Treeview"
)

for col in cart_columns:
    cart_tree.heading(col, text=col)
    cart_tree.column(col, anchor='center', width=80)

cart_tree.column("名称", width=120, anchor='w')
cart_tree.column("小计", width=90, anchor='e')

scroll_y = ttk.Scrollbar(cart_tree_frame, orient=tk.VERTICAL, command=cart_tree.yview)
cart_tree.configure(yscrollcommand=scroll_y.set)

cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

cart_tree.tag_configure('normal_row', font=FONTS["normal"])

# 总金额
total_frame = tk.Frame(cashier_frame, bg=COLORS["card"], pady=15)
total_frame.pack(fill=tk.X)

total_var = tk.StringVar(value="¥0.00")
total_label = tk.Label(
    total_frame,
    textvariable=total_var,
    font=FONTS["large"],
    fg=COLORS["primary"],
    bg=COLORS["card"],
    anchor='e'
)
total_label.pack(fill=tk.X)

# 结账按钮
checkout_btn = ttk.Button(
    cashier_frame,
    text="结账",
    style="Modern.TButton",
    command=checkout
)
checkout_btn.pack(fill=tk.X, pady=(15,0))

# 右键菜单
right_click_menu_selected = tk.Menu(root, tearoff=0, font=FONTS["small"])
right_click_menu_selected.add_command(label="查询商品", command=query_item)
right_click_menu_selected.add_command(label="删除商品", command=delete_item)
right_click_menu_selected.add_separator()
right_click_menu_selected.add_command(label="添加到购物车(1个)", command=lambda: add_to_cart(tree.selection()[0], 1))
right_click_menu_selected.add_command(label="添加到购物车(2个)", command=lambda: add_to_cart(tree.selection()[0], 2))
right_click_menu_selected.add_command(label="添加到购物车(5个)", command=lambda: add_to_cart(tree.selection()[0], 5))

right_click_menu_empty = tk.Menu(root, tearoff=0, font=FONTS["small"])
right_click_menu_empty.add_command(label="添加商品", command=add_blank_row)

tree.bind("<Double-1>", on_double_click)
tree.bind("<Button-3>", show_context_menu)

# 状态栏
status_frame = tk.Frame(root, bg=COLORS["primary_light"], height=30)
status_frame.pack(fill=tk.X, side=tk.BOTTOM)

status_var = tk.StringVar(value="系统就绪")
status_label = tk.Label(
    status_frame,
    textvariable=status_var,
    bd=0,
    relief=tk.FLAT,
    anchor=tk.W,
    font=FONTS["small"],
    bg=COLORS["primary_light"],
    fg=COLORS["dark"]
)
status_label.pack(fill=tk.X, padx=10)

# 初始化数据
inventory = load_inventory()
order_history = load_orders()

refresh_tree()
add_blank_row()

# 添加测试菜单
add_test_menu()

# 启动时自动聚焦
focus_barcode_entry()

# 启动主循环
root.mainloop()
