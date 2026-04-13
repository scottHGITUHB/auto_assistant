import os
import subprocess
import asyncio
import logging
from git import Repo
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 全局变量
CURRENT_COMMIT_FILE = ".current_commit"

class AutoUpdater:
    def __init__(self):
        self.repo_url = os.getenv("GITHUB_REPO", "https://github.com/scottHGITUHB/auto_assistant.git")
        self.branch = os.getenv("GITHUB_BRANCH", "master")
        self.update_interval = int(os.getenv("UPDATE_INTERVAL", "6"))  # 默认每6小时
    
    def get_current_commit(self):
        """获取当前代码的commit hash"""
        try:
            if os.path.exists(CURRENT_COMMIT_FILE):
                with open(CURRENT_COMMIT_FILE, "r") as f:
                    return f.read().strip()
            # 如果文件不存在，尝试从git获取
            repo = Repo(".")
            commit = repo.head.commit.hexsha
            self.save_current_commit(commit)
            return commit
        except Exception as e:
            logger.error(f"获取当前commit失败: {e}")
            return None
    
    def save_current_commit(self, commit):
        """保存当前commit hash到文件"""
        try:
            with open(CURRENT_COMMIT_FILE, "w") as f:
                f.write(commit)
        except Exception as e:
            logger.error(f"保存commit失败: {e}")
    
    async def check_update(self):
        """检查更新并执行更新"""
        logger.info("开始检查更新...")
        try:
            # 检查是否为git仓库
            if not os.path.exists(".git"):
                logger.warning("当前目录不是git仓库，跳过更新检查")
                return
            
            repo = Repo(".")
            origin = repo.remotes.origin
            
            # 获取当前commit
            current_commit = self.get_current_commit()
            
            # 拉取最新代码
            logger.info("拉取最新代码...")
            origin.pull()
            
            # 获取最新commit
            latest_commit = repo.head.commit.hexsha
            logger.info(f"当前版本: {current_commit}, 最新版本: {latest_commit}")
            
            # 对比版本
            if current_commit != latest_commit:
                logger.info("发现新版本，准备更新...")
                # 保存最新commit
                self.save_current_commit(latest_commit)
                # 重启服务
                await self.restart_service()
            else:
                logger.info("当前已是最新版本，无需更新")
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
    
    async def check_update_on_start(self):
        """启动时检查更新"""
        logger.info("启动时检查更新...")
        await self.check_update()
    
    async def restart_service(self):
        """重启服务"""
        logger.info("重启服务...")
        try:
            # 检查是否在Docker容器内
            if os.path.exists("/proc/1/cgroup"):
                # 在Docker容器内，使用docker-compose restart
                result = subprocess.run(
                    ["docker-compose", "restart"],
                    capture_output=True,
                    text=True
                )
                logger.info(f"重启服务结果: {result.stdout}")
                if result.stderr:
                    logger.error(f"重启服务错误: {result.stderr}")
            else:
                # 在本地运行，提示用户手动重启
                logger.info("请手动重启服务以应用更新")
        except Exception as e:
            logger.error(f"重启服务失败: {e}")

# 创建全局实例
auto_updater = AutoUpdater()

# 导出函数
async def check_update():
    await auto_updater.check_update()

async def check_update_on_start():
    await auto_updater.check_update_on_start()

if __name__ == "__main__":
    # 测试更新功能
    asyncio.run(check_update())
