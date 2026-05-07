from playwright.async_api import async_playwright
import time
import os
import asyncio

# 创建测试文件夹
TEST_DIR = "kimi_test"
if not os.path.exists(TEST_DIR):
    os.makedirs(TEST_DIR)
    print(f"创建测试文件夹: {TEST_DIR}")

# 全局浏览器会话管理
class KimiBrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        self.timeout_task = None
        self.TIMEOUT_MINUTES = 30  # 30分钟超时
    
    async def init_browser(self):
        """初始化浏览器会话"""
        if self.browser is None:
            # 不使用上下文管理器，手动管理生命周期
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(headless=True)
            
            storage_path = os.path.join(TEST_DIR, "kimi_auth.json")
            if os.path.exists(storage_path):
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    storage_state=storage_path
                )
            else:
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
            
            self.page = await self.context.new_page()
            await self.page.goto("https://kimi.moonshot.cn/chat")
            await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            
            # 检测登录状态
            self.is_logged_in = await self._check_login()
            
            # 关闭广告
            await close_ads_continuous(self.page)
            
            # 启动超时任务
            self._start_timeout()
            
            print("✅ 浏览器会话初始化完成")
    
    async def _check_login(self):
        """检测是否已登录"""
        try:
            input_box = self.page.locator('[contenteditable="true"], textarea').first
            return await input_box.is_visible()
        except:
            return False
    
    def _start_timeout(self):
        """启动超时任务"""
        if self.timeout_task:
            self.timeout_task.cancel()
        
        async def timeout_handler():
            await asyncio.sleep(self.TIMEOUT_MINUTES * 60)
            await self.close_browser()
            print("⏰ 会话超时，已自动关闭浏览器")
        
        self.timeout_task = asyncio.create_task(timeout_handler())
    
    def reset_timeout(self):
        """重置超时计时器"""
        self._start_timeout()
        print("🔄 超时计时器已重置")
    
    async def close_browser(self):
        """关闭浏览器会话"""
        if self.timeout_task:
            self.timeout_task.cancel()
        
        if self.page:
            try:
                storage_path = os.path.join(TEST_DIR, "kimi_auth.json")
                await self.context.storage_state(path=storage_path)
            except:
                pass
            await self.page.close()
            self.page = None
        
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        self.is_logged_in = False
        print("🔒 浏览器会话已关闭")
    
    async def send_message(self, question):
        """发送消息并获取回复"""
        if self.browser is None:
            await self.init_browser()
        
        if not self.is_logged_in:
            return "错误：未登录，请先运行登录流程"
        
        # 重置超时计时器
        self.reset_timeout()
        
        # 持续检测并关闭广告
        await close_ads_continuous(self.page)
        
        # 检查输入框是否可用
        chat_input = self.page.locator('[contenteditable="true"], textarea').first
        if not await chat_input.is_visible():
            await close_ads_continuous(self.page)
            chat_input = self.page.locator('[contenteditable="true"], textarea').first
            if not await chat_input.is_visible():
                return "错误：聊天输入框不可见"
        
        # 使用JavaScript直接聚焦并输入
        await self.page.evaluate('''(question) => {
            const input = document.querySelector('[contenteditable="true"], textarea');
            if (input) {
                input.focus();
                input.textContent = question;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }''', question)
        await asyncio.sleep(0.5)
        
        # 按回车发送消息
        await self.page.evaluate('''() => {
            const input = document.querySelector('[contenteditable="true"], textarea');
            if (input) {
                const event = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true });
                input.dispatchEvent(event);
            }
        }''')
        await asyncio.sleep(1)
        
        # 再次检查广告
        await close_ads_continuous(self.page)
        
        # 获取AI回复
        response_text = await self._get_ai_response()
        
        return response_text
    
    async def _get_ai_response(self):
        """获取AI回复"""
        start_time = time.time()
        last_text = ""
        stable_count = 0
        max_stable = 3
        timeout = 90
        
        while time.time() - start_time < timeout:
            try:
                await close_ads_once(self.page)
                
                messages = await self.page.locator('.markdown, .assistant, .message, [class*="answer"], [class*="response"]').all()
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
        
        return last_text if last_text else "超时未获取到回复"

# 创建全局浏览器管理器实例
browser_manager = KimiBrowserManager()

async def close_ads_once(page):
    """执行一次广告检测和关闭"""
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
                    print("✅ 点击了'稍后再说'按钮")
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
                    print("✅ 关闭了广告弹窗")
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
    """持续检测并关闭广告"""
    print("🔍 开始持续检测广告...")
    max_checks = 5
    check_count = 0
    
    while check_count < max_checks:
        ad_found = False
        
        try:
            later_button = page.locator('button:has-text("稍后再说")').first
            if await later_button.is_visible():
                await later_button.click()
                print("✅ 点击了'稍后再说'按钮")
                ad_found = True
                await asyncio.sleep(0.5)
        except:
            pass
        
        try:
            close_button = page.locator('button:has-text("关闭")').first
            if await close_button.is_visible():
                await close_button.click()
                print("✅ 关闭了广告弹窗")
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
            print("✅ 未检测到广告")
            break
        
        check_count += 1
        await asyncio.sleep(0.5)
    
    print("🔍 广告检测结束")

async def get_kimi_response(question):
    """获取Kimi AI的回答"""
    print(f"========== 获取Kimi AI回答开始 ==========")
    print(f"用户问题: {question}")
    try:
        response = await browser_manager.send_message(question)
        print(f"Kimi AI回复: {response}")
        print(f"========== 获取Kimi AI回答结束 ==========")
        return response
    except Exception as e:
        print(f"❌ 获取Kimi回复时出错: {e}")
        import traceback
        traceback.print_exc()
        # 重置浏览器会话，下次重新连接
        await browser_manager.close_browser()
        print(f"========== 获取Kimi AI回答结束(错误) ==========")
        return f"错误：{str(e)}"

async def test_kimi_login():
    """测试登录流程（带图形界面）"""
    print("测试 Kimi 登录流程...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            storage_path = os.path.join(TEST_DIR, "kimi_auth.json")
            
            if os.path.exists(storage_path):
                print("✅ 使用已保存的登录状态")
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    storage_state=storage_path
                )
            else:
                print("⚠️ 未找到登录状态，需要扫码登录")
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
            
            page = await context.new_page()
            await page.goto("https://kimi.moonshot.cn/chat")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            
            screenshot_path = os.path.join(TEST_DIR, "initial_page.png")
            await page.screenshot(path=screenshot_path)
            print(f"5. 初始页面截图已保存: {screenshot_path}")
            
            print("6. 检测登录状态...")
            try:
                input_box = page.locator('[contenteditable="true"], textarea').first
                if await input_box.is_visible():
                    print("✅ 已登录，无需扫码")
                    
                    await input_box.click()
                    await input_box.fill("你好")
                    print("✅ 已在输入框中粘贴: 你好")
                    
                    screenshot_path = os.path.join(TEST_DIR, "input_filled.png")
                    await page.screenshot(path=screenshot_path)
                    print(f"8. 输入框状态截图已保存: {screenshot_path}")
                    
                    await input_box.press("Enter")
                    print("✅ 消息已发送")
                    
                    print("10. 等待Kimi助手的回复...")
                    start_time = time.time()
                    last_text = ""
                    stable_count = 0
                    
                    while time.time() - start_time < 30:
                        try:
                            messages = await page.locator('.markdown, .assistant, .message').all()
                            if messages:
                                current_text = await messages[-1].inner_text()
                                current_text = current_text.strip()
                                
                                if current_text == last_text:
                                    stable_count += 1
                                else:
                                    stable_count = 0
                                    last_text = current_text
                                
                                if stable_count >= 3:
                                    break
                            
                            await asyncio.sleep(1)
                        except:
                            await asyncio.sleep(1)
                    
                    if last_text:
                        print("✅ 最终获取到Kimi助手的回复:")
                        print(f"\n{last_text}\n")
                        response_file = os.path.join(TEST_DIR, "kimi_response.txt")
                        with open(response_file, "w", encoding="utf-8") as f:
                            f.write(last_text)
                        print(f"✅ 回复已保存到: {response_file}")
                    else:
                        print("❌ 未获取到回复文字")
                    
                    screenshot_path = os.path.join(TEST_DIR, "response_received.png")
                    await page.screenshot(path=screenshot_path)
                    print(f"12. 回复状态截图已保存: {screenshot_path}")
                else:
                    print("❌ 聊天输入框不可见")
            except Exception as e:
                print(f"操作输入框时出错: {e}")
            
            print("13. 保存登录状态...")
            try:
                await context.storage_state(path=storage_path)
                print(f"✅ 登录状态已保存到: {storage_path}")
            except Exception as e:
                print(f"保存登录状态时出错: {e}")
            
            print("14. 关闭浏览器")
            await browser.close()
            print("✅ 测试完成")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_kimi_login())