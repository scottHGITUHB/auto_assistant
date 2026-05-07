from fastapi import APIRouter, Request
import logging
import os
import time
import asyncio
import sys
import json
import re
from datetime import datetime
from models import db, Memory, Reminder, FinanceRecord, CrawlerTask
from services.email_service import email_service
from services import crawler_service

# Set UTF-8 encoding for stdout
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# Global browser session management
playwright = None
browser = None
context = None
page = None
is_logged_in = False
timeout_task = None
TIMEOUT_MINUTES = 30

TEST_DIR = "kimi_test"
if not os.path.exists(TEST_DIR):
    os.makedirs(TEST_DIR)

# Chat history storage
CHAT_LOGS_DIR = "chat_logs"
if not os.path.exists(CHAT_LOGS_DIR):
    os.makedirs(CHAT_LOGS_DIR)

def save_chat_history(user_message, ai_response):
    """Save chat history to daily log file"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(CHAT_LOGS_DIR, f"{today}.json")
        
        # Load existing logs for today
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Add new chat record
        chat_record = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user_message": user_message,
            "ai_response": ai_response
        }
        logs.append(chat_record)
        
        # Save updated logs
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] Chat history saved to {log_file}")
    except Exception as e:
        print(f"[ERROR] Failed to save chat history: {e}")

def get_chat_history(days=7):
    """Get chat history for recent days"""
    try:
        history = {}
        for i in range(days):
            date = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(CHAT_LOGS_DIR, f"{date}.json")
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    history[date] = json.load(f)
        return history
    except Exception as e:
        print(f"[ERROR] Failed to get chat history: {e}")
        return {}

# Command handlers
async def handle_remember_command(content):
    """Handle /remember command"""
    try:
        # Remove command prefix
        memory_content = content.replace('/记住', '').replace('/remember', '').strip()
        
        if not memory_content:
            return "Please provide content to remember, e.g.: /Remember Chongqing has Hongyadong"
        
        # Save to database
        session = db.session
        new_memory = Memory(
            user_id="default_user",
            content=memory_content,
            category="chat_command"
        )
        session.add(new_memory)
        session.commit()
        
        return f"Already remembered: {memory_content}"
    except Exception as e:
        print(f"[ERROR] Failed to save memory: {e}")
        return f"Failed to save memory: {str(e)}"

async def handle_reminder_command(content):
    """Handle /remind command"""
    try:
        # Remove command prefix
        reminder_text = content.replace('/提醒', '').replace('/remind', '').strip()
        
        if not reminder_text:
            return "Please provide reminder content and time, e.g.: /Remind 5月16日教资考试"
        
        # Enhanced time parsing - support Chinese date formats
        time_patterns = [
            # Chinese date formats
            r'(\d{1,2}月\d{1,2}日)',  # 5月16日
            r'(\d{4}年\d{1,2}月\d{1,2}日)',  # 2024年5月16日
            r'(\d{1,2}月\d{1,2}日\d{1,2}:\d{2})',  # 5月16日15:00
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',  # 2024-01-01 15:00
            r'(\d{2}:\d{2})',  # 15:00
            r'(tomorrow|today|next\s+week|明天|后天|下周)',  # English and Chinese
        ]
        
        remind_at = "未指定时间"
        reminder_content = reminder_text
        
        for pattern in time_patterns:
            match = re.search(pattern, reminder_text, re.IGNORECASE)
            if match:
                remind_at = match.group(1)
                # Remove time from content, but keep the rest
                reminder_content = reminder_text.replace(remind_at, '').strip()
                # Clean up extra spaces
                reminder_content = re.sub(r'\s+', ' ', reminder_content).strip()
                break
        
        # If no time found, try to extract date from beginning or end
        if remind_at == "未指定时间":
            # Try to find date at the beginning: "5月16日教资考试"
            beginning_match = re.match(r'(\d{1,2}月\d{1,2}日)', reminder_text)
            if beginning_match:
                remind_at = beginning_match.group(1)
                reminder_content = reminder_text[len(remind_at):].strip()
            else:
                # Try to find date at the end: "教资考试5月16日"
                end_match = re.search(r'(\d{1,2}月\d{1,2}日)$', reminder_text)
                if end_match:
                    remind_at = end_match.group(1)
                    reminder_content = reminder_text[:end_match.start()].strip()
        
        # Save to database
        session = db.session
        new_reminder = Reminder(
            user_id="default_user",
            content=reminder_content,
            remind_at=remind_at,
            is_done=False
        )
        session.add(new_reminder)
        session.commit()
        
        # Send email notification if configured
        if email_service.is_configured():
            await email_service.send_reminder_email(reminder_content, remind_at)
            email_status = "Reminder email has been sent"
        else:
            email_status = "Email not configured, unable to send reminder email"
        
        return f"Reminder set: {reminder_content} (Time: {remind_at})\n{email_status}"
    except Exception as e:
        print(f"[ERROR] Failed to set reminder: {e}")
        return f"Failed to set reminder: {str(e)}"

async def handle_crawler_command(content):
    """Handle /get command"""
    try:
        # Remove command prefix
        crawler_name = content.replace('/获取', '').replace('/get', '').strip()
        
        if not crawler_name:
            return "Please provide the crawler name, e.g.: /Get news"
        
        # Find crawler task
        session = db.session
        crawler = session.query(CrawlerTask).filter(CrawlerTask.name.contains(crawler_name)).first()
        
        if not crawler:
            return f"Crawler '{crawler_name}' not found, please check the crawler management page"
        
        # Run crawler
        result = await crawler_service.run_crawler(crawler, session)
        
        if result.get("status") == "success":
            return f"Crawler '{crawler.name}' executed successfully:\n{result.get('result', 'No results')[:500]}"
        else:
            return f"Crawler execution failed: {result.get('message', 'Unknown error')}"
    except Exception as e:
        print(f"[ERROR] Failed to run crawler: {e}")
        return f"Failed to run crawler: {str(e)}"

async def handle_finance_command(content):
    """Handle /finance command with flexible parsing"""
    try:
        # Remove command prefix
        finance_text = content.replace('/理财', '').replace('/finance', '').strip()

        if not finance_text:
            return "请提供理财记录，例如: /理财 收入1500元工资 或 /理财 午餐花了50元"

        # Flexible parsing using regex patterns
        import re

        # Try to extract amount - support various formats:
        # 1500, 1500元, 1500块, 1,500, 1.5k, 1.5万
        amount_match = None
        amount = None

        # Pattern: 1.5万/1.5w
        wan_match = re.search(r'(\d+(?:\.\d+)?)\s*[万w]', finance_text, re.IGNORECASE)
        if wan_match:
            amount = float(wan_match.group(1)) * 10000
            amount_match = wan_match
        else:
            # Pattern: 1.5k
            k_match = re.search(r'(\d+(?:\.\d+)?)\s*[k千]', finance_text, re.IGNORECASE)
            if k_match:
                amount = float(k_match.group(1)) * 1000
                amount_match = k_match
            else:
                # Pattern: normal number with optional 元/块/yuan
                normal_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:元|块|yuan)?', finance_text)
                if normal_match:
                    amount_str = normal_match.group(1).replace(',', '')
                    amount = float(amount_str)
                    amount_match = normal_match

        if amount is None:
            return "无法识别金额，请包含数字，例如: 1500元、1.5万、2k"

        # Try to determine type (income/expense)
        record_type = None
        income_keywords = ['收入', '赚到', '收到', '工资', '薪水', '奖金', '分红', '收益', '退款', '报销',
                           'income', 'salary', 'earn', 'receive', 'bonus', 'refund']
        expense_keywords = ['支出', '花了', '用了', '消费', '支付', '付款', '买', '购买', '花费', '开销',
                            'expense', 'spent', 'cost', 'pay', 'buy', 'purchase']

        text_lower = finance_text.lower()
        for keyword in income_keywords:
            if keyword in text_lower:
                record_type = 'income'
                break

        if not record_type:
            for keyword in expense_keywords:
                if keyword in text_lower:
                    record_type = 'expense'
                    break

        # Default to expense if not found
        if not record_type:
            record_type = 'expense'

        # Try to extract category using common categories
        common_categories = {
            '餐饮': ['吃饭', '午餐', '晚餐', '早餐', '外卖', '餐厅', '火锅', '烧烤', '奶茶', '咖啡', '食堂', 'food', 'meal', 'lunch', 'dinner'],
            '交通': ['地铁', '公交', '打车', '出租车', '滴滴', '油费', '加油', '停车', '高铁', '火车', '飞机', 'transport', 'subway', 'bus', 'taxi'],
            '购物': ['买衣服', '买鞋', '买包', '超市', '便利店', '淘宝', '京东', '拼多多', 'shopping', 'buy'],
            '住房': ['房租', '房贷', '物业费', '水电', '燃气', '宽带', 'rent', 'mortgage'],
            '娱乐': ['电影', '游戏', 'ktv', '唱歌', '旅游', '旅行', '娱乐', 'movie', 'game', 'entertainment'],
            '医疗': ['看病', '买药', '医院', '体检', 'medical', 'hospital', 'medicine'],
            '教育': ['学费', '买书', '课程', '培训', '教育', 'education', 'book', 'course'],
            '通讯': ['话费', '流量', '手机', 'phone', 'mobile'],
            '工资': ['工资', '薪水', 'salary', 'wage'],
            '投资': ['股票', '基金', '理财', 'invest', 'stock', 'fund'],
            '人情': ['红包', '礼物', '请客', '送礼', 'gift', 'red envelope']
        }

        category = None
        for cat_name, keywords in common_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    category = cat_name
                    break
            if category:
                break

        # If no category found, try to extract from remaining text
        if not category:
            # Remove amount and common words to get category
            category_text = finance_text
            if amount_match:
                category_text = category_text.replace(amount_match.group(0), '')
            # Remove punctuation, numbers, spaces
            category_text = re.sub(r'[元块yuan,，\.\d\s]', '', category_text)
            # Remove ALL income/expense type indicator keywords (not just some)
            # These are words that indicate transaction type, not category
            type_indicators = '收入|支出|花了|用了|赚到|收到|工资|消费|income|expense|salary|earn|spent|cost|pay|buy|purchase|receive|bonus|refund'
            category_text = re.sub(type_indicators, '', category_text, flags=re.IGNORECASE)
            category_text = category_text.strip()

            if category_text:
                category = category_text[:10]  # Limit length
            else:
                # Use smart defaults based on record type when no category specified
                category = "其他支出" if record_type == 'expense' else "其他收入"

        note = finance_text
        record_date = datetime.now().strftime("%Y-%m-%d")

        # Save to database
        session = db.session
        new_record = FinanceRecord(
            user_id="default_user",
            type=record_type,
            amount=amount,
            category=category,
            note=note,
            record_date=record_date
        )
        session.add(new_record)
        session.commit()

        # Calculate financial summary
        summary = await get_finance_summary(session)

        type_text = "收入" if record_type == 'income' else "支出"
        response = f"[理财记录已保存] {type_text}: {amount:.2f}元 - {category}\n\n"
        response += f"===== 本月财务概览 =====\n"
        response += f"本月收入: {summary['monthly_income']:.2f}元\n"
        response += f"本月支出: {summary['monthly_expense']:.2f}元\n"
        response += f"本月结余: {summary['monthly_balance']:.2f}元\n"
        response += f"储蓄率: {summary['savings_rate']:.1f}%\n"

        if summary['monthly_budget'] > 0:
            response += f"\n预算状况:\n"
            response += f"建议预算(收入的80%): {summary['monthly_budget']:.2f}元\n"
            response += f"预算剩余: {summary['remaining_budget']:.2f}元\n"
            if summary['remaining_budget'] < 0:
                response += f"[注意] 已超支 {abs(summary['remaining_budget']):.2f}元\n"

        # Add category breakdown for current month
        if summary['monthly_category_stats']:
            response += f"\n本月支出分类:\n"
            for cat, cat_amount in sorted(summary['monthly_category_stats'].items(), key=lambda x: x[1], reverse=True):
                percentage = (cat_amount / summary['monthly_expense'] * 100) if summary['monthly_expense'] > 0 else 0
                response += f"  {cat}: {cat_amount:.2f}元 ({percentage:.1f}%)\n"

        # Add yearly summary
        response += f"\n===== 本年累计 =====\n"
        response += f"年度收入: {summary['yearly_income']:.2f}元\n"
        response += f"年度支出: {summary['yearly_expense']:.2f}元\n"
        response += f"年度结余: {summary['yearly_balance']:.2f}元\n"

        return response
    except Exception as e:
        print(f"[ERROR] Failed to save finance record: {e}")
        import traceback
        traceback.print_exc()
        return f"保存理财记录失败: {str(e)}"

async def get_finance_summary(session):
    """Get comprehensive financial summary with monthly and yearly stats"""
    try:
        records = session.query(FinanceRecord).all()

        total_income = sum(r.amount for r in records if r.type == 'income')
        total_expense = sum(r.amount for r in records if r.type == 'expense')
        balance = total_income - total_expense

        # Calculate monthly stats
        current_month = datetime.now().strftime("%Y-%m")
        monthly_income = sum(r.amount for r in records if r.type == 'income' and r.record_date.startswith(current_month))
        monthly_expense = sum(r.amount for r in records if r.type == 'expense' and r.record_date.startswith(current_month))
        monthly_balance = monthly_income - monthly_expense

        # Monthly category stats
        monthly_category_stats = {}
        for r in records:
            if r.type == 'expense' and r.record_date.startswith(current_month):
                monthly_category_stats[r.category] = monthly_category_stats.get(r.category, 0) + r.amount

        # Savings rate
        savings_rate = (monthly_balance / monthly_income * 100) if monthly_income > 0 else 0

        # Budget calculation (80% of income)
        monthly_budget = monthly_income * 0.8
        remaining_budget = monthly_budget - monthly_expense

        # Calculate yearly stats
        current_year = datetime.now().strftime("%Y")
        yearly_income = sum(r.amount for r in records if r.type == 'income' and r.record_date.startswith(current_year))
        yearly_expense = sum(r.amount for r in records if r.type == 'expense' and r.record_date.startswith(current_year))
        yearly_balance = yearly_income - yearly_expense

        # Monthly breakdown for current year
        monthly_breakdown = {}
        for r in records:
            if r.record_date.startswith(current_year):
                month = r.record_date[:7]  # YYYY-MM
                if month not in monthly_breakdown:
                    monthly_breakdown[month] = {'income': 0, 'expense': 0, 'balance': 0}
                monthly_breakdown[month][r.type] += r.amount

        for month in monthly_breakdown:
            monthly_breakdown[month]['balance'] = monthly_breakdown[month]['income'] - monthly_breakdown[month]['expense']

        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'monthly_income': monthly_income,
            'monthly_expense': monthly_expense,
            'monthly_balance': monthly_balance,
            'monthly_budget': monthly_budget,
            'remaining_budget': remaining_budget,
            'savings_rate': savings_rate,
            'monthly_category_stats': monthly_category_stats,
            'yearly_income': yearly_income,
            'yearly_expense': yearly_expense,
            'yearly_balance': yearly_balance,
            'monthly_breakdown': monthly_breakdown
        }
    except Exception as e:
        print(f"[ERROR] Failed to get finance summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            'total_income': 0, 'total_expense': 0, 'balance': 0,
            'monthly_income': 0, 'monthly_expense': 0, 'monthly_balance': 0,
            'monthly_budget': 0, 'remaining_budget': 0, 'savings_rate': 0,
            'monthly_category_stats': {},
            'yearly_income': 0, 'yearly_expense': 0, 'yearly_balance': 0,
            'monthly_breakdown': {}
        }

async def parse_and_handle_command(message):
    """Parse user message and handle commands"""
    message = message.strip()
    
    # Check for commands
    if message.startswith('/记住') or message.startswith('/remember'):
        return await handle_remember_command(message)
    
    elif message.startswith('/提醒') or message.startswith('/remind'):
        return await handle_reminder_command(message)
    
    elif message.startswith('/获取') or message.startswith('/get'):
        return await handle_crawler_command(message)
    
    elif message.startswith('/理财') or message.startswith('/finance'):
        return await handle_finance_command(message)
    
    else:
        # Normal message, use Kimi AI
        return await get_kimi_response(message)

# Kimi AI functions (keep existing)
async def init_browser():
    """Initialize browser session"""
    global playwright, browser, context, page, is_logged_in
    
    if browser is None:
        from playwright.async_api import async_playwright
        
        print("[INFO] Initializing browser...")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        
        storage_path = os.path.join(TEST_DIR, "kimi_auth.json")
        if os.path.exists(storage_path):
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                storage_state=storage_path
            )
        else:
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
        
        page = await context.new_page()
        await page.goto("https://kimi.moonshot.cn/chat")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(2)
        
        is_logged_in = await check_login()
        await close_ads_continuous(page)
        
        start_timeout()
        print("[INFO] Browser session initialized")

async def check_login():
    """Check if logged in"""
    try:
        input_box = page.locator('[contenteditable="true"], textarea').first
        return await input_box.is_visible()
    except:
        return False

def start_timeout():
    """Start timeout task"""
    global timeout_task
    if timeout_task:
        timeout_task.cancel()
    
    async def timeout_handler():
        await asyncio.sleep(TIMEOUT_MINUTES * 60)
        await close_browser()
        print("[INFO] Session timeout, browser closed")
    
    timeout_task = asyncio.create_task(timeout_handler())

def reset_timeout():
    """Reset timeout timer"""
    start_timeout()

async def close_browser():
    """Close browser session"""
    global browser, context, page, is_logged_in
    
    if timeout_task:
        timeout_task.cancel()
    
    if page:
        try:
            storage_path = os.path.join(TEST_DIR, "kimi_auth.json")
            await context.storage_state(path=storage_path)
        except Exception as e:
            print(f"[ERROR] Failed to save login state: {e}")
            pass
        await page.close()
        page = None
    
    if context:
        await context.close()
        context = None
    
    if browser:
        await browser.close()
        browser = None
    
    if playwright:
        await playwright.stop()
        playwright = None
    
    is_logged_in = False
    print("[INFO] Browser session closed")

async def close_ads_once(page):
    """Execute once ad detection and close"""
    try:
        later_selectors = [
            'button:has-text("稍后再说")',
            'text=稍后再说',
            '.btn-later',
            '.btn-secondary',
            '[class*="later"]',
            '[class*="secondary"]'
        ]
        
        for selector in later_selectors:
            try:
                later_button = page.locator(selector).first
                if await later_button.is_visible():
                    await later_button.click()
                    print("[INFO] Clicked 'Later' button")
                    await asyncio.sleep(0.5)
                    break
            except:
                continue
        
        close_selectors = [
            'button:has-text("关闭")',
            'button:has-text("×")',
            'button:has-text("关闭广告")',
            '.close-btn',
            '.close-button',
            '[aria-label="关闭"]',
            '.modal-close',
            '.popup-close'
        ]
        
        for selector in close_selectors:
            try:
                close_button = page.locator(selector).first
                if await close_button.is_visible():
                    await close_button.click()
                    print("[INFO] Closed ad popup")
                    await asyncio.sleep(0.5)
                    break
            except:
                continue
        
        try:
            videos = page.locator('video')
            count = await videos.count()
            for i in range(count):
                video = videos.nth(i)
                if await video.is_visible():
                    await page.evaluate('(el) => { el.pause(); el.style.pointerEvents = "none"; }', video)
        except:
            pass
    except Exception as e:
        pass

async def close_ads_continuous(page):
    """Continuously detect and close ads"""
    print("[INFO] Starting ad detection...")
    max_checks = 5
    check_count = 0
    
    while check_count < max_checks:
        ad_found = False
        
        try:
            later_button = page.locator('button:has-text("稍后再说")').first
            if await later_button.is_visible():
                await later_button.click()
                print("[INFO] Clicked 'Later' button")
                ad_found = True
                await asyncio.sleep(0.5)
        except:
            pass
        
        try:
            close_button = page.locator('button:has-text("关闭")').first
            if await close_button.is_visible():
                await close_button.click()
                print("[INFO] Closed ad popup")
                ad_found = True
                await asyncio.sleep(0.5)
        except:
            pass
        
        try:
            videos = page.locator('video')
            count = await videos.count()
            for i in range(count):
                video = videos.nth(i)
                if await video.is_visible():
                    await page.evaluate('(el) => { el.pause(); el.style.pointerEvents = "none"; }', video)
                    ad_found = True
        except:
            pass
        
        if not ad_found:
            print("[INFO] No ads detected")
            break
        
        check_count += 1
        await asyncio.sleep(0.5)
    
    print("[INFO] Ad detection completed")

async def get_ai_response():
    """Get AI response"""
    global page
    
    start_time = time.time()
    last_text = ""
    stable_count = 0
    max_stable = 3
    timeout = 90
    
    while time.time() - start_time < timeout:
        try:
            await close_ads_once(page)
            
            messages = await page.locator('.markdown, .assistant, .message, [class*="answer"], [class*="response"]').all()
            if not messages:
                await asyncio.sleep(1)
                continue
            
            current_text = await messages[-1].inner_text()
            current_text = current_text.strip()
            
            if not current_text:
                await asyncio.sleep(1)
                continue
            
            if current_text == last_text:
                stable_count += 1
            else:
                stable_count = 0
                last_text = current_text
            
            if stable_count >= max_stable:
                return current_text
            
            await asyncio.sleep(1)
            
        except Exception as e:
            await asyncio.sleep(1)
    
    return last_text if last_text else "Timeout: No response received"

async def get_kimi_response(question):
    """Get Kimi AI response"""
    global page, is_logged_in
    
    if browser is None:
        await init_browser()
    
    if not is_logged_in:
        return "Error: Not logged in, please run python kimi.py to login first"
    
    reset_timeout()
    await close_ads_continuous(page)
    
    chat_input = page.locator('[contenteditable="true"], textarea').first
    if not await chat_input.is_visible():
        await close_ads_continuous(page)
        chat_input = page.locator('[contenteditable="true"], textarea').first
        if not await chat_input.is_visible():
            return "Error: Chat input box not visible"
    
    # Use Playwright's fill method to input text
    chat_input = page.locator('[contenteditable="true"], textarea').first
    await chat_input.click()
    await chat_input.fill(question)
    await asyncio.sleep(0.5)
    
    # Press Enter to send message
    await chat_input.press("Enter")
    await asyncio.sleep(1)
    
    await close_ads_continuous(page)
    
    response_text = await get_ai_response()
    
    return response_text

@router.post("/send")
async def send_message(request: Request):
    """Process chat message and return AI response"""
    try:
        data = await request.json()
        message = data.get("message")

        if not message:
            return {"code": 400, "msg": "Message cannot be empty"}

        print(f"\n[INFO] ========== Received chat message ==========")
        print(f"[INFO] Message: {message}")

        # Parse and handle command
        response_text = await parse_and_handle_command(message)
        print(f"[INFO] Response: {response_text}")
        
        # Save chat history
        save_chat_history(message, response_text)

        print("[INFO] ========== Processing completed ==========")
        return {"code": 200, "response": response_text}
    except Exception as e:
        print(f"\n[ERROR] ========== Failed to process chat message ==========")
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"code": 500, "msg": str(e)}

@router.get("/history")
async def get_chat_logs():
    """Get chat history grouped by day"""
    try:
        history = get_chat_history(days=7)
        return {"code": 200, "data": history}
    except Exception as e:
        print(f"[ERROR] Failed to get chat logs: {e}")
        return {"code": 500, "msg": str(e)}

@router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "Chat service"}