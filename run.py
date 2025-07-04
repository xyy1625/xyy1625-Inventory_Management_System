import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import os
from datetime import datetime

DATA_FILE = 'inventory.json'
ORDER_FILE = 'order_history.json'

# --- 颜色和样式配置 ---
COLORS = {
    "primary": "#4e73df",
    "secondary": "#858796",
    "success": "#1cc88a",
    "info": "#36b9cc",
    "warning": "#f6c23e",
    "danger": "#e74a3b",
    "light": "#f8f9fc",
    "dark": "#5a5c69",
    "bg": "#f5f7fa",
    "card": "#ffffff",
    "text": "#3a3b45",
    "border": "#dddfeb"
}

FONTS = {
    "title": ("Microsoft YaHei", 16, "bold"),
    "subtitle": ("Segoe UI", 14, "bold"),
    "normal": ("Segoe UI", 10),
    "bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9)
}

# --- 数据加载保存 ---
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

# --- 计算总价 ---
def calculate_total(item):
    try:
        return round(item['quantity'] * item['price'], 2)
    except:
        return 0.0

# --- 刷新库存列表 ---
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
        tree.insert('', 'end', iid=item_id, values=(item_id, item['name'], item['quantity'], item['price'], total))

    if "__new__" not in tree.get_children():
        tree.insert('', 'end', iid="__new__", values=("000000", "", "", "", ""))
        tree.item("__new__", tags=("placeholder",))
    
    update_status(f"已加载 {len(filtered_items)} 条商品记录")

# --- 新增空白行 ---
def add_blank_row():
    if "__new__" not in tree.get_children():
        tree.insert('', 'end', iid="__new__", values=("000000", "", "", "", ""))
        tree.selection_set("__new__")
        tree.see("__new__")
        update_status("已添加新商品行，请双击编辑")

# --- 双击编辑 ---
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
        borderwidth=1,
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
                tree.item(row_id, tags=("placeholder",))
            else:
                tree.item(row_id, tags=())

            if col_name == "编号" and new_value != "000000":
                if new_value in inventory:
                    messagebox.showerror("错误", "商品编号已存在")
                    tree.delete("__new__")
                    return
                try:
                    name = temp_values[1]
                    quantity = int(temp_values[2]) if temp_values[2] else 0
                    price = float(temp_values[3]) if temp_values[3] else 0.0
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
                    item["price"] = float(new_value) if new_value else 0.0
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
                          f"编号: {item_id}\n名称: {item['name']}\n数量: {item['quantity']}\n价格: {item['price']}\n总价: {total}",
                          parent=root)
    else:
        messagebox.showerror("错误", "未找到该商品", parent=root)

# --- 搜索 ---
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

def add_to_cart():
    code = cash_code_var.get().strip()
    qty_text = cash_qty_var.get().strip()
    if not code:
        messagebox.showwarning("提示", "请输入商品编号", parent=root)
        return
    if code not in inventory:
        messagebox.showerror("错误", "库存中无此商品编号", parent=root)
        return
    try:
        qty = int(qty_text)
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
    cash_qty_var.set("")
    update_status(f"已添加 {qty} 件商品 {code} 到购物车")

def refresh_cart():
    for i in cart_tree.get_children():
        cart_tree.delete(i)
    total = 0.0
    for code, item in cart.items():
        subtotal = item['price'] * item['quantity']
        cart_tree.insert('', 'end', iid=code, values=(code, item['name'], item['quantity'], item['price'], f"{subtotal:.2f}"))
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
    
    # 计算总金额（直接从购物车计算，避免依赖界面变量）
    total_amount = round(sum(
        item['price'] * item['quantity'] 
        for item in cart.values()
    ), 2)
    
    # 扣减库存
    for code, item in cart.items():
        inventory[code]['quantity'] -= item['quantity']
    save_inventory()

    # 构建完整订单记录
    order = {
        'order_id': datetime.now().strftime("订单%Y%m%d%H%M%S"),
        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'items': [
            {
                'code': code,
                'name': item['name'],
                'quantity': item['quantity'],
                'price': float(item['price'])  # 确保是浮点数
            } 
            for code, item in cart.items()
        ],
        'total': total_amount  # 使用计算出的总金额
    }
    order_history.append(order)
    save_orders()

    # 显示收据（使用计算出的金额，而非界面变量）
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

# --- 订单历史窗口 ---
def show_order_history():
    history_win = tk.Toplevel(root)
    history_win.title("历史订单")
    history_win.geometry("900x500")
    history_win.configure(bg=COLORS["bg"])
    
    try:
        history_win.iconbitmap("inventory.ico")
    except:
        pass

    # 标题
    title_frame = tk.Frame(history_win, bg=COLORS["bg"])
    title_frame.pack(fill=tk.X, padx=15, pady=10)
    
    tk.Label(
        title_frame,
        text="历史订单记录",
        font=FONTS["title"],
        fg=COLORS["primary"],
        bg=COLORS["bg"]
    ).pack(side=tk.LEFT)
    
    # 搜索框
    search_frame = tk.Frame(history_win, bg=COLORS["bg"])
    search_frame.pack(fill=tk.X, padx=15, pady=(0,10))
    
    search_var_hist = tk.StringVar()
    search_entry_hist = tk.Entry(
        search_frame,
        textvariable=search_var_hist,
        font=FONTS["normal"],
        bg=COLORS["light"],
        relief="flat",
        highlightthickness=1,
        highlightcolor=COLORS["primary"],
        highlightbackground=COLORS["border"]
    )
    search_entry_hist.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
    
    def search_orders():
        keyword = search_var_hist.get().lower()
        for item in tree_orders.get_children():
            values = tree_orders.item(item, 'values')
            if keyword in values[0].lower() or keyword in values[1].lower():
                tree_orders.item(item, tags=('match',))
                tree_orders.selection_set(item)
            else:
                tree_orders.item(item, tags=('no_match',))
        tree_orders.tag_configure('match', background='#e6f7ff')
        tree_orders.tag_configure('no_match', background=COLORS["card"])
    
    search_btn_hist = tk.Button(
        search_frame,
        text="搜索",
        font=FONTS["bold"],
        bg=COLORS["primary"],
        fg="white",
        activebackground=COLORS["dark"],
        command=search_orders
    )
    search_btn_hist.pack(side=tk.LEFT, padx=(0,5))
    
    clear_btn_hist = tk.Button(
        search_frame,
        text="清除",
        font=FONTS["bold"],
        bg=COLORS["secondary"],
        fg="white",
        activebackground=COLORS["dark"],
        command=lambda: [search_var_hist.set(""), search_orders()]
    )
    clear_btn_hist.pack(side=tk.LEFT)
    
    # 订单表格
    card = tk.Frame(history_win, bg=COLORS["card"], bd=0, highlightthickness=0)
    card.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,15))
    
    columns = ("订单编号", "时间", "商品数量", "总金额")
    tree_orders = ttk.Treeview(card, columns=columns, show='headings', selectmode='browse')
    
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
    
    # 双击查看详情
    def show_order_details(event):
        selected = tree_orders.selection()
        if not selected:
            return
        item = tree_orders.item(selected[0])
        order_id = item['values'][0]
        
        for order in order_history:
            if order.get('order_id') == order_id:
                details_win = tk.Toplevel(history_win)
                details_win.title(f"订单详情 - {order_id}")
                details_win.geometry("600x400")
                details_win.configure(bg=COLORS["bg"])
                
                try:
                    details_win.iconbitmap("inventory.ico")
                except:
                    pass
                
                # 标题
                tk.Label(
                    details_win,
                    text=f"订单详情 - {order_id}",
                    font=FONTS["subtitle"],
                    fg=COLORS["primary"],
                    bg=COLORS["bg"],
                    pady=10
                ).pack()
                
                # 基本信息
                info_frame = tk.Frame(details_win, bg=COLORS["bg"])
                info_frame.pack(fill=tk.X, padx=15, pady=5)
                
                tk.Label(
                    info_frame,
                    text=f"时间: {order.get('time', '')}",
                    font=FONTS["normal"],
                    fg=COLORS["text"],
                    bg=COLORS["bg"],
                    anchor='w'
                ).pack(fill=tk.X)
                
                tk.Label(
                    info_frame,
                    text=f"商品数量: {len(order.get('items', []))}",
                    font=FONTS["normal"],
                    fg=COLORS["text"],
                    bg=COLORS["bg"],
                    anchor='w'
                ).pack(fill=tk.X)
                
                tk.Label(
                    info_frame,
                    text=f"总金额: ¥{order.get('total', 0.0):.2f}",
                    font=FONTS["bold"],
                    fg=COLORS["primary"],
                    bg=COLORS["bg"],
                    anchor='w'
                ).pack(fill=tk.X)
                
                # 商品列表
                items_frame = tk.Frame(details_win, bg=COLORS["bg"])
                items_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
                
                columns = ("商品编号", "名称", "数量", "单价", "小计")
                tree_items = ttk.Treeview(items_frame, columns=columns, show='headings', height=10)
                
                for col in columns:
                    tree_items.heading(col, text=col)
                    tree_items.column(col, width=100, anchor='center')
                
                tree_items.column("名称", width=150, anchor='w')
                
                scroll_y = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=tree_items.yview)
                tree_items.configure(yscrollcommand=scroll_y.set)
                
                tree_items.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
                
                for item in order.get('items', []):
                    code = item.get('code', '')
                    name = item.get('name', '未知商品')
                    qty = item.get('quantity', 0)
                    price = item.get('price', 0.0)
                    subtotal = qty * price
                    tree_items.insert('', 'end', values=(code, name, qty, f"¥{price:.2f}", f"¥{subtotal:.2f}"))
                
                break
    
    tree_orders.bind("<Double-1>", show_order_details)
    
    # 状态栏
    status_bar_hist = tk.Label(
        history_win,
        text=f"共 {len(order_history)} 条订单记录",
        bd=1,
        relief=tk.SUNKEN,
        anchor=tk.W,
        font=FONTS["small"],
        bg=COLORS["light"],
        fg=COLORS["secondary"]
    )
    status_bar_hist.pack(side=tk.BOTTOM, fill=tk.X)

# --- 输入框回车跳转 ---
def code_entry_key(event):
    if event.keysym == "Return":
        cash_qty_entry.focus_set()

def qty_entry_key(event):
    if event.keysym == "Return":
        cash_code_entry.focus_set()
        add_to_cart()

# --- 状态更新 ---
def update_status(message):
    status_bar.config(text=message)
    root.after(5000, lambda: status_bar.config(text="就绪"))

# --- 初始化窗口 ---
root = tk.Tk()
root.title("📦 广州外国语学校团委学生会信息部智能库存管理系统")
root.geometry("1280x720")
root.configure(bg=COLORS["bg"])

try:
    root.iconbitmap("inventory.ico")
except:
    pass

# 配置样式
style = ttk.Style()
style.theme_use("clam")

# 配置Treeview样式
style.configure("Treeview",
                font=FONTS["normal"],
                rowheight=28,
                background=COLORS["card"],
                fieldbackground=COLORS["card"],
                foreground=COLORS["text"],
                bordercolor=COLORS["border"],
                borderwidth=1)

style.configure("Treeview.Heading",
                font=FONTS["bold"],
                background=COLORS["primary"],
                foreground="white",
                relief="flat",
                padding=5)

style.map("Treeview",
          background=[('selected', '#e6f2ff')],
          foreground=[('selected', COLORS["text"])])

style.configure("TButton",
                font=FONTS["bold"],
                padding=6,
                relief="flat",
                background=COLORS["primary"],
                foreground="white")

style.map("TButton",
          background=[("active", COLORS["dark"])])

style.configure("TEntry",
                fieldbackground=COLORS["light"],
                foreground=COLORS["text"],
                bordercolor=COLORS["border"],
                lightcolor=COLORS["primary"],
                darkcolor=COLORS["primary"],
                padding=5)

# 顶栏
top_frame = tk.Frame(root, bg=COLORS["bg"])
top_frame.pack(fill=tk.X, padx=15, pady=10)

title_label = tk.Label(
    top_frame,
    text="📦 智能库存管理系统",
    font=FONTS["title"],
    fg=COLORS["primary"],
    bg=COLORS["bg"]
)
title_label.pack(side=tk.LEFT)

search_frame = tk.Frame(top_frame, bg=COLORS["bg"])
search_frame.pack(side=tk.LEFT, padx=20)

search_var = tk.StringVar()
search_entry = tk.Entry(
    search_frame,
    textvariable=search_var,
    font=FONTS["normal"],
    bg=COLORS["light"],
    relief="flat",
    highlightthickness=1,
    highlightcolor=COLORS["primary"],
    highlightbackground=COLORS["border"],
    width=25
)
search_entry.pack(side=tk.LEFT, padx=(0,5))
search_entry.bind("<Return>", search_inventory)

search_btn = ttk.Button(search_frame, text="搜索", command=search_inventory)
search_btn.pack(side=tk.LEFT, padx=(0,5))

clear_btn = ttk.Button(
    search_frame,
    text="清除",
    command=clear_search,
    style="TButton",
    takefocus=0
)
clear_btn.pack(side=tk.LEFT)

view_history_btn = ttk.Button(
    top_frame,
    text="历史订单",
    command=show_order_history
)
view_history_btn.pack(side=tk.RIGHT,padx=0)

# 主区域
main_frame = tk.Frame(root, bg=COLORS["bg"])
main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0,10))

# 左侧库存管理
left_card = tk.Frame(
    main_frame, 
    bg="#e0e0e0",  # 阴影颜色
    padx=2, pady=2  # 阴影大小
)
left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))

# 实际内容容器
left_card_inner = tk.Frame(
    left_card,
    bg=COLORS["card"],
    highlightthickness=0,
    bd=0
)
left_card_inner.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

# 标题
tk.Label(
    left_card_inner,
    text="库存管理",
    font=FONTS["subtitle"],
    fg=COLORS["primary"],
    bg=COLORS["card"]
).pack(fill=tk.X, pady=(8, 2))

# 表格
columns = ("编号", "名称", "数量", "价格", "总价")
tree = ttk.Treeview(left_card, columns=columns, show='headings', selectmode='browse')

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor='center', width=100)

tree.column("名称", width=180, anchor='w')
tree.column("总价", width=120, anchor='e')

scroll_y = ttk.Scrollbar(left_card, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscrollcommand=scroll_y.set)

tree.pack(fill=tk.BOTH, expand=True, pady=0)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

tree.tag_configure("placeholder", foreground=COLORS["secondary"], font=FONTS["small"])

# 右键菜单
right_click_menu_selected = tk.Menu(root, tearoff=0, font=FONTS["small"])
right_click_menu_selected.add_command(label="查询商品", command=query_item)
right_click_menu_selected.add_command(label="删除商品", command=delete_item)

right_click_menu_empty = tk.Menu(root, tearoff=0, font=FONTS["small"])
right_click_menu_empty.add_command(label="添加商品", command=add_blank_row)

tree.bind("<Double-1>", on_double_click)
tree.bind("<Button-3>", show_context_menu)

# 右侧收银系统
right_card = tk.Frame(
    main_frame,
    bg="#e0e0e0",
    width=400,
    padx=0, pady=2
)
right_card.pack(side=tk.RIGHT, fill=tk.Y, padx=0)

# 实际内容容器
right_card_inner = tk.Frame(
    right_card,
    bg=COLORS["card"],
    highlightthickness=0,
    bd=0
)
right_card_inner.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

# 标题
tk.Label(
    right_card_inner,
    text="收银系统",
    font=FONTS["subtitle"],
    fg=COLORS["primary"],
    bg=COLORS["card"]
).pack(fill=tk.X, pady=10)

# 输入表单
form_frame = tk.Frame(right_card, bg=COLORS["card"])
form_frame.pack(fill=tk.X, padx=0, pady=(0,15))

tk.Label(
    form_frame,
    text="商品编号:",
    font=FONTS["normal"],
    fg=COLORS["text"],
    bg=COLORS["card"],
    anchor='w'
).grid(row=0, column=0, sticky="w", pady=(0,5))

cash_code_var = tk.StringVar()
cash_code_entry = tk.Entry(
    form_frame,
    textvariable=cash_code_var,
    font=FONTS["normal"],
    bg=COLORS["light"],
    relief="flat",
    highlightthickness=1,
    highlightcolor=COLORS["primary"],
    highlightbackground=COLORS["border"]
)
cash_code_entry.grid(row=0, column=1, sticky="ew", pady=(0,5))
cash_code_entry.bind("<Return>", code_entry_key)

tk.Label(
    form_frame,
    text="数量:",
    font=FONTS["normal"],
    fg=COLORS["text"],
    bg=COLORS["card"],
    anchor='w'
).grid(row=1, column=0, sticky="w")

cash_qty_var = tk.StringVar()
cash_qty_entry = tk.Entry(
    form_frame,
    textvariable=cash_qty_var,
    font=FONTS["normal"],
    bg=COLORS["light"],
    relief="flat",
    highlightthickness=1,
    highlightcolor=COLORS["primary"],
    highlightbackground=COLORS["border"]
)
cash_qty_entry.grid(row=1, column=1, sticky="ew")
cash_qty_entry.bind("<Return>", qty_entry_key)

form_frame.columnconfigure(1, weight=1)

add_cart_btn = ttk.Button(
    right_card,
    text="加入购物车",
    command=add_to_cart
)
add_cart_btn.pack(fill=tk.X, padx=15, pady=(0,15))

# 购物车表格
cart_columns = ("编号", "名称", "数量", "单价", "小计")
cart_tree = ttk.Treeview(
    right_card,
    columns=cart_columns,
    show="headings",
    height=8,
    selectmode='browse'
)

for col in cart_columns:
    cart_tree.heading(col, text=col)
    cart_tree.column(col, anchor='center', width=80)

cart_tree.column("名称", width=120, anchor='w')
cart_tree.column("小计", width=90, anchor='e')

scroll_y = ttk.Scrollbar(right_card, orient=tk.VERTICAL, command=cart_tree.yview)
cart_tree.configure(yscrollcommand=scroll_y.set)

cart_tree.pack(fill=tk.BOTH, padx=0, expand=True)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

# 总金额
total_frame = tk.Frame(right_card, bg=COLORS["card"])
total_frame.pack(fill=tk.X, padx=0, pady=10)

total_var = tk.StringVar(value="¥0.00")
total_label = tk.Label(
    total_frame,
    text="总金额: ¥0.00",
    font=FONTS["bold"],
    fg=COLORS["primary"],
    bg=COLORS["card"],
    anchor='e'
)
total_label.pack(side=tk.RIGHT)

# 按钮组
btn_frame = tk.Frame(right_card, bg=COLORS["card"])
btn_frame.pack(fill=tk.X, padx=0, pady=(0,15))

clear_cart_btn = ttk.Button(
    btn_frame,
    text="清空",
    command=clear_cart,
    style="TButton"
)
clear_cart_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))

checkout_btn = ttk.Button(
    btn_frame,
    text="结账",
    command=checkout,
    style="TButton"
)
checkout_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5,0))

# 状态栏
status_bar = tk.Label(
    root,
    text="就绪",
    bd=1,
    relief=tk.SUNKEN,
    anchor=tk.W,
    font=FONTS["small"],
    bg=COLORS["light"],
    fg=COLORS["secondary"]
)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# --- 初始化数据 ---
inventory = load_inventory()
order_history = load_orders()

refresh_tree()
add_blank_row()

# 启动主循环
root.mainloop()