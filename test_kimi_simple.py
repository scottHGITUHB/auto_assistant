from playwright.sync_api import sync_playwright
import time
import os

# 创建测试文件夹
TEST_DIR = "kimi_test"
if not os.path.exists(TEST_DIR):
    os.makedirs(TEST_DIR)
    print(f"创建测试文件夹: {TEST_DIR}")

def is_logged_in(page):
    """检测是否已登录"""
    try:
        # 方法1：检测输入框（最稳）
        input_box = page.locator('[contenteditable="true"], textarea').first
        return input_box.is_visible()
    except:
        return False

def test_kimi_login():
    print("测试 Kimi 登录流程...")
    try:
        with sync_playwright() as p:
            # 启动浏览器
            print("1. 启动浏览器...")
            browser = p.chromium.launch(headless=False)
            
            # 检查是否有已保存的登录状态
            storage_path = os.path.join(TEST_DIR, "kimi_auth.json")
            
            # 创建上下文和页面
            print("2. 创建页面...")
            if os.path.exists(storage_path):
                print("✅ 使用已保存的登录状态")
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    storage_state=storage_path
                )
            else:
                print("⚠️ 未找到登录状态，需要扫码登录")
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
            page = context.new_page()
            
            # 打开Kimi AI
            print("3. 打开 Kimi AI...")
            page.goto("https://kimi.moonshot.cn/chat")
            
            # 等待页面加载
            print("4. 等待页面加载...")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)
            
            # 截图初始页面
            screenshot_path = os.path.join(TEST_DIR, "initial_page.png")
            page.screenshot(path=screenshot_path)
            print(f"5. 初始页面截图已保存: {screenshot_path}")
            
            # 检测是否已登录
            print("6. 检测登录状态...")
            if is_logged_in(page):
                print("✅ 已登录，无需扫码")
                
                # 找到聊天输入框并粘贴"你好"
                print("7. 查找聊天输入框...")
                try:
                    # 查找聊天输入框
                    chat_input = page.locator('[contenteditable="true"], textarea').first
                    if chat_input.is_visible():
                        print("✅ 找到聊天输入框")
                        # 粘贴"你好"
                        chat_input.click()
                        chat_input.fill("你好")
                        print("✅ 已在输入框中粘贴: 你好")
                        # 截图输入框状态
                        screenshot_path = os.path.join(TEST_DIR, "input_filled.png")
                        page.screenshot(path=screenshot_path)
                        print(f"8. 输入框状态截图已保存: {screenshot_path}")
                        
                        # 按回车发送消息
                        print("9. 按回车发送消息...")
                        chat_input.press("Enter")
                        print("✅ 消息已发送")
                        
                        # 等待Kimi助手的回复并提取文本
                        print("10. 等待Kimi助手的回复...")
                        try:
                            # 核心方法：使用DOM变化监听 + 稳定性判断获取AI回复
                            def get_ai_response(page, timeout=60):
                                """稳定获取AI回复（基于文本稳定性检测）"""

                                print("🔍 等待AI回复出现...")

                                # 1. 等待至少出现一条AI消息
                                page.wait_for_selector('.markdown, .assistant, .message', timeout=timeout*1000)

                                last_text = ""
                                stable_count = 0
                                max_stable = 3  # 连续3次不变认为结束

                                start_time = time.time()

                                while time.time() - start_time < timeout:
                                    try:
                                        # 2. 获取最后一条消息
                                        messages = page.locator('.markdown, .assistant, .message').all()
                                        if not messages:
                                            continue

                                        current_text = messages[-1].inner_text().strip()

                                        if not current_text:
                                            time.sleep(1)
                                            continue

                                        print(f"📝 当前长度: {len(current_text)}")

                                        # 3. 判断是否稳定
                                        if current_text == last_text:
                                            stable_count += 1
                                            print(f"⏳ 稳定计数: {stable_count}/{max_stable}")
                                        else:
                                            stable_count = 0

                                        if stable_count >= max_stable:
                                            print("✅ 检测到回复完成")
                                            return current_text

                                        last_text = current_text
                                        time.sleep(1)

                                    except Exception as e:
                                        print(f"⚠️ 读取失败: {e}")
                                        time.sleep(1)

                                print("❌ 超时，返回当前结果")
                                return last_text
                            
                            # 获取AI回复
                            response_text = get_ai_response(page, timeout=30)
                            
                            # 点击复制按钮
                            print("11. 点击复制按钮...")
                            clipboard_text = ""
                            try:
                                # 查找复制按钮
                                # 尝试多种可能的复制按钮选择器
                                copy_selectors = [
                                    # 查找回复内容附近的按钮
                                    '.message-actions button',
                                    '.chat-message-actions button',
                                    # 查找带有复制图标的按钮
                                    'button:has(svg)',
                                    # 查找带有特定类名的按钮
                                    '[class*="copy"], [class*="clipboard"]',
                                    # 查找所有可见的按钮
                                    'button:visible'
                                ]
                                
                                copy_button_found = False
                                for selector in copy_selectors:
                                    try:
                                        copy_buttons = page.locator(selector).all()
                                        for button in copy_buttons:
                                            if button.is_visible():
                                                # 尝试点击按钮
                                                button.click()
                                                print("✅ 点击了一个按钮")
                                                
                                                # 等待复制操作完成
                                                time.sleep(1)
                                                
                                                # 尝试获取剪贴板内容
                                                try:
                                                    clipboard_text = page.evaluate("navigator.clipboard.readText()")
                                                    if clipboard_text and ("你好" in clipboard_text or "很高兴" in clipboard_text):
                                                        print("✅ 从剪贴板获取到内容:")
                                                        print(f"\n{clipboard_text}\n")
                                                        
                                                        # 保存复制的内容到文件
                                                        clipboard_file = os.path.join(TEST_DIR, "kimi_clipboard.txt")
                                                        with open(clipboard_file, "w", encoding="utf-8") as f:
                                                            f.write(clipboard_text)
                                                        print(f"✅ 复制的内容已保存到: {clipboard_file}")
                                                        copy_button_found = True
                                                        break
                                                except Exception as e:
                                                    print(f"获取剪贴板内容时出错: {e}")
                                    except Exception as e:
                                        print(f"尝试选择器 {selector} 时出错: {e}")
                                    
                                    if copy_button_found:
                                        break
                                
                                if not copy_button_found:
                                    print("❌ 未找到复制按钮")
                            except Exception as e:
                                print(f"点击复制按钮时出错: {e}")
                            
                            # 如果通过复制按钮获取到内容，使用剪贴板内容
                            if clipboard_text:
                                response_text = clipboard_text
                            
                            if response_text:
                                print("✅ 最终获取到Kimi助手的回复:")
                                print(f"\n{response_text}\n")
                                # 保存回复到文件
                                response_file = os.path.join(TEST_DIR, "kimi_response.txt")
                                with open(response_file, "w", encoding="utf-8") as f:
                                    f.write(response_text)
                                print(f"✅ 回复已保存到: {response_file}")
                            else:
                                print("❌ 未获取到回复文字")
                                # 截图当前页面，便于分析
                                debug_screenshot = os.path.join(TEST_DIR, "debug_response.png")
                                page.screenshot(path=debug_screenshot)
                                print(f"📸 调试截图已保存: {debug_screenshot}")
                        except Exception as e:
                            print(f"获取回复时出错: {e}")
                        
                        # 截图回复状态
                        screenshot_path = os.path.join(TEST_DIR, "response_received.png")
                        page.screenshot(path=screenshot_path)
                        print(f"12. 回复状态截图已保存: {screenshot_path}")
                    else:
                        print("❌ 聊天输入框不可见")
                except Exception as e:
                    print(f"操作输入框时出错: {e}")
            else:
                print("❌ 未登录，需要重新扫码")
                
                # 查找登录按钮
                print("7. 查找登录按钮...")
                try:
                    # 尝试多种登录按钮选择器
                    login_selectors = [
                        'text=登录',
                        '.login-button',
                        '#login',
                        '[data-testid="login"]',
                        'button:has-text("登录")'
                    ]
                    
                    login_found = False
                    for selector in login_selectors:
                        try:
                            login_button = page.locator(selector).first
                            if login_button.is_visible():
                                print(f"✅ 找到登录按钮，使用选择器: {selector}")
                                login_found = True
                                try:
                                    login_button.click()
                                    print("7. 点击登录按钮")
                                    # 等待可能的新窗口或登录界面出现
                                    time.sleep(3)
                                    
                                    # 检查是否有新窗口打开
                                    print("8. 检查是否有新窗口打开...")
                                    try:
                                        # 获取所有页面
                                        pages = context.pages
                                        if len(pages) > 1:
                                            # 切换到新页面
                                            page = pages[-1]
                                            print(f"✅ 发现新窗口，切换到新页面: {page.url}")
                                        else:
                                            print("ℹ️  未发现新窗口，继续使用当前页面")
                                    except Exception as e:
                                        print(f"检查新窗口时出错: {e}")
                                    
                                    # 截图登录界面
                                    screenshot_path = os.path.join(TEST_DIR, "login_page.png")
                                    page.screenshot(path=screenshot_path)
                                    print(f"9. 登录界面截图已保存: {screenshot_path}")
                                    break
                                except Exception as e:
                                    print(f"❌ 点击登录按钮失败: {e}")
                                    # 截图当前页面
                                    screenshot_path = os.path.join(TEST_DIR, "login_button_error.png")
                                    page.screenshot(path=screenshot_path)
                                    print(f"📸 错误页面截图已保存: {screenshot_path}")
                        except Exception as e:
                            print(f"尝试选择器 {selector} 失败: {e}")
                except Exception as e:
                    print(f"❌ 查找登录按钮失败: {e}")
                
                if not login_found:
                    print("❌ 未找到登录按钮")
                    # 截图当前页面
                    screenshot_path = os.path.join(TEST_DIR, "no_login_button.png")
                    page.screenshot(path=screenshot_path)
                    print(f"📸 当前页面截图已保存: {screenshot_path}")
                else:
                    # 查找二维码
                    print("9. 查找二维码...")
                    # 尝试多种二维码选择器
                    qr_selectors = [
                        '.qr-code',
                        'img[src*="qrcode"]',
                        '[class*="qrcode"]',
                        '#qrcode',
                        'img[alt*="二维码"]',
                        '[data-testid*="qrcode"]'
                    ]
                    
                    qr_found = False
                    for selector in qr_selectors:
                        try:
                            qr_element = page.locator(selector).first
                            if qr_element.is_visible():
                                print(f"✅ 找到二维码，使用选择器: {selector}")
                                # 截图二维码
                                screenshot_path = os.path.join(TEST_DIR, "qr_code.png")
                                qr_element.screenshot(path=screenshot_path)
                                print(f"10. 二维码截图已保存: {screenshot_path}")
                                print("\n📱 请使用微信扫描二维码登录...")
                                qr_found = True
                                
                                # 等待登录成功
                                print("\n11. 等待登录成功...")
                                max_wait_time = 60
                                start_time = time.time()
                                
                                while time.time() - start_time < max_wait_time:
                                    elapsed = time.time() - start_time
                                    print(f"\r⏳ 等待中... ({elapsed:.1f}s / {max_wait_time}s)", end="")
                                    
                                    # 检查登录是否成功
                                    try:
                                        # 基于截图的登录成功检测：
                                        # 1. 检查登录弹窗是否消失（等待扫码页面特有）
                                        login_modal_visible = True
                                        try:
                                            # 查找登录弹窗元素
                                            login_modal = page.locator('[class*="modal"], [class*="dialog"], [class*="login"]').first
                                            login_modal_visible = login_modal.is_visible()
                                        except:
                                            login_modal_visible = False
                                        
                                        # 2. 检查二维码是否消失（等待扫码页面特有）
                                        qr_visible = True
                                        try:
                                            qr_element = page.locator('[class*="qrcode"]').first
                                            qr_visible = qr_element.is_visible()
                                        except:
                                            qr_visible = False
                                        
                                        # 3. 检查是否出现广告弹窗（已登录页面特有）
                                        ad_modal_visible = False
                                        try:
                                            ad_modal = page.locator('[class*="ad"], [class*="popup"], text="专业数据库已上线"').first
                                            ad_modal_visible = ad_modal.is_visible()
                                        except:
                                            ad_modal_visible = False
                                        
                                        # 4. 检查是否有"我知道了"按钮（已登录页面广告弹窗特有）
                                        know_button_visible = False
                                        try:
                                            know_button = page.locator('text=我知道了').first
                                            know_button_visible = know_button.is_visible()
                                        except:
                                            know_button_visible = False
                                        
                                        # 5. 检查左下角是否显示用户名（已登录页面特有，如"登月者4392"）
                                        username_visible = False
                                        try:
                                            # 查找包含文字的元素，排除登录文字
                                            user_elements = page.locator('div, span').filter(has_text=lambda text: text and "登录" not in text and len(text) > 2).all()
                                            for element in user_elements:
                                                if element.is_visible():
                                                    username_visible = True
                                                    break
                                        except:
                                            username_visible = False
                                        
                                        # 6. 检查左侧导航栏是否显示完整（已登录页面特有）
                                        sidebar_visible = False
                                        try:
                                            # 检查是否有多个导航项
                                            nav_items = page.locator('text=网站, text=文档, text=PPT, text=表格, text=历史').count()
                                            if nav_items >= 3:
                                                sidebar_visible = True
                                        except:
                                            sidebar_visible = False
                                        
                                        # 调试信息
                                        print(f"\n调试: 登录弹窗可见={login_modal_visible}, 二维码可见={qr_visible}, 广告弹窗可见={ad_modal_visible}, 我知道了按钮可见={know_button_visible}, 用户名可见={username_visible}, 侧边栏可见={sidebar_visible}")
                                        
                                        # 登录成功的条件：
                                        # - 二维码消失
                                        # - 出现"我知道了"按钮（广告弹窗的标志）
                                        # 注：根据终端输出，当二维码消失且"我知道了"按钮出现时，就应该采取行动
                                        if not qr_visible and know_button_visible:
                                            print("\n✅ 登录成功！检测到广告弹窗和'我知道了'按钮")
                                            
                                            # 检查并关闭广告弹窗
                                            print("12. 检查是否有广告弹窗...")
                                            try:
                                                # 查找广告弹窗的"我知道了"按钮
                                                know_button = page.locator('text=我知道了').first
                                                if know_button.is_visible():
                                                    print("✅ 发现广告弹窗，点击'我知道了'按钮关闭")
                                                    know_button.click()
                                                    time.sleep(1)
                                                    # 截图关闭广告后的页面
                                                    screenshot_path = os.path.join(TEST_DIR, "ad_closed.png")
                                                    page.screenshot(path=screenshot_path)
                                                    print(f"13. 广告关闭后截图已保存: {screenshot_path}")
                                            except Exception as e:
                                                print(f"关闭广告弹窗时出错: {e}")
                                            
                                            # 找到聊天输入框并粘贴"你好"
                                            print("14. 查找聊天输入框...")
                                            try:
                                                # 查找聊天输入框
                                                chat_input = page.locator('[contenteditable="true"], textarea').first
                                                if chat_input.is_visible():
                                                    print("✅ 找到聊天输入框")
                                                    # 粘贴"你好"
                                                    chat_input.click()
                                                    chat_input.fill("你好")
                                                    print("✅ 已在输入框中粘贴: 你好")
                                                    # 截图输入框状态
                                                    screenshot_path = os.path.join(TEST_DIR, "input_filled.png")
                                                    page.screenshot(path=screenshot_path)
                                                    print(f"15. 输入框状态截图已保存: {screenshot_path}")
                                                    
                                                    # 按回车发送消息
                                                    print("16. 按回车发送消息...")
                                                    chat_input.press("Enter")
                                                    print("✅ 消息已发送")
                                                    
                                                    # 等待Kimi助手的回复并提取文本
                                                    print("17. 等待Kimi助手的回复...")
                                                    try:
                                                        # 核心方法：使用DOM变化监听 + 稳定性判断获取AI回复
                                                        def get_ai_response(page, timeout=60):
                                                            """稳定获取AI回复（基于文本稳定性检测）"""

                                                            print("🔍 等待AI回复出现...")

                                                            # 1. 等待至少出现一条AI消息
                                                            page.wait_for_selector('.markdown, .assistant, .message', timeout=timeout*1000)

                                                            last_text = ""
                                                            stable_count = 0
                                                            max_stable = 3  # 连续3次不变认为结束

                                                            start_time = time.time()

                                                            while time.time() - start_time < timeout:
                                                                try:
                                                                    # 2. 获取最后一条消息
                                                                    messages = page.locator('.markdown, .assistant, .message').all()
                                                                    if not messages:
                                                                        continue

                                                                    current_text = messages[-1].inner_text().strip()

                                                                    if not current_text:
                                                                        time.sleep(1)
                                                                        continue

                                                                    print(f"📝 当前长度: {len(current_text)}")

                                                                    # 3. 判断是否稳定
                                                                    if current_text == last_text:
                                                                        stable_count += 1
                                                                        print(f"⏳ 稳定计数: {stable_count}/{max_stable}")
                                                                    else:
                                                                        stable_count = 0

                                                                    if stable_count >= max_stable:
                                                                        print("✅ 检测到回复完成")
                                                                        return current_text

                                                                    last_text = current_text
                                                                    time.sleep(1)

                                                                except Exception as e:
                                                                    print(f"⚠️ 读取失败: {e}")
                                                                    time.sleep(1)

                                                            print("❌ 超时，返回当前结果")
                                                            return last_text
                                                        
                                                        # 获取AI回复
                                                        response_text = get_ai_response(page, timeout=30)
                                                        
                                                        # 点击复制按钮
                                                        print("18. 点击复制按钮...")
                                                        clipboard_text = ""
                                                        try:
                                                            # 查找复制按钮
                                                            # 尝试多种可能的复制按钮选择器
                                                            copy_selectors = [
                                                                # 查找回复内容附近的按钮
                                                                '.message-actions button',
                                                                '.chat-message-actions button',
                                                                # 查找带有复制图标的按钮
                                                                'button:has(svg)',
                                                                # 查找带有特定类名的按钮
                                                                '[class*="copy"], [class*="clipboard"]',
                                                                # 查找所有可见的按钮
                                                                'button:visible'
                                                            ]
                                                            
                                                            copy_button_found = False
                                                            for selector in copy_selectors:
                                                                try:
                                                                    copy_buttons = page.locator(selector).all()
                                                                    for button in copy_buttons:
                                                                        if button.is_visible():
                                                                            # 尝试点击按钮
                                                                            button.click()
                                                                            print("✅ 点击了一个按钮")
                                                                            
                                                                            # 等待复制操作完成
                                                                            time.sleep(1)
                                                                            
                                                                            # 尝试获取剪贴板内容
                                                                            try:
                                                                                clipboard_text = page.evaluate("navigator.clipboard.readText()")
                                                                                if clipboard_text and ("你好" in clipboard_text or "很高兴" in clipboard_text):
                                                                                    print("✅ 从剪贴板获取到内容:")
                                                                                    print(f"\n{clipboard_text}\n")
                                                                                    
                                                                                    # 保存复制的内容到文件
                                                                                    clipboard_file = os.path.join(TEST_DIR, "kimi_clipboard.txt")
                                                                                    with open(clipboard_file, "w", encoding="utf-8") as f:
                                                                                        f.write(clipboard_text)
                                                                                    print(f"✅ 复制的内容已保存到: {clipboard_file}")
                                                                                    copy_button_found = True
                                                                                    break
                                                                            except Exception as e:
                                                                                print(f"获取剪贴板内容时出错: {e}")
                                                                    if copy_button_found:
                                                                        break
                                                                except Exception as e:
                                                                    print(f"尝试选择器 {selector} 时出错: {e}")
                                                            
                                                            if not copy_button_found:
                                                                print("❌ 未找到复制按钮")
                                                        except Exception as e:
                                                            print(f"点击复制按钮时出错: {e}")
                                                        
                                                        # 如果通过复制按钮获取到内容，使用剪贴板内容
                                                        if clipboard_text:
                                                            response_text = clipboard_text
                                                        
                                                        if response_text:
                                                            print("✅ 最终获取到Kimi助手的回复:")
                                                            print(f"\n{response_text}\n")
                                                            # 保存回复到文件
                                                            response_file = os.path.join(TEST_DIR, "kimi_response.txt")
                                                            with open(response_file, "w", encoding="utf-8") as f:
                                                                f.write(response_text)
                                                            print(f"✅ 回复已保存到: {response_file}")
                                                        else:
                                                            print("❌ 未获取到回复文字")
                                                            # 截图当前页面，便于分析
                                                            debug_screenshot = os.path.join(TEST_DIR, "debug_response.png")
                                                            page.screenshot(path=debug_screenshot)
                                                            print(f"📸 调试截图已保存: {debug_screenshot}")
                                                    except Exception as e:
                                                        print(f"获取回复时出错: {e}")
                                                    
                                                    # 截图回复状态
                                                    screenshot_path = os.path.join(TEST_DIR, "response_received.png")
                                                    page.screenshot(path=screenshot_path)
                                                    print(f"19. 回复状态截图已保存: {screenshot_path}")
                                                else:
                                                    print("❌ 聊天输入框不可见")
                                            except Exception as e:
                                                print(f"操作输入框时出错: {e}")
                                            
                                            # 保存登录状态
                                            print("19. 保存登录状态...")
                                            try:
                                                storage_path = os.path.join(TEST_DIR, "kimi_auth.json")
                                                context.storage_state(path=storage_path)
                                                print(f"✅ 登录状态已保存到: {storage_path}")
                                                print("ℹ️  下次登录无需扫码")
                                            except Exception as e:
                                                print(f"保存登录状态时出错: {e}")
                                            
                                            # 截图成功页面
                                            screenshot_path = os.path.join(TEST_DIR, "login_success.png")
                                            page.screenshot(path=screenshot_path)
                                            print(f"20. 登录成功截图已保存: {screenshot_path}")
                                            break
                                    except Exception as e:
                                        print(f"\n检测登录状态时出错: {e}")
                                    
                                    time.sleep(2)
                                
                                if time.time() - start_time >= max_wait_time:
                                    print("\n❌ 登录超时")
                                break
                        except Exception as e:
                            print(f"尝试选择器 {selector} 失败: {e}")
                    
                    if not qr_found:
                        # 截图当前页面，看看实际情况
                        screenshot_path = os.path.join(TEST_DIR, "no_qr_code.png")
                        page.screenshot(path=screenshot_path)
                        print(f"❌ 未找到二维码，当前页面截图已保存: {screenshot_path}")
            
            # 每次关闭前都保存登录状态
            print("13. 保存登录状态...")
            try:
                storage_path = os.path.join(TEST_DIR, "kimi_auth.json")
                context.storage_state(path=storage_path)
                print(f"✅ 登录状态已保存到: {storage_path}")
            except Exception as e:
                print(f"保存登录状态时出错: {e}")
            
            # 关闭浏览器
            print("14. 关闭浏览器")
            browser.close()
            print("✅ 测试完成")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kimi_login()