#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import datetime
import re
import math
from config import COMMAND_PREFIX

# User data storage
user_data = {}

# Button layouts
basic_buttons = [
    ["7", "8", "9", "/", "√", "x²"],
    ["4", "5", "6", "*", "(", ")"],
    ["1", "2", "3", "-", "sin", "cos"],
    ["0", ".", "=", "+", "tan", "π"],
    ["C", "⌫", "History", "M+", "MR", "MC"],
    ["Scientific", "Basic"]
]

scientific_buttons = [
    ["7", "8", "9", "/", "^", "log"],
    ["4", "5", "6", "*", "ln", "!"],
    ["1", "2", "3", "-", "°→rad", "rad→°"],
    ["0", ".", "=", "+", "e", "1/x"],
    ["C", "⌫", "History", "M+", "MR", "MC"],
    ["Scientific", "Basic"]
]

def create_keyboard(current_input="0", is_scientific=False):
    """Create the calculator keyboard"""
    if not current_input:
        current_input = "0"
    
    buttons_layout = scientific_buttons if is_scientific else basic_buttons
    
    monitor = [[InlineKeyboardButton(
        f"{current_input[:20] + '...' if len(current_input) > 20 else current_input}", 
        callback_data="monitor"
    )]]
    
    keys = []
    for row in buttons_layout[:-1]:
        key_row = []
        for btn in row:
            callback_data = f"calc_{btn}"
            
            if btn.isdigit() or btn == ".":
                btn_style = btn
            elif btn in "+":
                btn_style = f"[{btn}]" 
            elif btn in "-":
                btn_style = f"[{btn}]"
            elif btn in "*":
                btn_style = "[×]"
            elif btn in "/":
                btn_style = "[÷]"
            elif btn in "^":
                btn_style = "[^]"
            elif btn == "=":
                btn_style = f"{btn}"
            elif btn == "C":
                btn_style = "C"
            elif btn == "⌫":
                btn_style = "⌫"
            elif "History" in btn:
                btn_style = "H"
            elif btn in ["M+", "MR", "MC"]:
                btn_style = f"M{btn[1:]}"
            else:
                btn_style = btn
            
            key_row.append(InlineKeyboardButton(btn_style, callback_data=callback_data))
        keys.append(key_row)
    
    mode_row = []
    for btn in buttons_layout[-1]:
        callback_data = f"mode_{btn.lower()}"
        mode_row.append(InlineKeyboardButton(btn, callback_data=callback_data))
    keys.append(mode_row)
    
    return InlineKeyboardMarkup(monitor + keys)

def safe_eval(expression, degrees=False):
    """Safely evaluate mathematical expressions"""
    try:
        if not expression or expression == "0":
            raise ValueError("❌Please Adjust Your Calculation")

        allowed_chars = set('0123456789.+-*/()^πe! \t')
        allowed_functions = {'sqrt', 'sin', 'cos', 'tan', 'log', 'ln', 'factorial', 'radians', 'degrees'}
        
        temp_expr = expression.lower()
        for func in allowed_functions:
            temp_expr = temp_expr.replace(func, '')
        
        for char in temp_expr:
            if char not in allowed_chars and not char.isalpha():
                raise ValueError(f"❌Please Adjust Your Calculation")

        if expression.endswith(('+', '-', '*', '/', '^', '(', '.')):
            raise ValueError("❌Please Adjust Your Calculation")
            
        if '()' in expression or any(f"{func}()" in expression.lower() for func in allowed_functions):
            raise ValueError("❌Please Adjust Your Calculation")
        
        if expression.count('(') != expression.count(')'):
            raise ValueError("❌Please Adjust Your Calculation")

        expr = expression.replace('π', 'math.pi').replace('e', 'math.e')
        
        func_pattern = re.compile(r'([a-zA-Z]+)\(')
        for func in func_pattern.findall(expr):
            if func.lower() not in allowed_functions:
                raise ValueError(f"❌Please Adjust Your Calculation")
        
        if degrees:
            expr = re.sub(r'(sin|cos|tan)\(([^)]+)\)', 
                         lambda m: f"math.{m.group(1).lower()}(math.radians({m.group(2)}))", expr.lower())
        
        expr = expr.replace('^', '**')
        expr = re.sub(r'(\d+)!', r'math.factorial(\1)', expr)
        expr = expr.replace('1/x', '1/')
        
        result = eval(expr, {'__builtins__': None}, {'math': math})
        
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(round(result, 10))
    except Exception as e:
        raise ValueError(f"❌Please Adjust Your Calculation")

def setup_calc_handler(app: Client):
    """Set up the calculator message and callback handlers"""
    
    @app.on_message(filters.command(["calc", "calculator"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def calculator(client, message):
        """Handler for /calc command"""
        user_id = message.from_user.id
        if user_id not in user_data:
            user_data[user_id] = {
                'history': [],
                'memory': None,
                'scientific_mode': False,
                'degrees': True
            }
        
        await client.send_message(
            chat_id=message.chat.id,
            text="**✨Hey There! Welcome To Smart Pro Calculator 🇧🇩**",
            reply_markup=create_keyboard(is_scientific=user_data[user_id]['scientific_mode']),
            parse_mode=ParseMode.MARKDOWN
        )

    @app.on_callback_query(filters.regex(r"^(calc|mode)_"))
    async def handle_calculator(client: Client, query: CallbackQuery):
        """Handler for all calculator button presses"""
        user_id = query.from_user.id
        data = query.data
        
        if user_id not in user_data:
            user_data[user_id] = {
                'history': [],
                'memory': None,
                'scientific_mode': False,
                'degrees': True
            }
        
        user_state = user_data[user_id]
        current_display = query.message.reply_markup.inline_keyboard[0][0].text
        current_value = current_display.replace("Display: ", "")
        
        if data.startswith("mode_"):
            mode = data.split("_")[1]
            user_state['scientific_mode'] = (mode == "scientific")
            await query.message.edit_reply_markup(
                reply_markup=create_keyboard(
                    current_input=current_value,
                    is_scientific=user_state['scientific_mode']
                )
            )
            return
        
        action = data.split("_")[1]
        
        if action.isdigit():
            new_display = action if current_value == "0" else current_value + action
        
        elif action == ".":
            if current_value == "0":
                new_display = "0."
            elif "." not in current_value.split()[-1]:
                new_display = current_value + "."
            else:
                await client.answer_callback_query(
                    query.id,
                    text="❌Please Adjust Your Calculation",
                    show_alert=True
                )
                return
        
        elif action in ["+", "-", "*", "/", "^"]:
            if current_value == "0" and not user_state['history']:
                await client.answer_callback_query(
                    query.id,
                    text="❌Please Adjust Your Calculation",
                    show_alert=True
                )
                return
            
            if current_value and current_value[-1] in ["+", "-", "*", "/", "^"]:
                await client.answer_callback_query(
                    query.id,
                    text="❌Please Adjust Your Calculation",
                    show_alert=True
                )
                return
                
            new_display = current_value + action
        
        elif action == "π":
            new_display = "π" if current_value == "0" else current_value + "π"
        elif action == "e":
            new_display = "e" if current_value == "0" else current_value + "e"
        
        elif action == "1/x":
            new_display = "1/" if current_value == "0" else f"1/({current_value})"
        elif action in ["sin", "cos", "tan", "log", "ln", "sqrt"]:
            new_display = f"{action}(" if current_value == "0" else f"{action}({current_value})"
        elif action == "x²":
            new_display = f"({current_value})^2"
        elif action == "!":
            if current_value == "0":
                await client.answer_callback_query(
                    query.id,
                    text="Please enter a number first",
                    show_alert=True
                )
                return
            new_display = f"{current_value}!"
        
        elif action == "M+":
            try:
                result = safe_eval(current_value, user_state['degrees'])
                value = float(result)
                user_state['memory'] = value if user_state['memory'] is None else user_state['memory'] + value
                await client.answer_callback_query(
                    query.id,
                    text=f"Memory: {user_state['memory']}",
                    show_alert=False
                )
                return
            except Exception as e:
                await client.answer_callback_query(
                    query.id,
                    text=f"Error: {str(e)}",
                    show_alert=True
                )
                return
        
        elif action == "MR":
            if user_state['memory'] is not None:
                new_display = str(user_state['memory'])
                await query.message.edit_reply_markup(
                    reply_markup=create_keyboard(
                        current_input=new_display,
                        is_scientific=user_state['scientific_mode']
                    )
                )
            else:
                await client.answer_callback_query(
                    query.id,
                    text="Memory is empty",
                    show_alert=True
                )
            return
        
        elif action == "MC":
            user_state['memory'] = None
            await client.answer_callback_query(
                query.id,
                text="Memory cleared",
                show_alert=False
            )
            return
        
        elif action == "History":
            hist = "\n".join(user_state['history'][-5:]) if user_state['history'] else "No history yet"
            await client.answer_callback_query(
                query.id,
                text=f"History:\n{hist}",
                show_alert=True
            )
            return
        
        elif action == "C":
            await query.message.edit_reply_markup(
                reply_markup=create_keyboard(
                    is_scientific=user_state['scientific_mode']
                )
            )
            return
        
        elif action == "⌫":
            new_display = current_value[:-1] if len(current_value) > 1 else "0"
            await query.message.edit_reply_markup(
                reply_markup=create_keyboard(
                    current_input=new_display,
                    is_scientific=user_state['scientific_mode']
                )
            )
            return
        
        elif action == "=":
            try:
                if current_value == "0":
                    await client.answer_callback_query(
                        query.id,
                        text="❌Please Adjust Your Calculation",
                        show_alert=True
                    )
                    return
                
                result = safe_eval(current_value, user_state['degrees'])
                timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                history_entry = f"{current_value} = {result} ({timestamp})"
                user_state['history'].append(history_entry)
                
                await query.message.edit_reply_markup(
                    reply_markup=create_keyboard(
                        current_input=result,
                        is_scientific=user_state['scientific_mode']
                    )
                )
            except Exception as e:
                await client.answer_callback_query(
                    query.id,
                    text=f"Error: {str(e)}",
                    show_alert=True
                )
            return
        
        elif action == "°→rad":
            user_state['degrees'] = False
            await client.answer_callback_query(
                query.id,
                text="Using radians now",
                show_alert=False
            )
            return
        elif action == "rad→°":
            user_state['degrees'] = True
            await client.answer_callback_query(
                query.id,
                text="Using degrees now",
                show_alert=False
            )
            return
        
        else:
            new_display = current_value + action
        
        await query.message.edit_reply_markup(
            reply_markup=create_keyboard(
                current_input=new_display,
                is_scientific=user_state['scientific_mode']
            )
        )