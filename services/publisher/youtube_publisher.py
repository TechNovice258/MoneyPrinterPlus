#  Copyright © [2024] 你的名字
# 仅供个人和学习用途

from config.config import youtube_site
import time

def youtube_publisher(driver, video_file, text_file):
    print(f"[YouTube] driver={driver}, video_file={video_file}, text_file={text_file}")
    driver.switch_to.new_window('tab')
    driver.get(youtube_site)
    time.sleep(5)

    # 检查是否需要登录
    if "accounts.google.com" in driver.current_url:
        print("请手动登录 Google 账号，登录后不要关闭窗口。")
        time.sleep(30)
        driver.get(youtube_site)
        time.sleep(5)

    try:
        # 点击"创建"按钮
        create_btn = driver.find_element("xpath", '//*[@id="create-icon"]')
        create_btn.click()
        time.sleep(2)

        # 点击"上传视频"
        upload_btn = driver.find_element("xpath", '//tp-yt-paper-item[@test-id="upload-beta"]')
        upload_btn.click()
        time.sleep(3)

        # 上传视频
        file_input = driver.find_element("xpath", '//input[@type="file" and @name="Filedata"]')
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
            title_input = driver.find_element("xpath", '//input[@id="textbox" and @aria-label="添加标题"]')
            title_input.clear()
            title_input.send_keys(title)
        except Exception as e:
            print("未找到标题输入框：", e)

        # 填写描述
        try:
            desc_input = driver.find_element("xpath", '//textarea[@id="textbox" and @aria-label="添加说明"]')
            desc_input.clear()
            desc_input.send_keys(description)
        except Exception as e:
            print("未找到描述输入框：", e)

        # 点击"下一步"直到"发布"
        try:
            for _ in range(3):
                next_btn = driver.find_element("xpath", '//ytcp-button[@id="next-button"]')
                next_btn.click()
                time.sleep(2)
        except Exception as e:
            print("未找到下一步按钮：", e)

        # 选择"公开"并发布
        try:
            public_radio = driver.find_element("xpath", '//tp-yt-paper-radio-button[@name="PUBLIC"]')
            public_radio.click()
            time.sleep(1)
            publish_btn = driver.find_element("xpath", '//ytcp-button[@id="done-button"]')
            publish_btn.click()
            print("已点击发布 YouTube 视频。")
            time.sleep(5)
        except Exception as e:
            print("未找到发布按钮或公开选项：", e)
    except Exception as e:
        print("YouTube 自动化上传失败：", e) 