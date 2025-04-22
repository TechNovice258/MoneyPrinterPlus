#  Copyright © [2024] 你的名字
# 仅供个人和学习用途

from config.config import tiktok_site
import time

def tiktok_publisher(driver, video_file, text_file):
    print(f"[TikTok] driver={driver}, video_file={video_file}, text_file={text_file}")
    driver.switch_to.new_window('tab')
    driver.get(tiktok_site)
    time.sleep(5)

    # 检查是否需要登录
    if "login" in driver.current_url or "signup" in driver.current_url:
        print("请手动扫码或输入账号登录 TikTok，登录后不要关闭窗口。")
        time.sleep(30)
        driver.get(tiktok_site)
        time.sleep(5)

    try:
        # 上传视频
        file_input = driver.find_element("xpath", '//input[@type="file"]')
        file_input.send_keys(video_file)
        print("视频已选择，等待上传完成...")
        time.sleep(15)

        # 读取标题和描述
        with open(text_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        title = lines[0].strip() if lines else ""
        description = "".join(lines[1:]).strip() if len(lines) > 1 else ""

        # 填写标题
        try:
            title_input = driver.find_element("xpath", '//input[@placeholder="Add a title"]')
            title_input.clear()
            title_input.send_keys(title)
        except Exception as e:
            print("未找到标题输入框：", e)

        # 填写描述（如有）
        # try:
        #     desc_input = driver.find_element("xpath", '//textarea[@placeholder="Add a description"]')
        #     desc_input.clear()
        #     desc_input.send_keys(description)
        # except Exception as e:
        #     print("未找到描述输入框：", e)

        # 点击发布
        try:
            publish_btn = driver.find_element("xpath", '//button[contains(text(),"Post")]')
            publish_btn.click()
            print("已点击发布 TikTok 视频。")
            time.sleep(5)
        except Exception as e:
            print("未找到发布按钮：", e)
    except Exception as e:
        print("TikTok 自动化上传失败：", e) 